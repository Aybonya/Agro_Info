"""
Train YOLO11n to detect license plates, trucks, tractors, and trailers.
"""
from pathlib import Path
import shutil
import json
import torch
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
DATA_YAML = ROOT / "dataset_truck_plate.yaml"
OUTPUT_DIR = WORKSPACE / "models"
SAVED_MODEL = OUTPUT_DIR / "truck_plate_yolo11n.pt"

def get_device():
    if torch.cuda.is_available():
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        return 0
    print("Using CPU")
    return "cpu"

def train():
    device = get_device()
    print(f"Loading pretrained YOLO11n base weights...")
    base_model_path = WORKSPACE / "yolo11n.pt"
    if not base_model_path.exists():
        base_model_path = ROOT / "yolo11n.pt"
    
    model = YOLO(str(base_model_path) if base_model_path.exists() else "yolo11n.pt")

    print(f"Starting training on {DATA_YAML} for 50 epochs...")
    results = model.train(
        data=str(DATA_YAML),
        epochs=50,
        imgsz=640,
        batch=4,
        device=device,
        workers=0,
        patience=15,
        project=str(ROOT / "runs"),
        name="truck_plate_detector",
        exist_ok=True,
        pretrained=True,
        seed=42,
        plots=True,
        verbose=True,
    )

    best_pt = ROOT / "runs" / "truck_plate_detector" / "weights" / "best.pt"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if best_pt.exists():
        shutil.copy(best_pt, SAVED_MODEL)
        print(f"\n[OK] Best model saved to: {SAVED_MODEL}")
        print(f"[OK] Training run weights: {best_pt}")

    # Validation
    print("\nRunning final validation on val set...")
    val_model = YOLO(str(best_pt if best_pt.exists() else SAVED_MODEL))
    metrics = val_model.val(data=str(DATA_YAML), split="val", verbose=True)

    summary = {
        "mAP50": float(metrics.box.map50),
        "mAP50_95": float(metrics.box.map),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
        "classes": list(metrics.names.values()),
    }

    # Per-class mAP50
    if hasattr(metrics.box, "maps") and metrics.box.maps is not None:
        summary["per_class_mAP50"] = {
            metrics.names[i]: float(metrics.box.maps[i]) for i in range(len(metrics.names))
        }

    summary_file = ROOT / "runs" / "truck_plate_detector" / "summary_metrics.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print("TRAINING FINISHED SUCCESSFULLY!")
    print(f"Overall mAP50:    {summary['mAP50'] * 100:.2f}%")
    print(f"Overall mAP50-95: {summary['mAP50_95'] * 100:.2f}%")
    print(f"Overall Precision: {summary['precision'] * 100:.2f}%")
    print(f"Overall Recall:    {summary['recall'] * 100:.2f}%")
    print("=" * 50)
    return results

if __name__ == "__main__":
    train()
