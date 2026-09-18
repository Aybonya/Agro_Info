"""
Детекция транспорта и номерных знаков через облачный API Roboflow (v5).
Сохраняет размеченные фотографии, вырезанные номерные знаки и JSON-отчёт.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import cv2
from inference_sdk import InferenceHTTPClient, InferenceConfiguration

from config import API_URL, API_KEY, MODEL_ID, DEFAULT_CONFIDENCE

CLASS_COLORS = {
    "license plate": (0, 215, 255),  # Золотистый/Жёлтый
    "truck": (255, 140, 0),          # Синий/Лазурный в BGR
    "trailer": (180, 105, 255),      # Фиолетовый
    "tractor": (50, 205, 50),        # Зеленый
}

def get_client() -> InferenceHTTPClient:
    return InferenceHTTPClient(
        api_url=API_URL,
        api_key=API_KEY
    ).configure(InferenceConfiguration(
        api_key_transport="header"
    ))

def clamp_crop(image, xyxy, padding=0.08):
    h, w = image.shape[:2]
    x1, y1, x2, y2 = map(float, xyxy)
    pad_x = (x2 - x1) * padding
    pad_y = (y2 - y1) * padding
    left = max(0, int(x1 - pad_x))
    top = max(0, int(y1 - pad_y))
    right = min(w, int(x2 + pad_x))
    bottom = min(h, int(y2 + pad_y))
    return image[top:bottom, left:right], (left, top, right, bottom)

def process_image(client: InferenceHTTPClient, image_path: Path, conf: float, output_dir: Path):
    res = client.infer(str(image_path), model_id=MODEL_ID)
    img = cv2.imread(str(image_path))
    if img is None:
        return None

    img_h, img_w = img.shape[:2]
    annotated = img.copy()
    crops_dir = output_dir / "plate_crops"
    annotated_dir = output_dir / "annotated"
    crops_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)

    objects = []
    plate_idx = 0
    thickness = max(2, int(min(img.shape[:2]) / 350))

    for pred in res.get("predictions", []):
        score = float(pred.get("confidence", 0.0))
        if score < conf:
            continue

        cls_name = pred.get("class", "object")
        xc, yc = float(pred["x"]), float(pred["y"])
        w, h = float(pred["width"]), float(pred["height"])

        x1 = max(0, int(xc - w / 2))
        y1 = max(0, int(yc - h / 2))
        x2 = min(img_w, int(xc + w / 2))
        y2 = min(img_h, int(yc + h / 2))
        xyxy = [x1, y1, x2, y2]

        color = CLASS_COLORS.get(cls_name, (0, 255, 0))
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

        label = f"{cls_name} {score:.2f}"
        font_scale = max(0.55, thickness * 0.22)
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        text_y = max(y1 - 6, th + 4)
        cv2.rectangle(annotated, (x1, text_y - th - 4), (x1 + tw + 6, text_y + baseline), color, -1)
        cv2.putText(annotated, label, (x1 + 3, text_y - 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 1, cv2.LINE_AA)

        obj_record = {
            "class": cls_name,
            "confidence": round(score, 3),
            "bbox_xyxy": xyxy,
            "detection_id": pred.get("detection_id"),
        }

        # Если найден номерной знак — вырезаем и сохраняем кроп
        if "plate" in cls_name.lower():
            plate_idx += 1
            crop_img, _ = clamp_crop(img, xyxy)
            if crop_img.size > 0:
                crop_name = f"{image_path.stem}_plate_{plate_idx}.jpg"
                crop_path = crops_dir / crop_name
                cv2.imwrite(str(crop_path), crop_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                obj_record["crop_file"] = crop_name

        objects.append(obj_record)

    # Сохраняем размеченное фото
    annotated_file = annotated_dir / image_path.name
    cv2.imwrite(str(annotated_file), annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])

    return {
        "image": image_path.name,
        "width": img_w,
        "height": img_h,
        "model_id": MODEL_ID,
        "objects_count": len(objects),
        "objects": objects,
    }

def main():
    parser = argparse.ArgumentParser(description="Детекция через Roboflow Cloud API (v5)")
    parser.add_argument("source", nargs="?", default="../Auto/10.jpg", help="Путь к файлу или папке (по умолчанию: ../Auto/10.jpg)")
    parser.add_argument("--conf", type=float, default=DEFAULT_CONFIDENCE, help=f"Порог уверенности (по умолчанию: {DEFAULT_CONFIDENCE})")
    parser.add_argument("--output", default="output", help="Папка для сохранения результатов (по умолчанию: output)")
    args = parser.parse_args()

    src = Path(args.source)
    if not src.is_absolute():
        src = (Path(__file__).parent / src).resolve()

    if src.is_file():
        files = [src]
    elif src.is_dir():
        files = sorted(p for p in src.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    else:
        raise SystemExit(f"Файл или папка не найдены: {src}")

    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = (Path(__file__).parent / output_dir).resolve()

    client = get_client()
    print(f"Подключение к Roboflow Cloud ({MODEL_ID})...")
    print(f"Обработка изображений: {len(files)} шт.")

    all_results = []
    for f in files:
        res = process_image(client, f, args.conf, output_dir)
        if res:
            all_results.append(res)
            summary = [f"{o['class']} ({o['confidence']})" for o in res['objects']]
            print(f"  {f.name}: {res['objects_count']} объ. -> {', '.join(summary) if summary else 'ничего не найдено'}")

    report_file = output_dir / "roboflow_results.json"
    with open(report_file, "w", encoding="utf-8") as out:
        json.dump(all_results, out, indent=2, ensure_ascii=False)

    print(f"\n[УСПЕХ] Готово!")
    print(f"  Размеченные снимки: {output_dir / 'annotated'}")
    print(f"  Вырезанные номера:  {output_dir / 'plate_crops'}")
    print(f"  JSON-отчёт:         {report_file}")

if __name__ == "__main__":
    main()
