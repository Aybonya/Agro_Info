"""Определение типа техники, производителя и модели через GPT-4o (vision) —
запасной/дополнительный способ поверх CLIP: GPT знает гораздо больше моделей
техники "из коробки", чем наш небольшой список брендов для zero-shot CLIP.

Требует OPENAI_API_KEY в .env (или переменных окружения) и доступ в интернет.
"""
import base64
import json
import os
from dataclasses import dataclass

import cv2
from dotenv import load_dotenv
from openai import OpenAI

from config import TYPE_RU_LABELS

load_dotenv()

_client = None

_TYPE_KEYS = list(TYPE_RU_LABELS.keys())

_SYSTEM_PROMPT = (
    "Ты эксперт по сельскохозяйственной и грузовой технике. По фото кадра с "
    "весовой определи тип техники, производителя и, если узнаёшь, точную модель. "
    f"Тип должен быть одним из: {', '.join(_TYPE_KEYS)}. "
    "Если не уверен в производителе или модели — верни null, не угадывай наугад. "
    "Ответь строго JSON без пояснений: "
    '{"type": "...", "manufacturer": "...", "model": "...", "confidence": 0.0-1.0}'
)


@dataclass
class GptClassifyResult:
    vehicle_type: str | None
    manufacturer: str | None
    model: str | None
    confidence: float
    raw_error: str | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY не задан (проверьте .env)")
        _client = OpenAI(api_key=api_key)
    return _client


def _encode_jpeg_base64(crop_bgr) -> str:
    ok, buf = cv2.imencode(".jpg", crop_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise ValueError("Не удалось закодировать изображение")
    return base64.b64encode(buf).decode("ascii")


def classify_with_gpt(crop_bgr, model: str = "gpt-4o-mini") -> GptClassifyResult:
    try:
        client = _get_client()
        b64 = _encode_jpeg_base64(crop_bgr)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Определи технику на этом фото."},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}", "detail": "high"}},
                    ],
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=200,
        )
        data = json.loads(response.choices[0].message.content)

        def _clean(value):
            if not value or str(value).strip().lower() in ("null", "none", "unknown", "н/д"):
                return None
            return str(value).strip()

        vehicle_type = _clean(data.get("type"))
        if vehicle_type not in _TYPE_KEYS:
            vehicle_type = None
        return GptClassifyResult(
            vehicle_type=vehicle_type,
            manufacturer=_clean(data.get("manufacturer")),
            model=_clean(data.get("model")),
            confidence=float(data.get("confidence") or 0.0),
        )
    except Exception as e:
        return GptClassifyResult(None, None, None, 0.0, raw_error=str(e))
