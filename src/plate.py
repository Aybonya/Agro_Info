"""Поиск и распознавание государственного номера в области техники."""
import re
from dataclasses import dataclass

import cv2
from paddleocr import PaddleOCR

from config import PLATE_REGEX

_ocr = None
# Запасной (fallback) шаблон: цифры, затем ОДИН цельный блок букв, затем необязательные
# цифры региона (регион часто не попадает в тот же OCR-фрагмент, что основной текст).
# Ключевое ограничение — ровно один блок цифр и один блок букв без чередований:
# это отсекает мешанину из нескольких кусков текста (надпись на кузове + случайные
# цифры и т.п.), которая по одной лишь длине/составу символов выглядела бы похоже.
# Ведущих цифр ровно 2-3 (не 4) — у настоящего номера их всегда 3, а диапазон 1-4
# слишком легко совпадает со штампом даты на кадре камеры (например "2019" в "2019 Tue").
_FALLBACK_PLATE_REGEX = re.compile(r"^\d{2,3}[A-Z]{1,4}\d{0,4}$")
_FALLBACK_LEN_RANGE = range(5, 10)
# Номера старого двухстрочного образца (часто на синих табличках прицепов/спецтехники):
# буквенная серия сверху, номер снизу — например "AFE" над "P523". OCR читает такие
# строки как два отдельных фрагмента, поэтому их нужно сначала склеить по вертикали.
_TWO_LINE_PLATE_REGEX = re.compile(r"^[A-Z]{1,4}\d{2,5}$")
# Сколько символов слева пробуем отрезать перед строгим совпадением с форматом номера —
# OCR иногда цепляет соседний код страны ("KZ"/"K2" слева от рамки номера) к тексту
_MAX_PREFIX_TRIM = 3
# Если номер не нашёлся в полном кропе техники — техника может быть мелкой/далёкой,
# и сама табличка тонет среди более крупных деталей (шильдики, закрашенные номера на
# кузове). Повторно ищем в увеличенной нижней части кропа, где обычно висит номер.
_ZOOM_BOTTOM_FRACTION = 0.45
_ZOOM_SCALE = 4


@dataclass
class PlateResult:
    text: str | None
    confidence: float
    bbox: tuple | None  # x1, y1, x2, y2 в координатах исходного изображения


def get_reader() -> PaddleOCR:
    global _ocr
    if _ocr is None:
        # PP-OCRv4 (не дефолтная v6-пайплайн модель) — на этой связке paddlepaddle
        # v6-модели падают с ошибкой рантайма oneDNN на CPU; mkldnn отключаем по той же причине
        _ocr = PaddleOCR(
            lang="en",
            ocr_version="PP-OCRv4",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
        )
    return _ocr


