"""Detect equipment on a weighbridge image with a safe temporary fallback."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
CUSTOM = ROOT / "runs" / "weighbridge_truck" / "weights" / "best.pt"
VEHICLE_CLASSES = {"truck", "train"}


def largest_candidate(result, names, accepted):
    candidates = [box for box in result.boxes if names[int(box.cls[0])] in accepted]
    return max(candidates, key=lambda box: float((box.xywh[0][2] * box.xywh[0][3]).item())) if candidates else None


def as_record(image, box, method):
    if box is None:
        return {"image": image.name, "equipment": None, "method": None}
    x1, y1, x2, y2 = (round(float(v), 1) for v in box.xyxy[0])
    return {"image": image.name, "equipment": {"label": "gruzovik", "confidence": round(float(box.conf[0]), 3), "bbox_xyxy": [x1, y1, x2, y2]}, "method": method}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="JPG file or directory")
    source = Path(parser.parse_args().source)
    files = [source] if source.is_file() else sorted(source.glob("*.jpg"))
    if not files:
        raise SystemExit("No JPG files found")
    custom, fallback = YOLO(CUSTOM), YOLO("yolo11n.pt")
    report = []
    for image in files:
        result = custom(str(image), conf=0.05, verbose=False)[0]
        box = largest_candidate(result, result.names, {"gruzovik"})
        method = "fine_tuned"
        if box is None:
            result = fallback(str(image), conf=0.05, verbose=False)[0]
            box = largest_candidate(result, result.names, VEHICLE_CLASSES)
            method = "foundation_fallback"
        row = as_record(image, box, method)
        report.append(row)
        print(json.dumps(row, ensure_ascii=False))
    (ROOT / "latest_detection.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
