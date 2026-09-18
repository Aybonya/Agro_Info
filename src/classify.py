"""Определение типа техники и производителя.

Стратегия (для типа и марки):
1. Марка: сначала пытаемся найти название бренда в тексте, распознанном OCR
   на кузове/решётке (нечёткое сравнение со справочником KNOWN_MANUFACTURERS).
2. Если OCR не помог — сравниваем фото техники (по картинке, embedding CLIP)
   с эталонной галереей вручную размеченных фото (reference_gallery.py).
   Это надёжнее zero-shot текстовых промптов: CLIP визуально путает похожие
   советские кабины (KAMAZ/ЗИЛ/МАЗ), а некоторых брендов (Кировец, Lovol)
   вообще нет среди текстовых кандидатов.
3. Если и в галерее нет уверенного совпадения — используем zero-shot
   классификацию CLIP по названиям брендов/типов техники.
"""
import difflib
from dataclasses import dataclass

import cv2
import open_clip
import torch
from PIL import Image

from config import KNOWN_MANUFACTURERS, VEHICLE_TYPES, TYPE_RU_LABELS, DATA_DIR
from detect import detect_vehicles
from reference_gallery import REFERENCE_LABELS
from gpt_classify import classify_with_gpt

_clip_model = None
_clip_preprocess = None
_clip_tokenizer = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

# Порог косинусной похожести embedding'ов, выше которого доверяем эталонной
# галерее больше, чем zero-shot текстовому CLIP — подобран эмпирически:
# видимо разные объекты одного типа обычно дают >0.8, случайные — заметно ниже
_GALLERY_SIM_THRESHOLD = 0.80

_gallery_embeddings = None  # [(embedding, type_key, manufacturer)], считается лениво


@dataclass
class ClassifyResult:
    vehicle_type: str
    vehicle_type_ru: str
    type_confidence: float
    manufacturer: str | None
    manufacturer_confidence: float
    manufacturer_source: str  # "ocr" | "gallery" | "clip" | "gpt" | "unknown"
    model: str | None = None  # конкретная модель (напр. "КАМАЗ-5320"); знает только GPT


def _get_clip():
    global _clip_model, _clip_preprocess, _clip_tokenizer
    if _clip_model is None:
        _clip_model, _, _clip_preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        _clip_model = _clip_model.to(_device).eval()
        _clip_tokenizer = open_clip.get_tokenizer("ViT-B-32")
    return _clip_model, _clip_preprocess, _clip_tokenizer


def _clip_zero_shot(crop_rgb, labels: dict[str, str]) -> tuple[str, float]:
    model, preprocess, tokenizer = _get_clip()
    image = preprocess(Image.fromarray(crop_rgb)).unsqueeze(0).to(_device)
    keys = list(labels.keys())
    prompts = [f"a photo of {labels[k]}" for k in keys]
    text = tokenizer(prompts).to(_device)
    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)[0]
    best_idx = int(probs.argmax())
    return keys[best_idx], float(probs[best_idx])


def _encode_image(crop_rgb) -> torch.Tensor:
    model, preprocess, _ = _get_clip()
    image = preprocess(Image.fromarray(crop_rgb)).unsqueeze(0).to(_device)
    with torch.no_grad():
        features = model.encode_image(image)
        features /= features.norm(dim=-1, keepdim=True)
    return features[0]


def _get_gallery() -> list[tuple[torch.Tensor, str, str | None]]:
    """Эталонные embedding'и по фото из REFERENCE_LABELS — считаются один раз
    и кешируются в памяти на весь запуск."""
    global _gallery_embeddings
    if _gallery_embeddings is None:
        _gallery_embeddings = []
        for fname, (type_key, manufacturer) in REFERENCE_LABELS.items():
            path = DATA_DIR / fname
            image = cv2.imread(str(path))
            if image is None:
                continue
            dets = detect_vehicles(str(path))
            if not dets:
                continue
            bx1, by1, bx2, by2 = [int(v) for v in dets[0].bbox]
            h, w = image.shape[:2]
            bx1, by1 = max(0, bx1), max(0, by1)
            bx2, by2 = min(w, bx2), min(h, by2)
            crop_rgb = cv2.cvtColor(image[by1:by2, bx1:bx2], cv2.COLOR_BGR2RGB)
            _gallery_embeddings.append((_encode_image(crop_rgb), type_key, manufacturer))
    return _gallery_embeddings


