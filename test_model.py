"""Run the Roboflow model on one photo or on every photo in a folder."""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path

import cv2
import requests


ROOT = Path(__file__).resolve().parent
# Roboflow model ID for the hosted endpoint is project/version, without workspace.
DEFAULT_MODEL_ID = "trucks-dataset-dqp47-5-yolo26n-t1/1"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def clamp_box(image, x1, y1, x2, y2):
  height, width = image.shape[:2]
  left, top = max(0, int(x1)), max(0, int(y1))
  right, bottom = min(width, int(x2)), min(height, int(y2))
  return image[top:bottom, left:right]


def detect_image(image, url, api_key):
  ok, encoded_image = cv2.imencode(".jpg", image)
  if not ok:
    raise ValueError("Не удалось преобразовать изображение в JPEG")

  response = requests.post(
    url,
    data=base64.b64encode(encoded_image).decode("utf-8"),
    headers={
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/x-www-form-urlencoded",
    },
    timeout=120,
  )
  if response.status_code == 404:
    raise RuntimeError(
      "Модель Roboflow не найдена. Проверьте ROBOFLOW_MODEL_ID: "
      "нужен точный project-slug/version из раздела Deploy." 
    )
  response.raise_for_status()
  return response.json()


def process_image(image_path, url, api_key, annotated_dir, crops_dir):
  image = cv2.imread(str(image_path))
  if image is None:
    raise ValueError(f"Не удалось открыть изображение: {image_path}")

  result = detect_image(image, url, api_key)
  annotated = image.copy()
  detections = []

  for index, prediction in enumerate(result.get("predictions", []), start=1):
    x = float(prediction["x"])
    y = float(prediction["y"])
    width = float(prediction["width"])
    height = float(prediction["height"])
    x1, y1 = x - width / 2, y - height / 2
    x2, y2 = x + width / 2, y + height / 2
    class_name = str(prediction.get("class", "object"))
    confidence = float(prediction.get("confidence", 0))
    color = (0, 255, 0) if "plate" in class_name.lower() else (255, 0, 0)

    cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
    cv2.putText(
      annotated,
      f"{class_name} {confidence:.2f}",
      (int(x1), max(20, int(y1) - 8)),
      cv2.FONT_HERSHEY_SIMPLEX,
      0.6,
      color,
      2,
    )

    detection = {
      "class": class_name,
      "confidence": round(confidence, 4),
      "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
    }
    if "plate" in class_name.lower():
      crop = clamp_box(image, x1, y1, x2, y2)
      if crop.size:
        crop_name = f"{image_path.stem}_plate_{index}.jpg"
        cv2.imwrite(str(crops_dir / crop_name), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
        detection["crop_file"] = crop_name
    detections.append(detection)

  annotated_path = annotated_dir / image_path.name
  cv2.imwrite(str(annotated_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])
  return {"image": image_path.name, "detections": detections}


def main():
  parser = argparse.ArgumentParser(description="Распознавание грузовиков и номеров на фотографиях")
  parser.add_argument("source", nargs="?", default="Auto", help="Фото или папка с фото")
  parser.add_argument("--output-dir", default="output", help="Папка для результатов")
  args = parser.parse_args()

  api_key = os.getenv("ROBOFLOW_API_KEY")
  if not api_key:
    raise SystemExit("Задайте ключ: $env:ROBOFLOW_API_KEY='ваш_ключ'")

  source = Path(args.source)
  if not source.is_absolute():
    source = ROOT / source
  if source.is_file():
    image_paths = [source]
  elif source.is_dir():
    image_paths = sorted(path for path in source.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
  else:
    raise SystemExit(f"Путь не найден: {source}")
  if not image_paths:
    raise SystemExit(f"В папке нет изображений: {source}")

  output_dir = Path(args.output_dir)
  if not output_dir.is_absolute():
    output_dir = ROOT / output_dir
  annotated_dir = output_dir / "annotated"
  crops_dir = output_dir / "plate_crops"
  annotated_dir.mkdir(parents=True, exist_ok=True)
  crops_dir.mkdir(parents=True, exist_ok=True)
  model_id = os.getenv("ROBOFLOW_MODEL_ID", DEFAULT_MODEL_ID).strip("/")
  url = f"https://serverless.roboflow.com/{model_id}"

  results = []
  for image_path in image_paths:
    try:
      result = process_image(image_path, url, api_key, annotated_dir, crops_dir)
      results.append(result)
      print(f"{image_path.name}: {len(result['detections'])} объектов")
    except (requests.RequestException, RuntimeError, ValueError, KeyError) as error:
      print(f"ОШИБКА {image_path.name}: {error}")

  report_path = output_dir / "detection_results.json"
  report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
  print(f"\nГотово. Размеченные фото: {annotated_dir}")
  print(f"Вырезанные номера: {crops_dir}")
  print(f"Отчёт: {report_path}")


if __name__ == "__main__":
  main()