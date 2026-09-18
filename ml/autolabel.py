"""Create an initial YOLO dataset from unlabelled gate-camera photos.

The generated labels must be reviewed before they become production ground truth.
For the current single-camera collection, COCO's `truck` and `train` detections
both frequently correspond to a truck on the weighbridge, so they are merged
into one class: gruzovik.
"""
from __future__ import annotations

import random
import shutil
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "Auto"
OUT = ROOT / "dataset"
VALID_SOURCE_CLASSES = {"truck", "train"}
RANDOM_SEED = 42


def yolo_row(box, width: int, height: int) -> str:
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    xc = ((x1 + x2) / 2) / width
    yc = ((y1 + y2) / 2) / height
    bw = (x2 - x1) / width
    bh = (y2 - y1) / height
    return f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n"


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Source folder not found: {SOURCE}")
    images = sorted(SOURCE.glob("*.jpg"), key=lambda p: int(p.stem))
    if not images:
        raise SystemExit("No JPG photos found in Auto")

    if OUT.exists():
        shutil.rmtree(OUT)
    for split in ("train", "val"):
        (OUT / "images" / split).mkdir(parents=True)
        (OUT / "labels" / split).mkdir(parents=True)

    model = YOLO("yolo11n.pt")
    accepted = []
    skipped = []
    for image_path in images:
        result = model(str(image_path), conf=0.05, verbose=False)[0]
        candidates = [
            box for box in result.boxes
            if result.names[int(box.cls[0])] in VALID_SOURCE_CLASSES
        ]
        if not candidates:
            skipped.append(image_path.name)
            continue
        # The largest suitable detection is the truck on the weighbridge.
        best = max(candidates, key=lambda b: float((b.xywh[0][2] * b.xywh[0][3]).item()))
        accepted.append((image_path, yolo_row(best, result.orig_shape[1], result.orig_shape[0])))

    random.Random(RANDOM_SEED).shuffle(accepted)
    val_count = max(1, round(len(accepted) * 0.2))
    for i, (image_path, label) in enumerate(accepted):
        split = "val" if i < val_count else "train"
        shutil.copy2(image_path, OUT / "images" / split / image_path.name)
        (OUT / "labels" / split / f"{image_path.stem}.txt").write_text(label, encoding="utf-8")

    (OUT / "autolabel_report.txt").write_text(
        "Autolabel report\n"
        f"Source photos: {len(images)}\n"
        f"Auto-labelled: {len(accepted)}\n"
        f"Train: {len(accepted) - val_count}\n"
        f"Validation: {val_count}\n"
        f"Skipped: {', '.join(skipped) if skipped else 'none'}\n"
        "\nReview labels visually before deployment.\n",
        encoding="utf-8",
    )
    print((OUT / "autolabel_report.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
