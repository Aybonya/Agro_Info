"""Минимальный пример вызова Roboflow Cloud для тестирования одной фотографии."""
import sys
import json
from pathlib import Path
from inference_sdk import InferenceHTTPClient, InferenceConfiguration
from config import API_URL, API_KEY, MODEL_ID

client = InferenceHTTPClient(
    api_url=API_URL,
    api_key=API_KEY
).configure(InferenceConfiguration(api_key_transport="header"))

image_file = sys.argv[1] if len(sys.argv) > 1 else "../Auto/10.jpg"
print(f"Запрос в Roboflow Cloud для: {image_file} ...")

result = client.infer(image_file, model_id=MODEL_ID)

print("\n--- Найденные объекты ---")
for pred in result.get("predictions", []):
    print(f"Класс: {pred['class']:15} | Уверенность: {pred['confidence']*100:.1f}% | Координаты центра: ({pred['x']}, {pred['y']})")