def _clean(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def _run_ocr(crop):
    """Возвращает список (text, conf, (x1,y1,x2,y2)) — уже очищенный текст."""
    reader = get_reader()
    results = []
    for res in reader.predict(crop):
        boxes = res.get("rec_boxes")
        texts = res.get("rec_texts")
        scores = res.get("rec_scores")
        if boxes is None:
            continue
        for box, text, score in zip(boxes, texts, scores):
            cleaned = _clean(text)
            if not cleaned:
                continue
            x1, y1, x2, y2 = [int(v) for v in box]
            results.append((cleaned, float(score), (x1, y1, x2, y2)))
    return results


def _two_line_candidates(fragments):
    """Ищет пары фрагментов, расположенных друг над другом (верхняя строка —
    буквенная серия, нижняя — номер с кодом региона), и склеивает их в одного
    кандидата в естественном порядке чтения (сверху вниз)."""
    candidates = []
    for text_a, conf_a, box_a in fragments:
        ax1, ay1, ax2, ay2 = box_a
        ah = max(ay2 - ay1, 1)
        aw = max(ax2 - ax1, 1)
        for text_b, conf_b, box_b in fragments:
            bx1, by1, bx2, by2 = box_b
            if by1 <= ay1:  # b должен быть строго ниже a (a — верхняя строка)
                continue
            bh = max(by2 - by1, 1)
            x_overlap = min(ax2, bx2) - max(ax1, bx1)
            if x_overlap < 0.4 * min(aw, bx2 - bx1):
                continue
            gap = by1 - ay2
            if gap < -0.6 * max(ah, bh) or gap > 0.9 * max(ah, bh):
                continue
            merged_text = text_a + text_b
            conf = min(conf_a, conf_b)
            bbox = (min(ax1, bx1), ay1, max(ax2, bx2), by2)
            candidates.append((merged_text, conf, bbox))
    return candidates


def _best_strict_match(text: str):
    """Пробует сам текст и его суффиксы (отрезая посторонний префикс вроде кода
    страны 'KZ'/'K2', слипшегося с рамкой номера) на точное совпадение с форматом
    номера. Возвращает самый длинный (наименее обрезанный) подходящий суффикс."""
    for start in range(0, min(len(text), _MAX_PREFIX_TRIM + 1)):
        candidate = text[start:]
        if PLATE_REGEX.match(candidate):
            return candidate
    return None


def _match_fragments(fragments):
    """Прогоняет фрагменты OCR через три уровня проверки (точный формат номера,
    мягкий фолбэк, двухстрочный номер) и возвращает лучшего кандидата
    (text, conf, bbox_local) либо None."""
    # 1) точный формат номера — пробуем каждый фрагмент целиком и его суффиксы
    # (PaddleOCR обычно читает весь номер одним связным фрагментом)
    best = None
    for text, conf, bbox_local in fragments:
        matched = _best_strict_match(text)
        if matched is not None and (best is None or conf > best[1]):
            best = (matched, conf, bbox_local)
    if best is not None:
        return best

    # 2) запасной вариант: текст похож на номер по форме "цифры-буквы-(цифры)",
    # даже если не совпадает точно (например, не распознался код региона)
    fallback_candidates = [
        (text, conf, bbox_local) for text, conf, bbox_local in fragments
        if len(text) in _FALLBACK_LEN_RANGE and _FALLBACK_PLATE_REGEX.match(text)
    ]
    if fallback_candidates:
        return max(fallback_candidates, key=lambda c: c[1])

    # 3) двухстрочный номер старого образца (серия сверху, номер снизу)
    two_line_matches = [
        (text, conf, bbox_local) for text, conf, bbox_local in _two_line_candidates(fragments)
        if _TWO_LINE_PLATE_REGEX.match(text)
    ]
    if two_line_matches:
        return max(two_line_matches, key=lambda c: c[1])

    return None


def _cluster_fragments(fragments, gap_ratio=1.0):
    """Группирует близко расположенные (по X и Y) фрагменты OCR в кластеры —
    одна физическая табличка при плохом качестве снимка часто распознаётся
    несколькими мелкими обрывками рядом друг с другом, а не одним текстом."""
    items = list(fragments)
    used = [False] * len(items)
    clusters = []
    for i in range(len(items)):
        if used[i]:
            continue
        cluster = [i]
        used[i] = True
        changed = True
        while changed:
            changed = False
            cx1 = min(items[k][2][0] for k in cluster)
            cy1 = min(items[k][2][1] for k in cluster)
            cx2 = max(items[k][2][2] for k in cluster)
            cy2 = max(items[k][2][3] for k in cluster)
            ch = max(cy2 - cy1, 1)
            for j in range(len(items)):
                if used[j]:
                    continue
                jx1, jy1, jx2, jy2 = items[j][2]
                jh = max(jy2 - jy1, 1)
                dx = max(jx1 - cx2, cx1 - jx2, 0)
                dy = max(jy1 - cy2, cy1 - jy2, 0)
                if dx < gap_ratio * max(ch, jh) and dy < gap_ratio * max(ch, jh):
                    cluster.append(j)
                    used[j] = True
                    changed = True
        clusters.append(cluster)

    result = []
    for cluster in clusters:
        text = "".join(items[k][0] for k in sorted(cluster, key=lambda k: items[k][2][1]))
        # уверенность кластера — по САМОМУ СЛАБОМУ фрагменту в нём (не по самому
        # сильному): один яркий, уверенно прочитанный кусок в куче шумных обрывков
        # рядом — это ещё не табличка, а музор/текстура со случайным сильным пятном
        conf = min(items[k][1] for k in cluster)
        x1 = min(items[k][2][0] for k in cluster)
        y1 = min(items[k][2][1] for k in cluster)
        x2 = max(items[k][2][2] for k in cluster)
        y2 = max(items[k][2][3] for k in cluster)
        result.append((text, conf, (x1, y1, x2, y2), len(cluster)))
    return result


# Настоящий номер — это 1 строка текста (иногда OCR рвёт её на 2 куска) или 2
# строки старого образца — никогда не куча из 3+ разрозненных обрывков.
_UNCERTAIN_MAX_FRAGMENTS = 2
# Кластер должен быть уверенным целиком, а не содержать один яркий кусок среди шума
_UNCERTAIN_MIN_CONFIDENCE = 0.5


def _uncertain_candidate(fragments):
    """Последний рубеж: текст не удалось разобрать по формату номера, но если в
    кластере фрагментов есть хотя бы одна цифра (настоящий номер всегда её
    содержит) — считаем это местом номера и возвращаем область без подтверждённого
    текста, чтобы её можно было отметить рамкой и сохранить кроп. Кластер должен
    быть компактным (≤2 фрагментов) и достаточно уверенным целиком — иначе легко
    принять текстуру (протектор шины, грязь) или закрашенный инвентарный номер
    техники за номерной знак."""
    candidates = [
        (text, conf, bbox) for text, conf, bbox, n_frags in _cluster_fragments(fragments)
        if any(ch.isdigit() for ch in text)
        and n_frags <= _UNCERTAIN_MAX_FRAGMENTS
        and conf >= _UNCERTAIN_MIN_CONFIDENCE
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda c: c[1])


def _zoomed_bottom_ocr(crop):
    """Повторный OCR на увеличенной нижней части кропа техники (где обычно висит
    номер) — помогает, когда техника мелкая/далёкая и настоящая табличка тонет
    среди более крупных деталей (закрашенные номера на кузове, шильдики и т.п.).
    Возвращает фрагменты в координатах исходного crop."""
    ch = crop.shape[0]
    y_offset = int(ch * (1 - _ZOOM_BOTTOM_FRACTION))
    bottom = crop[y_offset:, :]
    if bottom.size == 0:
        return []
    zoomed = cv2.resize(bottom, (bottom.shape[1] * _ZOOM_SCALE, bottom.shape[0] * _ZOOM_SCALE),
                         interpolation=cv2.INTER_CUBIC)
    fragments = []
    for text, conf, (zx1, zy1, zx2, zy2) in _run_ocr(zoomed):
        bbox_local = (zx1 / _ZOOM_SCALE, zy1 / _ZOOM_SCALE + y_offset,
                      zx2 / _ZOOM_SCALE, zy2 / _ZOOM_SCALE + y_offset)
        fragments.append((text, conf, bbox_local))
    return fragments


def find_plate(image, vehicle_bbox: tuple) -> PlateResult:
    """image: полный кадр (numpy BGR). vehicle_bbox: bbox техники."""
    x1, y1, x2, y2 = [int(v) for v in vehicle_bbox]
    h, w = image.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return PlateResult(None, 0.0, None)

    def to_global(bbox_local):
        lx1, ly1, lx2, ly2 = bbox_local
        return (x1 + lx1, y1 + ly1, x1 + lx2, y1 + ly2)

    match = _match_fragments(_run_ocr(crop))
    zoom_fragments = None
    if match is None:
        zoom_fragments = _zoomed_bottom_ocr(crop)
        match = _match_fragments(zoom_fragments)

    if match is not None:
        text, conf, bbox_local = match
        return PlateResult(text, conf, to_global(bbox_local))

    # 4) текст не сложился ни в один формат номера, но в кадре есть область
    # с цифрами там, где обычно висит номер — отмечаем её как неуверенный
    # кандидат (без подтверждённого текста), чтобы граница и кроп не терялись
    if zoom_fragments is None:
        zoom_fragments = _zoomed_bottom_ocr(crop)
    uncertain = _uncertain_candidate(zoom_fragments)
    if uncertain is not None:
        _text, conf, bbox_local = uncertain
        return PlateResult(None, conf, to_global(bbox_local))

    return PlateResult(None, 0.0, None)


def read_text_tokens(image, vehicle_bbox: tuple) -> list[str]:
    """Свободный OCR по области техники — для поиска названия бренда на кузове/решётке."""
    x1, y1, x2, y2 = [int(v) for v in vehicle_bbox]
    h, w = image.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return []
    return [text for text, conf, _bbox in _run_ocr(crop) if conf > 0.3]
