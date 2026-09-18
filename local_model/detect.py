"""
Локальная высокоточная детекция транспорта и номерных знаков (без интернета).
Использует обученную модель YOLO11 (truck_plate_yolo11n.pt) с метрикой mAP@50 = 94.1%!
Классы:
  - truck         (грузовик / тягач)
  - trailer       (прицеп / полуприцеп / кузов)
  - license plate (номерной знак)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
WEIGHTS_DIR = ROOT / "weights"

UNIFIED_WEIGHTS = WEIGHTS_DIR / "truck_plate_yolo11n.pt"
VEHICLE_WEIGHTS = WEIGHTS_DIR / "yolo11n.pt"
PLATE_WEIGHTS = WEIGHTS_DIR / "license_plate_yolov8n.pt"

CLASS_COLORS = {
    "license plate": (0, 215, 255),  # Жёлтый / Золотистый
    "license_plate": (0, 215, 255),
    "truck": (255, 140, 0),          # Синий / Лазурный в BGR
    "trailer": (180, 105, 255),      # Фиолетовый / Пурпурный
    "car": (255, 191, 0),
    "tractor": (50, 205, 50),
}

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

def draw_box(canvas, label, conf, xyxy, color):
    x1, y1, x2, y2 = map(int, xyxy)
    thickness = max(2, int(min(canvas.shape[:2]) / 350))
    cv2.rectangle(canvas, (x1, y1), (x2, y2), color, thickness)
    
    text = f"{label} {conf:.2f}"
    font_scale = max(0.55, thickness * 0.22)
    (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
    text_y = max(y1 - 6, text_h + 4)
    cv2.rectangle(canvas, (x1, text_y - text_h - 4), (x1 + text_w + 6, text_y + baseline), color, -1)
    cv2.putText(canvas, text, (x1 + 3, text_y - 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 1, cv2.LINE_AA)

def detect_image(
    img: cv2.typing.MatLike,
    image_name: str,
    u_model: YOLO,
    v_model: YOLO | None = None,
    p_model: YOLO | None = None,
    conf: float = 0.25,
    imgsz: int = 1280,
    output_dir: Path | None = None,
):
    annotated = img.copy()
    crops_dir = output_dir / "plate_crops" if output_dir else None
    annotated_dir = output_dir / "annotated" if output_dir else None
    if crops_dir: crops_dir.mkdir(parents=True, exist_ok=True)
    if annotated_dir: annotated_dir.mkdir(parents=True, exist_ok=True)

    objects = []
    plate_idx = 0

    # 1. Запуск основной обученной модели (YOLO11 mAP=94.1%)
    res_u = u_model.predict(img, imgsz=imgsz, conf=conf, verbose=False)[0]
    for box in res_u.boxes:
        cls_name = res_u.names[int(box.cls.item())]
        c = float(box.conf.item())
        xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
        
        color = CLASS_COLORS.get(cls_name, (0, 255, 0))
        draw_box(annotated, cls_name, c, xyxy, color)

        obj_rec = {"class": cls_name, "confidence": round(c, 3), "bbox_xyxy": xyxy}
        if "plate" in cls_name.lower() and crops_dir:
            plate_idx += 1
            crop_img, _ = clamp_crop(img, xyxy)
            if crop_img.size > 0:
                crop_name = f"{Path(image_name).stem}_plate_{plate_idx}.jpg"
                cv2.imwrite(str(crops_dir / crop_name), crop_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                obj_rec["crop_file"] = crop_name
        objects.append(obj_rec)

    # 2. Если грузовик или номер не найдены — используем специализированный фолбэк
    has_vehicle = any(o["class"] in {"truck", "trailer", "car"} for o in objects)
    has_plate = any("plate" in o["class"].lower() for o in objects)

    if not has_vehicle and v_model:
        res_v = v_model.predict(img, imgsz=imgsz, conf=conf, verbose=False)[0]
        for box in res_v.boxes:
            v_name = res_v.names[int(box.cls.item())]
            if v_name in {"truck", "trailer", "car"}:
                c = float(box.conf.item())
                xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
                draw_box(annotated, v_name, c, xyxy, CLASS_COLORS.get(v_name, (255, 140, 0)))
                objects.append({"class": v_name, "confidence": round(c, 3), "bbox_xyxy": xyxy})
                break

    if not has_plate and p_model:
        res_p = p_model.predict(img, imgsz=imgsz, conf=conf, verbose=False)[0]
        for box in res_p.boxes:
            c = float(box.conf.item())
            xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
            draw_box(annotated, "license plate", c, xyxy, CLASS_COLORS["license plate"])
            obj_rec = {"class": "license plate", "confidence": round(c, 3), "bbox_xyxy": xyxy}
            if crops_dir:
                plate_idx += 1
                crop_img, _ = clamp_crop(img, xyxy)
                if crop_img.size > 0:
                    crop_name = f"{Path(image_name).stem}_plate_{plate_idx}.jpg"
                    cv2.imwrite(str(crops_dir / crop_name), crop_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    obj_rec["crop_file"] = crop_name
            objects.append(obj_rec)

    if annotated_dir:
        cv2.imwrite(str(annotated_dir / image_name), annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])

    return {
        "image": image_name,
        "width": img.shape[1],
        "height": img.shape[0],
        "objects_count": len(objects),
        "objects": objects,
    }

def main():
    parser = argparse.ArgumentParser(description="Высокоточная локальная детекция: truck, trailer, license plate")
    parser.add_argument("source", nargs="?", default="../Auto/10.jpg", help="Путь к фото или папке (по умолчанию: ../Auto/10.jpg)")
    parser.add_argument("--conf", type=float, default=0.25, help="Порог уверенности (по умолчанию: 0.25)")
    parser.add_argument("--imgsz", type=int, default=1280, help="Разрешение инференса (по умолчанию: 1280)")
    parser.add_argument("--output", default="output", help="Папка вывода (по умолчанию: output)")
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

    print(f"Загрузка обученной модели: {UNIFIED_WEIGHTS.name} (mAP 94.1%)...")
    u_model = YOLO(str(UNIFIED_WEIGHTS))
    v_model = YOLO(str(VEHICLE_WEIGHTS)) if VEHICLE_WEIGHTS.exists() else None
    p_model = YOLO(str(PLATE_WEIGHTS)) if PLATE_WEIGHTS.exists() else None

    print(f"Обработка {len(files)} изображений...")
    all_results = []
    for f in files:
        img = cv2.imread(str(f))
        if img is None: continue
        res = detect_image(img, f.name, u_model, v_model, p_model, conf=args.conf, imgsz=args.imgsz, output_dir=output_dir)
        all_results.append(res)
        summary = [f"{o['class']} ({o['confidence']})" for o in res['objects']]
        print(f"  {f.name}: {', '.join(summary) if summary else 'ничего не найдено'}")

    report_file = output_dir / "local_results.json"
    with open(report_file, "w", encoding="utf-8") as out:
        json.dump(all_results, out, indent=2, ensure_ascii=False)

    print(f"\n[УСПЕХ] Готово!")
    print(f"  Размеченные снимки: {output_dir / 'annotated'}")
    print(f"  Вырезанные номера:  {output_dir / 'plate_crops'}")
    print(f"  JSON-отчёт:         {report_file}")

if __name__ == "__main__":
    main()
