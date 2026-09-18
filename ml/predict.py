"""Run the trained model on a new photo or an entire folder.

Example:
    python predict.py ../Auto/1.jpg
"""
import argparse
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
WEIGHTS = ROOT / "runs" / "weighbridge_truck" / "weights" / "best.pt"

parser = argparse.ArgumentParser()
parser.add_argument("source", help="Photo or folder to analyse")
args = parser.parse_args()

model = YOLO(WEIGHTS)
results = model.predict(args.source, conf=0.35, save=True, project=str(ROOT / "predictions"), name="latest", exist_ok=True)
for result in results:
    print(f"{Path(result.path).name}: {len(result.boxes)} unit(s) of equipment detected")
