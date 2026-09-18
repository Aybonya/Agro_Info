"""
Скрипт объединения и стандартизации датасетов в единый формат YOLO:
Целевые классы:
  0: license plate  (номерной знак)
  1: truck          (грузовик / тягач / машина)
  2: trailer        (прицеп / полуприцеп / кузов)
"""
from pathlib import Path
import shutil
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
DATASET_DIR = WORKSPACE / "local_model" / "dataset"

TRAIN_IMG = DATASET_DIR / "train" / "images"
TRAIN_LBL = DATASET_DIR / "train" / "labels"
VAL_IMG = DATASET_DIR / "valid" / "images"
VAL_LBL = DATASET_DIR / "valid" / "labels"

def setup_dirs():
    for d in [TRAIN_IMG, TRAIN_LBL, VAL_IMG, VAL_LBL]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

def process_truck_and_box():
    """
    truck and truck box.v4i.yolov8:
      0: Box   -> 2 (trailer)
      1: Truck -> 1 (truck)
    """
    src = WORKSPACE / "truck and truck box.v4i.yolov8"
    if not src.exists():
        return 0, 0

    counts = {"train": 0, "val": 0}
    splits = [("train", TRAIN_IMG, TRAIN_LBL), ("valid", VAL_IMG, VAL_LBL), ("test", TRAIN_IMG, TRAIN_LBL)]
    idx = 0
    for split_name, dst_img, dst_lbl in splits:
        img_dir = src / split_name / "images"
        lbl_dir = src / split_name / "labels"
        if not img_dir.exists(): continue
        
        for img_p in img_dir.glob("*.*"):
            lbl_p = lbl_dir / f"{img_p.stem}.txt"
            if not lbl_p.exists(): continue
            
            new_lines = []
            for line in lbl_p.read_text(encoding="utf-8", errors="ignore").splitlines():
                parts = line.strip().split()
                if not parts: continue
                c = int(parts[0])
                target_c = 2 if c == 0 else 1  # 0:Box -> 2:trailer, 1:Truck -> 1:truck
                new_lines.append(f"{target_c} {' '.join(parts[1:])}")

            if new_lines:
                idx += 1
                dst_name = f"ttb_{idx:05d}{img_p.suffix.lower()}"
                shutil.copy(img_p, dst_img / dst_name)
                (dst_lbl / f"ttb_{idx:05d}.txt").write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                counts["val" if split_name == "valid" else "train"] += 1

    print(f"[OK] truck and truck box: добавлено {counts['train']} train, {counts['val']} val")
    return counts["train"], counts["val"]

