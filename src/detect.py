"""Детекция техники на изображении с помощью YOLOv8 (предобученная COCO-модель)."""
from dataclasses import dataclass
from ultralytics import YOLO

from config import VEHICLE_COCO_CLASSES

_model = None


@dataclass
class Detection:
    bbox: tuple  # x1, y1, x2, y2
    coco_class: str
    confidence: float


def get_model() -> YOLO:
    global _model
    if _model is None:
        _model = YOLO("yolov8n.pt")
    return _model


def detect_vehicles(image_path: str) -> list[Detection]:
    model = get_model()
    # imgsz=1280: снимки с весовой — full-HD/широкоугольные, техника часто занимает
    # небольшую часть кадра. При стандартном imgsz=640 YOLO её banально не находит.
    result = model.predict(source=image_path, verbose=False, imgsz=1280)[0]
    names = result.names
    detections = []
    for box in result.boxes:
        cls_name = names[int(box.cls[0])]
        if cls_name not in VEHICLE_COCO_CLASSES:
            continue
        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
        detections.append(Detection(
            bbox=(x1, y1, x2, y2),
            coco_class=cls_name,
            confidence=float(box.conf[0]),
        ))
    detections.sort(key=lambda d: (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1]), reverse=True)
    return detections
