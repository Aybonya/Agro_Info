"""Минимальный пример локального вызова для проверки одной фотографии."""
import sys
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
WEIGHTS = ROOT / "weights" / "truck_plate_yolo11n.pt"

if not WEIGHTS.exists():
    raise SystemExit(f"Веса не найдены: {WEIGHTS}")

model = YOLO(str(WEIGHTS))
image_file = sys.argv[1] if len(sys.argv) > 1 else "../Auto/10.jpg"
print(f"Локальный инференс для: {image_file} ...")

results = model.predict(image_file, conf=0.15, verbose=False)[0]

print("\n--- Найденные объекты (Локальная модель) ---")
for box in results.boxes:
    cls_name = results.names[int(box.cls[0])]
    conf = float(box.conf[0])
    xyxy = [round(x, 1) for x in box.xyxy[0].tolist()]
    print(f"Класс: {cls_name:15} | Уверенность: {conf*100:.1f}% | Рамка: {xyxy}")
