"""Поиск и распознавание государственного номера в области техники."""
import re
from dataclasses import dataclass

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
# Сколько символов слева пробуем отрезать перед строгим совпадением с форматом номера —
# OCR иногда цепляет соседний код страны ("KZ"/"K2" слева от рамки номера) к тексту
_MAX_PREFIX_TRIM = 3


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


def _best_strict_match(text: str):
    """Пробует сам текст и его суффиксы (отрезая посторонний префикс вроде кода
    страны 'KZ'/'K2', слипшегося с рамкой номера) на точное совпадение с форматом
    номера. Возвращает самый длинный (наименее обрезанный) подходящий суффикс."""
    for start in range(0, min(len(text), _MAX_PREFIX_TRIM + 1)):
        candidate = text[start:]
        if PLATE_REGEX.match(candidate):
            return candidate
    return None


def find_plate(image, vehicle_bbox: tuple) -> PlateResult:
    """image: полный кадр (numpy BGR). vehicle_bbox: bbox техники."""
    x1, y1, x2, y2 = [int(v) for v in vehicle_bbox]
    h, w = image.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return PlateResult(None, 0.0, None)

    fragments = _run_ocr(crop)

    def to_global(bbox_local):
        lx1, ly1, lx2, ly2 = bbox_local
        return (x1 + lx1, y1 + ly1, x1 + lx2, y1 + ly2)

    # 1) точный формат номера — пробуем каждый фрагмент целиком и его суффиксы
    # (PaddleOCR обычно читает весь номер одним связным фрагментом)
    best = None
    for text, conf, bbox_local in fragments:
        matched = _best_strict_match(text)
        if matched is not None and (best is None or conf > best[1]):
            best = (matched, conf, to_global(bbox_local))

    if best is not None:
        return PlateResult(*best)

    # 2) запасной вариант: текст похож на номер по форме "цифры-буквы-(цифры)",
    # даже если не совпадает точно (например, не распознался код региона)
    fallback_candidates = [
        (text, conf, bbox_local) for text, conf, bbox_local in fragments
        if len(text) in _FALLBACK_LEN_RANGE and _FALLBACK_PLATE_REGEX.match(text)
    ]
    if fallback_candidates:
        text, conf, bbox_local = max(fallback_candidates, key=lambda c: c[1])
        return PlateResult(text, conf, to_global(bbox_local))

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