def process_labelme_file(j_file: Path, dst_img: Path, dst_lbl: Path, dst_base_name: str) -> bool:
    img_file = None
    for ext in [".jpg", ".png", ".jpeg", ".JPG", ".PNG"]:
        candidate = j_file.with_suffix(ext)
        if candidate.exists():
            img_file = candidate
            break
    if not img_file: return False

    try:
        data = json.loads(j_file.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return False

    shapes = data.get("shapes", [])
    if not shapes: return False

    try:
        with Image.open(img_file) as im:
            w, h = im.size
    except Exception:
        return False

    yolo_lines = []
    for s in shapes:
        label = str(s.get("label", "")).lower().strip()
        pts = s.get("points", [])
        if not pts or len(pts) < 2: continue

        xs = [float(p[0]) for p in pts]
        ys = [float(p[1]) for p in pts]
        x1, x2 = max(0.0, min(xs)), min(float(w), max(xs))
        y1, y2 = max(0.0, min(ys)), min(float(h), max(ys))
        if x2 <= x1 or y2 <= y1: continue

        xc = max(0.0, min(1.0, ((x1 + x2) / 2.0) / w))
        yc = max(0.0, min(1.0, ((y1 + y2) / 2.0) / h))
        bw = max(0.0, min(1.0, (x2 - x1) / w))
        bh = max(0.0, min(1.0, (y2 - y1) / h))

        if "plate" in label:
            target_c = 0  # license plate
        else:
            target_c = 1  # car/truck -> truck

        yolo_lines.append(f"{target_c} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

    if not yolo_lines: return False

    # Безопасное копирование файла
    target_img = dst_img / f"{dst_base_name}{img_file.suffix.lower()}"
    target_lbl = dst_lbl / f"{dst_base_name}.txt"
    shutil.copy(img_file, target_img)
    target_lbl.write_text("\n".join(yolo_lines) + "\n", encoding="utf-8")
    return True

def process_data_folder():
    data_dir = WORKSPACE / "data"
    if not data_dir.exists():
        return 0, 0

    train_c, val_c = 0, 0

    # Training
    if (data_dir / "Training").exists():
        for i, jf in enumerate((data_dir / "Training").rglob("*.json")):
            if process_labelme_file(jf, TRAIN_IMG, TRAIN_LBL, f"dtrain_{i:04d}"):
                train_c += 1

    # Validation
    if (data_dir / "Validation").exists():
        for i, jf in enumerate((data_dir / "Validation").rglob("*.json")):
            if process_labelme_file(jf, VAL_IMG, VAL_LBL, f"dval_{i:04d}"):
                val_c += 1

    # Data
    if (data_dir / "Data").exists():
        all_jsons = list((data_dir / "Data").rglob("*.json"))
        split_idx = int(len(all_jsons) * 0.8)
        for i, jf in enumerate(all_jsons):
            dst_i = TRAIN_IMG if i < split_idx else VAL_IMG
            dst_l = TRAIN_LBL if i < split_idx else VAL_LBL
            if process_labelme_file(jf, dst_i, dst_l, f"dextra_{i:04d}"):
                if i < split_idx: train_c += 1
                else: val_c += 1

    print(f"[OK] data folder (LabelMe): добавлено {train_c} train, {val_c} val")
    return train_c, val_c

def process_tractor_detection():
    """
    Tractor Detection.v1i.yolov8 (снимки весовой):
      0: license plate -> 0
      1: tractor       -> 1 (truck)
      2: trailer       -> 2 (trailer)
      3: truck         -> 1 (truck)
    """
    src = WORKSPACE / "Tractor Detection.v1i.yolov8"
    if not src.exists(): return 0, 0
    
    mapping = {0: 0, 1: 1, 2: 2, 3: 1}
    counts = {"train": 0, "val": 0}
    splits = [("train", TRAIN_IMG, TRAIN_LBL), ("valid", VAL_IMG, VAL_LBL), ("test", VAL_IMG, VAL_LBL)]
    idx = 0
    for split_name, dst_img, dst_lbl in splits:
        img_dir = src / split_name / "images"
        lbl_dir = src / split_name / "labels"
        if not img_dir.exists(): continue
        for img_p in img_dir.glob("*.*"):
            lbl_p = lbl_dir / f"{img_p.stem}.txt"
            if not lbl_p.exists(): continue
            new_lines = []
            for line in lbl_p.read_text(encoding="utf-8", errors="ignore").splitlines():
                parts = line.strip().split()
                if not parts: continue
                c = int(parts[0])
                target_c = mapping.get(c, 1)
                new_lines.append(f"{target_c} {' '.join(parts[1:])}")
            if new_lines:
                idx += 1
                name = f"trac_{idx:04d}"
                shutil.copy(img_p, dst_img / f"{name}{img_p.suffix.lower()}")
                (dst_lbl / f"{name}.txt").write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                counts["val" if "val" in split_name or "test" in split_name else "train"] += 1

    print(f"[OK] Tractor Detection (весовая): добавлено {counts['train']} train, {counts['val']} val")
    return counts["train"], counts["val"]

def process_license_plates():
    src = WORKSPACE / "Truck License Plate Detection.v1i.yolov8"
    if not src.exists(): return 0, 0
    counts = {"train": 0, "val": 0}
    splits = [("train", TRAIN_IMG, TRAIN_LBL), ("valid", VAL_IMG, VAL_LBL)]
    idx = 0
    for split_name, dst_img, dst_lbl in splits:
        img_dir = src / split_name / "images"
        lbl_dir = src / split_name / "labels"
        if not img_dir.exists(): continue
        for img_p in img_dir.glob("*.*"):
            lbl_p = lbl_dir / f"{img_p.stem}.txt"
            if not lbl_p.exists(): continue
            new_lines = []
            for line in lbl_p.read_text(encoding="utf-8", errors="ignore").splitlines():
                parts = line.strip().split()
                if not parts: continue
                new_lines.append(f"0 {' '.join(parts[1:])}")
            if new_lines:
                idx += 1
                name = f"lp_{idx:04d}"
                shutil.copy(img_p, dst_img / f"{name}{img_p.suffix.lower()}")
                (dst_lbl / f"{name}.txt").write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                counts["val" if split_name == "valid" else "train"] += 1

    print(f"[OK] License Plate Dataset: добавлено {counts['train']} train, {counts['val']} val")
    return counts["train"], counts["val"]

def create_yaml():
    yaml_path = DATASET_DIR / "data.yaml"
    content = f"""path: {DATASET_DIR.as_posix()}
train: train/images
val: valid/images

nc: 3
names:
  0: license plate
  1: truck
  2: trailer
"""
    yaml_path.write_text(content, encoding="utf-8")
    print(f"[OK] Создан {yaml_path}")

def main():
    print("=" * 60)
    print("Подготовка объединенного датасета в local_model/dataset")
    print("=" * 60)
    setup_dirs()
    process_truck_and_box()
    process_data_folder()
    process_tractor_detection()
    process_license_plates()
    create_yaml()

    total_train = len(list(TRAIN_IMG.glob("*.*")))
    total_val = len(list(VAL_IMG.glob("*.*")))
    print("=" * 60)
    print(f"ИТОГО В ДАТАСЕТЕ:")
    print(f"  Обучающая выборка (train):   {total_train} изображений")
    print(f"  Проверочная выборка (valid): {total_val} изображений")
    print(f"  Всего изображений:           {total_train + total_val}")
    print("=" * 60)

if __name__ == "__main__":
    main()
