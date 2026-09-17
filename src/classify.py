"""Определение типа техники и производителя.

Стратегия:
1. Марка: сначала пытаемся найти название бренда в тексте, распознанном OCR
   на кузове/решётке (нечёткое сравнение со справочником KNOWN_MANUFACTURERS).
   Если не нашли — используем zero-shot классификацию CLIP по названиям брендов.
2. Тип техники: zero-shot классификация CLIP по набору текстовых описаний
   (самосвал, бортовой/зерновоз, цистерна, трактор, легковой, автобус, спецтехника).
"""
import difflib
from dataclasses import dataclass

import cv2
import open_clip
import torch
from PIL import Image

from config import KNOWN_MANUFACTURERS, VEHICLE_TYPES, TYPE_RU_LABELS

_clip_model = None
_clip_preprocess = None
_clip_tokenizer = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


@dataclass
class ClassifyResult:
    vehicle_type: str
    vehicle_type_ru: str
    type_confidence: float
    manufacturer: str | None
    manufacturer_confidence: float
    manufacturer_source: str  # "ocr" | "clip" | "unknown"


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

    type_key, type_conf = _clip_zero_shot(crop_rgb, VEHICLE_TYPES)

    manufacturer, mf_conf = match_manufacturer_from_text(ocr_tokens)
    source = "ocr"
    if manufacturer is None:
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
