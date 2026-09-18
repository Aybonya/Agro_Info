"""Общие настройки и справочники для пайплайна распознавания техники и номеров."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "Auto"
RESULTS_DIR = ROOT_DIR / "results"
ANNOTATED_DIR = RESULTS_DIR / "annotated"
PLATES_DIR = RESULTS_DIR / "plates"

# Классы COCO (YOLOv8), которые считаем "техникой"
VEHICLE_COCO_CLASSES = {"car", "truck", "bus"}

# Известные производители техники (для сопоставления текста с кузова/решётки)
KNOWN_MANUFACTURERS = [
    "KAMAZ", "MAZ", "GAZ", "ZIL", "URAL", "UAZ", "MTZ", "BELARUS",
    "VOLVO", "MAN", "SCANIA", "ISUZU", "HYUNDAI", "FOTON", "HOWO",
    "IVECO", "DAF", "MERCEDES", "RENAULT", "JOHN DEERE", "CASE",
    "CLAAS", "NEW HOLLAND", "SHACMAN", "FAW", "KIROVETS", "LOVOL",
]

# Типы техники для zero-shot классификации через CLIP (RU-подписи для отчёта)
VEHICLE_TYPES = {
    "dump_truck": "a dump truck with a tipping cargo box (samosval)",
    "flatbed_grain_truck": "a flatbed truck with side rails carrying grain, covered with a tarp",
    "tanker_truck": "a tanker truck with a cylindrical tank",
    "tractor": "a farm tractor",
    "car": "a passenger car or pickup",
    "bus": "a bus",
    "special_equipment": "an excavator, loader or other special construction equipment",
}

TYPE_RU_LABELS = {
    "dump_truck": "Самосвал",
    "flatbed_grain_truck": "Бортовой/зерновоз",
    "tanker_truck": "Автоцистерна",
    "tractor": "Трактор",
    "car": "Легковой автомобиль",
    "bus": "Автобус",
    "special_equipment": "Спецтехника",
}

# Регэксп-паттерн номеров Казахстана: 3 цифры + 1-3 буквы + 2 цифры региона
import re  # noqa: E402
PLATE_REGEX = re.compile(r"^\d{3}[A-Z]{1,3}\d{2}$")
