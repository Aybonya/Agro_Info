"""
Roboflow Cloud Truck & License Plate Detector
Uses the user's latest trained Roboflow model:
  - Workspace: akh-xkhw0
  - Project: trucks-dataset-dqp47
  - Version: 6 (v6 - trained on 3,349 images, YOLO26 Nano)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import cv2
from inference_sdk import InferenceHTTPClient, InferenceConfiguration

API_URL = "https://serverless.roboflow.com"
API_KEY = "T6sW80zFrGiFCA9k112V"
MODEL_ID = "trucks-dataset-dqp47/6"  # Version 6 is the user's latest trained model!

CLASS_COLORS = {
    "license plate": (0, 215, 255),  # Gold/Yellow
    "truck": (255, 140, 0),          # Azure/Blue
    "trailer": (180, 105, 255),      # Purple
    "tractor": (50, 205, 50),        # Green
}

def get_client() -> InferenceHTTPClient:
    return InferenceHTTPClient(
        api_url=API_URL,
        api_key=API_KEY
    ).configure(InferenceConfiguration(
        api_key_transport="header"
    ))

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

def detect_roboflow(client: InferenceHTTPClient, image_path: str | Path, conf_threshold: float = 0.35) -> dict:
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    res = client.infer(str(image_path), model_id=MODEL_ID)
    
    img_w = res.get("image", {}).get("width", 0)
    img_h = res.get("image", {}).get("height", 0)
    
    parsed_objects = []
    for pred in res.get("predictions", []):
        confidence = float(pred.get("confidence", 0.0))
        if confidence < conf_threshold:
            continue
        
        xc = float(pred["x"])
        yc = float(pred["y"])
        w = float(pred["width"])
        h = float(pred["height"])

        x1 = max(0, int(xc - w / 2))
        y1 = max(0, int(yc - h / 2))
        x2 = min(img_w or 99999, int(xc + w / 2))
        y2 = min(img_h or 99999, int(yc + h / 2))

        parsed_objects.append({
            "class": pred.get("class"),
            "confidence": round(confidence, 3),
            "bbox_xyxy": [x1, y1, x2, y2],
            "detection_id": pred.get("detection_id"),
        })

    return {
        "image": image_path.name,
        "width": img_w,
        "height": img_h,
        "model_id": MODEL_ID,
        "objects_count": len(parsed_objects),
        "objects": parsed_objects,
    }

def annotate_and_crop(image_path: Path, objects: list[dict], annotated_path: Path, crops_dir: Path | None = None):
    img = cv2.imread(str(image_path))
    if img is None:
        return
    
    thickness = max(2, int(min(img.shape[:2]) / 350))
    plate_idx = 0

    for obj in objects:
        cls_name = obj["class"]
        color = CLASS_COLORS.get(cls_name, (0, 255, 0))
        x1, y1, x2, y2 = obj["bbox_xyxy"]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        
        label = f"{cls_name} {obj['confidence']:.2f}"
        font_scale = max(0.55, thickness * 0.22)
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        text_y = max(y1 - 6, th + 4)
        cv2.rectangle(img, (x1, text_y - th - 4), (x1 + tw + 6, text_y + baseline), color, -1)
        cv2.putText(img, label, (x1 + 3, text_y - 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 1, cv2.LINE_AA)

        if "plate" in cls_name.lower() and crops_dir:
            plate_idx += 1
            crop_img, _ = clamp_crop(img, obj["bbox_xyxy"])
            if crop_img.size > 0:
                crop_file = crops_dir / f"{image_path.stem}_plate_{plate_idx}.jpg"
                cv2.imwrite(str(crop_file), crop_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                obj["crop_file"] = crop_file.name

    annotated_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(annotated_path), img, [cv2.IMWRITE_JPEG_QUALITY, 92])

def main():
    parser = argparse.ArgumentParser(description="Detect trucks and plates using Roboflow Cloud model v5")
    parser.add_argument("source", nargs="?", default="Auto/10.jpg", help="Image path or folder (default: Auto/10.jpg)")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold (default: 0.35)")
    parser.add_argument("--output-dir", default="output/roboflow_results", help="Output directory for annotated images and crops")
    args = parser.parse_args()

    source = Path(args.source)
    if source.is_file():
        files = [source]
    elif source.is_dir():
        files = sorted(p for p in source.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    else:
        raise SystemExit(f"Source not found: {source}")

    client = get_client()
    output_dir = Path(args.output_dir)
    annotated_dir = output_dir / "annotated"
    crops_dir = output_dir / "plate_crops"
    annotated_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to Roboflow Cloud ({MODEL_ID} - latest v6)...")
    print(f"Processing {len(files)} image(s)...")

    results = []
    for f in files:
        res = detect_roboflow(client, f, conf_threshold=args.conf)
        out_img = annotated_dir / f.name
        annotate_and_crop(f, res["objects"], out_img, crops_dir=crops_dir)
        results.append(res)
        summary = [f"{o['class']} ({o['confidence']})" for o in res['objects']]
        print(f"  {f.name}: {res['objects_count']} object(s) -> {', '.join(summary) if summary else 'none'}")

    json_report = output_dir / "roboflow_results.json"
    with open(json_report, "w", encoding="utf-8") as out_f:
        json.dump(results, out_f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Annotated images saved to: {annotated_dir}")
    print(f"[OK] License plate crops saved to: {crops_dir}")
    print(f"[OK] Results saved to: {json_report}")

if __name__ == "__main__":
    main()
