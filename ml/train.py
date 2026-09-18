"""Fine-tune a detector for the weighbridge camera."""
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    model = YOLO("yolo11n.pt")
    model.train(
        data=str(ROOT / "data.yaml"),
        # This environment has a CPU-only PyTorch build. Change to device=0
        # after installing a CUDA-enabled PyTorch build for the RTX 3050.
        epochs=50,
        imgsz=640,
        batch=2,
        device="cpu",
        workers=0,
        patience=15,
        project=str(ROOT / "runs"),
        name="weighbridge_truck",
        exist_ok=True,
        pretrained=True,
        seed=42,
        plots=True,
    )
