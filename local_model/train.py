"""
Скрипт для дообучения локальной модели YOLO11 на новых данных.

Использование:
  python train.py                     # использует local_model/dataset/data.yaml
  python train.py --data my_data.yaml # или любой внешний data.yaml
  python train.py --epochs 60         # указать количество эпох
"""
import argparse
from pathlib import Path
import shutil
import torch
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
LOCAL_DATA_YAML = ROOT / "dataset" / "data.yaml"
FALLBACK_DATA_YAML = WORKSPACE / "ml" / "dataset_truck_plate.yaml"
OUTPUT_WEIGHTS = ROOT / "weights" / "truck_plate_yolo11n.pt"
BASE_WEIGHTS = OUTPUT_WEIGHTS if OUTPUT_WEIGHTS.exists() else "yolo11n.pt"

def main():
    parser = argparse.ArgumentParser(description="Дообучение локальной модели YOLO11")
    parser.add_argument("--data", default=None, help="Путь к data.yaml (по умолчанию local_model/dataset/data.yaml)")
    parser.add_argument("--epochs", type=int, default=30, help="Количество эпох (по умолчанию 30)")
    parser.add_argument("--batch", type=int, default=8, help="Размер батча (по умолчанию 8)")
    parser.add_argument("--patience", type=int, default=10, help="Ранняя остановка patience (по умолчанию 10)")
    parser.add_argument("--from-scratch", action="store_true", help="Обучать с нуля на yolo11n.pt, а не дообучать текущую модель")
    args = parser.parse_args()

    # Определение пути к data.yaml
    if args.data:
        data_yaml = Path(args.data)
        if not data_yaml.is_absolute():
            data_yaml = (ROOT / data_yaml).resolve()
    else:
        # Проверяем, есть ли снимки в local_model/dataset/train/images
        train_images = list((ROOT / "dataset" / "train" / "images").glob("*.*"))
        if train_images:
            data_yaml = LOCAL_DATA_YAML
            print(f"Найден локальный датасет: {len(train_images)} изображений в local_model/dataset/train/images")
        elif FALLBACK_DATA_YAML.exists():
            data_yaml = FALLBACK_DATA_YAML
            print(f"В local_model/dataset/train/images пока пусто. Используется исходный датасет: {FALLBACK_DATA_YAML.name}")
        else:
            data_yaml = LOCAL_DATA_YAML

    if not data_yaml.exists():
        raise SystemExit(f"Файл конфигурации датасета не найден: {data_yaml}")

    device = 0 if torch.cuda.is_available() else "cpu"
    device_name = torch.cuda.get_device_name(0) if device == 0 else "CPU"
    print(f"Устройство: {device_name}")

    start_weights = "yolo11n.pt" if args.from_scratch else str(BASE_WEIGHTS)
    print(f"Базовые веса: {start_weights}")
    print(f"Запуск обучения на: {data_yaml} ({args.epochs} эпох)...")

    model = YOLO(start_weights)
    model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=640,
        batch=args.batch,
        device=device,
        workers=0,
        patience=args.patience,
        project=str(ROOT / "runs"),
        name="local_fine_tune",
        exist_ok=True,
    )

    best_pt = ROOT / "runs" / "local_fine_tune" / "weights" / "best.pt"
    if best_pt.exists():
        shutil.copy(best_pt, OUTPUT_WEIGHTS)
        print(f"\n[УСПЕХ] Обновлённая модель сохранена в: {OUTPUT_WEIGHTS}")
        print("Теперь detect.py будет автоматически использовать новую обученную версию!")

if __name__ == "__main__":
    main()