def match_by_gallery(crop_rgb) -> tuple[float, str, str | None] | None:
    """Ищет самое похожее (по картинке, не по тексту) фото среди эталонов,
    размеченных вручную. Возвращает (похожесть, тип, производитель_или_None)
    для лучшего совпадения, либо None, если галерея пуста."""
    gallery = _get_gallery()
    if not gallery:
        return None
    query = _encode_image(crop_rgb)
    best = None
    for embedding, type_key, manufacturer in gallery:
        sim = float((query @ embedding).item())
        if best is None or sim > best[0]:
            best = (sim, type_key, manufacturer)
    return best


def match_manufacturer_from_text(ocr_tokens: list[str]) -> tuple[str | None, float]:
    best_match, best_score = None, 0.0
    for token in ocr_tokens:
        token_clean = token.upper().strip()
        if len(token_clean) < 3:
            continue
        matches = difflib.get_close_matches(token_clean, KNOWN_MANUFACTURERS, n=1, cutoff=0.6)
        if matches:
            score = difflib.SequenceMatcher(None, token_clean, matches[0]).ratio()
            if score > best_score:
                best_match, best_score = matches[0], score
    return best_match, best_score


def classify_vehicle(image_bgr, vehicle_bbox: tuple, ocr_tokens: list[str]) -> ClassifyResult:
    x1, y1, x2, y2 = [int(v) for v in vehicle_bbox]
    h, w = image_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    crop_bgr = image_bgr[y1:y2, x1:x2]
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)

    # Основной путь — GPT-4o (vision): видит и текст на кузове, и модель
    # техники, знает гораздо больше брендов/моделей, чем наш список для CLIP.
    # При недоступности (нет ключа/сети/ошибка API) — откат на CLIP ниже.
    gpt_result = classify_with_gpt(crop_bgr)
    if gpt_result.raw_error is None and gpt_result.vehicle_type is not None:
        return ClassifyResult(
            vehicle_type=gpt_result.vehicle_type,
            vehicle_type_ru=TYPE_RU_LABELS[gpt_result.vehicle_type],
            type_confidence=gpt_result.confidence,
            manufacturer=gpt_result.manufacturer,
            manufacturer_confidence=gpt_result.confidence if gpt_result.manufacturer else 0.0,
            manufacturer_source="gpt" if gpt_result.manufacturer else "unknown",
            model=gpt_result.model,
        )

    # --- откат: GPT недоступен — эталонная галерея (размечена вручную) — надёжнее zero-shot текстовых
    # промптов, особенно для брендов, которые CLIP визуально путает
    # (KAMAZ/ЗИЛ/МАЗ) или которых нет среди текстовых кандидатов (Кировец, Lovol)
    gallery_match = match_by_gallery(crop_rgb)
    gallery_confident = gallery_match is not None and gallery_match[0] >= _GALLERY_SIM_THRESHOLD

    if gallery_confident:
        _sim, type_key, _mf = gallery_match
        type_conf = gallery_match[0]
    else:
        type_key, type_conf = _clip_zero_shot(crop_rgb, VEHICLE_TYPES)

    manufacturer, mf_conf = match_manufacturer_from_text(ocr_tokens)
    source = "ocr"
    if manufacturer is None:
        if gallery_confident and gallery_match[2] is not None:
            manufacturer, mf_conf, source = gallery_match[2], gallery_match[0], "gallery"
        else:
            brand_labels = {b: b for b in KNOWN_MANUFACTURERS}
            clip_brand, clip_conf = _clip_zero_shot(crop_rgb, brand_labels)
            if clip_conf >= 0.15:
                manufacturer, mf_conf, source = clip_brand, clip_conf, "clip"
            else:
                manufacturer, mf_conf, source = None, 0.0, "unknown"

    return ClassifyResult(
        vehicle_type=type_key,
        vehicle_type_ru=TYPE_RU_LABELS[type_key],
        type_confidence=type_conf,
        manufacturer=manufacturer,
        manufacturer_confidence=mf_conf,
        manufacturer_source=source,
    )
