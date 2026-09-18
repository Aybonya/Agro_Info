"""
Inference utility for truck and license plate detection.
Detects both vehicles (truck, car, etc.) and license plates on weighbridge camera images.
Supports:
1) roboflow: Roboflow Cloud model (trucks-dataset-dqp47/2) for trucks + local detector for license plates
2) pipeline: Local high-precision dual models (YOLO11 vehicle + dedicated license plate detector)
3) unified: Local single-pass YOLO11 model trained on weighbridge dataset (models/truck_plate_yolo11n.pt)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
UNIFIED_MODEL = WORKSPACE / "models" / "truck_plate_yolo11n.pt"
VEHICLE_MODEL = WORKSPACE / "yolo11n.pt"
PLATE_MODEL = WORKSPACE / "ALPR-Auto-Processor" / "models" / "license_plate_yolov8n.pt"

ROBOFLOW_API_URL = "https://serverless.roboflow.com"
ROBOFLOW_API_KEY = "T6sW80zFrGiFCA9k112V"
ROBOFLOW_MODEL_ID = "trucks-dataset-dqp47/6"

CLASS_COLORS = {
    "license_plate": (0, 215, 255),  # Gold/Yellow
    "license plate": (0, 215, 255),
    "truck": (255, 140, 0),          # Azure/Blue in BGR
    "car": (255, 191, 0),            # Cyan/Light Blue
    "tractor": (50, 205, 50),        # Lime Green
    "trailer": (180, 105, 255),      # Purple
    "bus": (230, 216, 173),
}

def clamp_crop(image, xyxy, padding=0.08):
    """Crop bounding box with padding, constrained to image boundaries."""
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
    thickness = max(2, int(min(canvas.shape[:2]) / 400))
    cv2.rectangle(canvas, (x1, y1), (x2, y2), color, thickness)
    
    text = f"{label} {conf:.2f}"
    font_scale = max(0.55, thickness * 0.22)
    (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
    text_y = max(y1 - 6, text_h + 4)
    cv2.rectangle(canvas, (x1, text_y - text_h - 4), (x1 + text_w + 6, text_y + baseline), color, -1)
    cv2.putText(canvas, text, (x1 + 3, text_y - 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 1, cv2.LINE_AA)

def predict_single_pipeline(
    img: cv2.typing.MatLike,
    image_name: str,
    v_model: YOLO,
    p_model: YOLO,
    conf: float = 0.25,
    imgsz: int = 1280,
    crops_dir: Path | None = None,
    annotated_dir: Path | None = None,
):
    canvas = img.copy()
    detections = []
    plate_idx = 0

    # 1. Detect vehicles
    res_v = v_model.predict(img, imgsz=imgsz, conf=conf, verbose=False)[0]
    for box in res_v.boxes:
        cls_id = int(box.cls.item())
        cls_name = res_v.names[cls_id]
        if cls_name not in {"truck", "car", "bus", "tractor", "trailer"}:
            continue
        c = float(box.conf.item())
        xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
        draw_box(canvas, cls_name, c, xyxy, CLASS_COLORS.get(cls_name, (255, 140, 0)))
        detections.append({
            "class": cls_name,
            "confidence": round(c, 3),
            "bbox_xyxy": xyxy,
            "source": "local_yolo",
        })

    # 2. Detect license plates
    res_p = p_model.predict(img, imgsz=imgsz, conf=conf, verbose=False)[0]
    for box in res_p.boxes:
        c = float(box.conf.item())
        xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
        draw_box(canvas, "license_plate", c, xyxy, CLASS_COLORS["license_plate"])
        
        det_rec = {
            "class": "license_plate",
            "confidence": round(c, 3),
            "bbox_xyxy": xyxy,
            "source": "local_plate_yolo",
        }

        if crops_dir:
            plate_idx += 1
            crop_img, _ = clamp_crop(img, xyxy)
            if crop_img.size > 0:
                crop_name = f"{Path(image_name).stem}_plate_{plate_idx}.jpg"
                crop_path = crops_dir / crop_name
                cv2.imwrite(str(crop_path), crop_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                det_rec["crop_file"] = crop_name

        detections.append(det_rec)

    if annotated_dir:
        out_img_path = annotated_dir / image_name
        cv2.imwrite(str(out_img_path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])

    return {
        "image": image_name,
        "width": img.shape[1],
        "height": img.shape[0],
        "detections_count": len(detections),
        "detections": detections,
    }

def predict_single_roboflow(
    img_path: Path,
    rf_client,
    p_model: YOLO,
    conf: float = 0.20,
    imgsz: int = 1280,
    crops_dir: Path | None = None,
    annotated_dir: Path | None = None,
):
    img = cv2.imread(str(img_path))
    if img is None:
        return None

    canvas = img.copy()
    detections = []
    plate_idx = 0

    # 1. Detect trucks via Roboflow Cloud
    rf_res = rf_client.infer(str(img_path), model_id=ROBOFLOW_MODEL_ID)
    img_w, img_h = img.shape[1], img.shape[0]

    for pred in rf_res.get("predictions", []):
        c = float(pred.get("confidence", 0.0))
        if c < conf:
            continue
        xc, yc = float(pred["x"]), float(pred["y"])
        w, h = float(pred["width"]), float(pred["height"])
        x1 = max(0, int(xc - w / 2))
        y1 = max(0, int(yc - h / 2))
        x2 = min(img_w, int(xc + w / 2))
        y2 = min(img_h, int(yc + h / 2))
        xyxy = [x1, y1, x2, y2]
        cls_name = pred.get("class", "truck")

        draw_box(canvas, f"Roboflow {cls_name}", c, xyxy, (255, 140, 0))
        detections.append({
            "class": cls_name,
            "confidence": round(c, 3),
            "bbox_xyxy": xyxy,
            "source": "roboflow_cloud",
            "model_id": ROBOFLOW_MODEL_ID,
        })

    # 2. Detect license plates
    res_p = p_model.predict(img, imgsz=imgsz, conf=conf, verbose=False)[0]
    for box in res_p.boxes:
        c = float(box.conf.item())
        xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
        draw_box(canvas, "license_plate", c, xyxy, CLASS_COLORS["license_plate"])

        det_rec = {
            "class": "license_plate",
            "confidence": round(c, 3),
            "bbox_xyxy": xyxy,
            "source": "local_plate_yolo",
        }

        if crops_dir:
            plate_idx += 1
            crop_img, _ = clamp_crop(img, xyxy)
            if crop_img.size > 0:
                crop_name = f"{img_path.stem}_plate_{plate_idx}.jpg"
                crop_path = crops_dir / crop_name
                cv2.imwrite(str(crop_path), crop_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                det_rec["crop_file"] = crop_name

        detections.append(det_rec)

    if annotated_dir:
        out_img_path = annotated_dir / img_path.name
        cv2.imwrite(str(out_img_path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])

    return {
        "image": img_path.name,
        "width": img_w,
        "height": img_h,
        "detections_count": len(detections),
        "detections": detections,
    }

def predict_single_unified(
    img: cv2.typing.MatLike,
    image_name: str,
    u_model: YOLO,
    conf: float = 0.15,
    imgsz: int = 1280,
    crops_dir: Path | None = None,
    annotated_dir: Path | None = None,
):
    canvas = img.copy()
    detections = []
    plate_idx = 0

    res = u_model.predict(img, imgsz=imgsz, conf=conf, verbose=False)[0]
    for box in res.boxes:
        cls_id = int(box.cls.item())
        cls_name = res.names[cls_id]
        c = float(box.conf.item())
        xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
        draw_box(canvas, cls_name, c, xyxy, CLASS_COLORS.get(cls_name, (0, 255, 0)))

        det_rec = {
            "class": cls_name,
            "confidence": round(c, 3),
            "bbox_xyxy": xyxy,
            "source": "unified_yolo11",
        }

        if "plate" in cls_name.lower() and crops_dir:
            plate_idx += 1
            crop_img, _ = clamp_crop(img, xyxy)
            if crop_img.size > 0:
                crop_name = f"{Path(image_name).stem}_plate_{plate_idx}.jpg"
                crop_path = crops_dir / crop_name
                cv2.imwrite(str(crop_path), crop_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                det_rec["crop_file"] = crop_name

        detections.append(det_rec)

    if annotated_dir:
        out_img_path = annotated_dir / image_name
        cv2.imwrite(str(out_img_path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])

    return {
        "image": image_name,
        "width": img.shape[1],
        "height": img.shape[0],
        "detections_count": len(detections),
        "detections": detections,
    }

def main():
    parser = argparse.ArgumentParser(description="Predict vehicles and license plates from photos")
    parser.add_argument("source", nargs="?", default="Auto", help="Path to image file or directory (default: Auto)")
    parser.add_argument("--mode", choices=["roboflow", "pipeline", "unified"], default="roboflow",
                        help="Detection mode: 'roboflow' (Roboflow Cloud for trucks + plate detector), 'pipeline' (local dual models), or 'unified' (single YOLO11)")
    parser.add_argument("--conf", type=float, default=0.20, help="Confidence threshold (default: 0.20)")
    parser.add_argument("--imgsz", type=int, default=1280, help="Inference resolution (default: 1280)")
    parser.add_argument("--output-dir", default="output", help="Directory for output results")
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.is_absolute():
        source_path = (WORKSPACE / source_path).resolve()

    if source_path.is_file():
        files = [source_path]
    elif source_path.is_dir():
        files = sorted(p for p in source_path.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    else:
        raise SystemExit(f"Source path not found: {source_path}")

    out_base = Path(args.output_dir)
    if not out_base.is_absolute():
        out_base = (WORKSPACE / out_base).resolve()

    crops_dir = out_base / "plate_crops"
    annotated_dir = out_base / "annotated"
    crops_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)

    print(f"Mode: {args.mode}")
    print(f"Processing {len(files)} image(s) from {source_path}...")

    all_results = []
    if args.mode == "roboflow":
        from inference_sdk import InferenceHTTPClient, InferenceConfiguration
        print(f"Connecting to Roboflow Cloud model ({ROBOFLOW_MODEL_ID})...")
        rf_client = InferenceHTTPClient(
            api_url=ROBOFLOW_API_URL,
            api_key=ROBOFLOW_API_KEY
        ).configure(InferenceConfiguration(api_key_transport="header"))
        p_model = YOLO(str(PLATE_MODEL))
        
        for img_file in files:
            res = predict_single_roboflow(img_file, rf_client, p_model, conf=args.conf, imgsz=args.imgsz, crops_dir=crops_dir, annotated_dir=annotated_dir)
            if res:
                all_results.append(res)
                classes_found = [f"{d['class']} [{d.get('source','')}] ({d['confidence']})" for d in res['detections']]
                print(f"  {img_file.name}: {', '.join(classes_found) if classes_found else 'none'}")

    elif args.mode == "unified":
        if not UNIFIED_MODEL.exists():
            raise SystemExit(f"Unified model weights not found at: {UNIFIED_MODEL}")
        print(f"Loading unified model: {UNIFIED_MODEL}")
        model = YOLO(str(UNIFIED_MODEL))
        for img_file in files:
            img = cv2.imread(str(img_file))
            if img is None: continue
            res = predict_single_unified(img, img_file.name, model, conf=args.conf, imgsz=args.imgsz, crops_dir=crops_dir, annotated_dir=annotated_dir)
            all_results.append(res)
            print(f"  {img_file.name}: {[d['class'] for d in res['detections']]}")

    else:
        print(f"Loading vehicle detector ({VEHICLE_MODEL.name}) and license plate detector ({PLATE_MODEL.name})...")
        v_model = YOLO(str(VEHICLE_MODEL))
        p_model = YOLO(str(PLATE_MODEL))
        for img_file in files:
            img = cv2.imread(str(img_file))
            if img is None: continue
            res = predict_single_pipeline(img, img_file.name, v_model, p_model, conf=args.conf, imgsz=args.imgsz, crops_dir=crops_dir, annotated_dir=annotated_dir)
            all_results.append(res)
            classes_found = [f"{d['class']} ({d['confidence']})" for d in res['detections']]
            print(f"  {img_file.name}: {', '.join(classes_found) if classes_found else 'none'}")

    report_path = out_base / "detection_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Completed {len(all_results)} images!")
    print(f"  Annotated images: {annotated_dir}")
    print(f"  Cropped plates:   {crops_dir}")
    print(f"  JSON report:      {report_path}")

if __name__ == "__main__":
    main()
