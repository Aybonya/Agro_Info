"""Главный скрипт: детекция техники, распознавание номера, определение типа и марки.

Запуск:
    python src/pipeline.py

Результат:
    results/results.json, results/results.csv — данные по каждому фото
    results/annotated/*.jpg — все обработанные кадры с отмеченными объектами
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DATA_DIR, RESULTS_DIR, ANNOTATED_DIR, PLATES_DIR  # noqa: E402
from detect import detect_vehicles  # noqa: E402
from plate import find_plate, read_text_tokens  # noqa: E402
from classify import classify_vehicle  # noqa: E402

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

# cv2.putText не умеет рисовать кириллицу (выводит "?????"), поэтому весь текст
# на аннотированных кадрах рисуется через PIL шрифтом с поддержкой юникода
_FONT_CANDIDATES = ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf",
                     "C:/Windows/Fonts/tahoma.ttf"]
_font_cache: dict[int, ImageFont.FreeTypeFont] = {}


def _get_font(size: int):
    if size not in _font_cache:
        path = next((p for p in _FONT_CANDIDATES if Path(p).exists()), None)
        _font_cache[size] = ImageFont.truetype(path, size) if path else ImageFont.load_default()
    return _font_cache[size]


def _put_label(image, text, org, color, font_size=26, bg=(0, 0, 0)):
    """Текст (в т.ч. кириллица) на закрашенной подложке — читаемо на любом фоне."""
    font = _get_font(font_size)
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    x, y = org
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    tw, th = r - l, b - t
    draw.rectangle((x - 4, y - th - 8, x + tw + 4, y + 6), fill=(bg[2], bg[1], bg[0]))
    draw.text((x, y - th - t - 2), text, font=font, fill=(color[2], color[1], color[0]))
    image[:] = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _draw_text(image, text, org, color, font_size=26):
    """Текст (в т.ч. кириллица) без подложки — поверх уже нарисованного фона."""
    font = _get_font(font_size)
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    x, y = org
    _, t, _, b = draw.textbbox((0, 0), text, font=font)
    draw.text((x, y - (b - t) - t), text, font=font, fill=(color[2], color[1], color[0]))
    image[:] = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def draw_annotation(image, vehicle_bbox, plate_result, classify_result, vehicle_id=1):
    GREEN = (60, 220, 60)
    YELLOW = (0, 210, 255)
    x1, y1, x2, y2 = [int(v) for v in vehicle_bbox]

    # --- рамка техники ---
    cv2.rectangle(image, (x1, y1), (x2, y2), GREEN, 3)
    veh_label = f"ID:{vehicle_id} {classify_result.vehicle_type_ru}"
    if classify_result.manufacturer:
        veh_label += f" ({classify_result.manufacturer})"
    _put_label(image, veh_label, (x1 + 4, y1 - 8 if y1 > 30 else y1 + 28), GREEN)

    plate_crop = None
    if plate_result.bbox is not None:
        px1, py1, px2, py2 = [int(v) for v in plate_result.bbox]
        cv2.rectangle(image, (px1, py1), (px2, py2), YELLOW, 3)
        _put_label(image, plate_result.text or "?", (px1, py2 + 28), YELLOW)
        plate_crop = image[max(0, py1):py2, max(0, px1):px2].copy()

    # --- информационная панель в правом верхнем углу (как у LPR-референса) ---
    panel_w = 320
    panel_h = 260
    px, py = image.shape[1] - panel_w - 20, 20
    overlay = image.copy()
    cv2.rectangle(overlay, (px, py), (px + panel_w, py + panel_h), (25, 25, 25), -1)
    image[:] = cv2.addWeighted(overlay, 0.85, image, 0.15, 0)
    cv2.rectangle(image, (px, py), (px + panel_w, py + panel_h), YELLOW, 2)
    cv2.putText(image, "Plate", (px + 12, py + 32), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (255, 255, 255), 2, cv2.LINE_AA)

    if plate_crop is not None and plate_crop.size > 0:
        target_w = panel_w - 24
        scale = target_w / plate_crop.shape[1]
        target_h = max(1, int(plate_crop.shape[0] * scale))
        target_h = min(target_h, 90)
        thumb = cv2.resize(plate_crop, (target_w, target_h))
        image[py + 44:py + 44 + target_h, px + 12:px + 12 + target_w] = thumb
        text_y = py + 44 + target_h + 40
    else:
        text_y = py + 100

    plate_text = plate_result.text or "не распознан"
    _draw_text(image, plate_text, (px + 12, text_y + 8), YELLOW, font_size=28)
    if plate_result.text:
        cv2.putText(image, f"{plate_result.confidence * 100:.0f}%", (px + 12, text_y + 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1, cv2.LINE_AA)

    _draw_text(image, f"Type: {classify_result.vehicle_type_ru}",
               (px + 12, py + panel_h - 38), (255, 255, 255), font_size=18)
    mf_text = f"Brand: {classify_result.manufacturer or '?'}"
    cv2.putText(image, mf_text, (px + 12, py + panel_h - 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    return image


def save_plate_crop(image, plate_bbox, plate_text, source_name: str) -> str | None:
    """Вырезает чистую область номера (без рамок/подписей) и сохраняет в PLATES_DIR."""
    h, w = image.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in plate_bbox]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    stem = Path(source_name).stem
    safe_text = plate_text if plate_text else "unknown"
    out_path = PLATES_DIR / f"{safe_text}_{stem}.jpg"
    cv2.imwrite(str(out_path), crop)
    return out_path.name


def process_image(path: Path) -> dict:
    image = cv2.imread(str(path))
    record = {
        "file": path.name,
        "vehicle_found": False,
        "vehicle_type": None,
        "vehicle_type_ru": None,
        "type_confidence": None,
        "manufacturer": None,
        "manufacturer_confidence": None,
        "manufacturer_source": None,
        "plate_number": None,
        "plate_confidence": None,
        "plate_crop_file": None,
        "bbox": None,
    }

    if image is None:
        record["error"] = "cannot read image"
        return record, None

    detections = detect_vehicles(str(path))
    if not detections:
        return record, image

    main = detections[0]
    record["vehicle_found"] = True
    record["bbox"] = [round(v, 1) for v in main.bbox]

    plate_result = find_plate(image, main.bbox)
    ocr_tokens = read_text_tokens(image, main.bbox)
    cls_result = classify_vehicle(image, main.bbox, ocr_tokens)

    plate_crop_file = None
    if plate_result.bbox is not None:
        plate_crop_file = save_plate_crop(image, plate_result.bbox, plate_result.text, path.name)

    record.update({
        "vehicle_type": cls_result.vehicle_type,
        "vehicle_type_ru": cls_result.vehicle_type_ru,
        "type_confidence": round(cls_result.type_confidence, 3),
        "manufacturer": cls_result.manufacturer,
        "manufacturer_confidence": round(cls_result.manufacturer_confidence, 3),
        "manufacturer_source": cls_result.manufacturer_source,
        "plate_number": plate_result.text,
        "plate_confidence": round(plate_result.confidence, 3) if plate_result.text else None,
        "plate_crop_file": plate_crop_file,
    })

    annotated = draw_annotation(image.copy(), main.bbox, plate_result, cls_result)
    return record, annotated


def parse_args():
    parser = argparse.ArgumentParser(
        description="Детекция техники, номеров, типа и производителя по фото.")
    parser.add_argument(
        "images", nargs="*",
        help="Конкретные файлы для обработки (имя файла из --dir или полный путь). "
             "Если не указаны — обрабатываются все фото из --dir.")
    parser.add_argument(
        "--dir", "-d", type=Path, default=DATA_DIR,
        help=f"Папка с фото (по умолчанию {DATA_DIR}).")
    return parser.parse_args()


def resolve_image_paths(args) -> list[Path]:
    """Список файлов для обработки: указанные явно (с проверкой, что существуют
    и являются изображениями) или все фото из --dir, если ничего не указано."""
    if not args.images:
        return sorted(
            [p for p in args.dir.iterdir() if p.suffix.lower() in IMAGE_EXTS],
            key=lambda p: (len(p.stem), p.stem),
        )

    paths = []
    for name in args.images:
        path = Path(name)
        if not path.exists():
            path = args.dir / name
        if not path.exists():
            print(f"Файл не найден: {name}")
            continue
        if path.suffix.lower() not in IMAGE_EXTS:
            print(f"Пропущен (не изображение): {path}")
            continue
        paths.append(path)
    return paths


def load_existing_records() -> dict:
    """Ранее сохранённые результаты (file -> record), чтобы при обработке
    отдельных файлов не терять данные по остальным фото из прошлого запуска."""
    json_path = RESULTS_DIR / "results.json"
    if not json_path.exists():
        return {}
    with open(json_path, encoding="utf-8") as f:
        return {r["file"]: r for r in json.load(f)}


def main():
    args = parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
    PLATES_DIR.mkdir(parents=True, exist_ok=True)

    image_paths = resolve_image_paths(args)
    if not image_paths:
        print(f"Нет изображений для обработки в {args.dir}")
        return

    # при обработке конкретных файлов (не всей папки целиком) сохраняем
    # результаты по остальным ранее обработанным фото, а не стираем их
    is_partial_run = bool(args.images)
    records_by_file = load_existing_records() if is_partial_run else {}

    for i, path in enumerate(image_paths, 1):
        print(f"[{i}/{len(image_paths)}] {path.name} ...", flush=True)
        record, annotated = process_image(path)
        records_by_file[record["file"]] = record
        if annotated is not None:
            out_path = ANNOTATED_DIR / f"annotated_{path.name}"
            cv2.imwrite(str(out_path), annotated)

    records = sorted(records_by_file.values(), key=lambda r: (len(r["file"]), r["file"]))

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "results.csv", index=False, encoding="utf-8-sig")
    with open(RESULTS_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    found = sum(r["vehicle_found"] for r in records)
    plates = sum(1 for r in records if r["plate_number"])
    plate_crops = sum(1 for r in records if r["plate_crop_file"])
    print(f"\nГотово: обработано {len(image_paths)} фото "
          f"(всего в результатах {len(records)}), техника найдена на {found}, "
          f"номер распознан на {plates}.")
    print(f"Результаты: {RESULTS_DIR / 'results.json'}, {RESULTS_DIR / 'results.csv'}")
    print(f"Размеченные примеры: {ANNOTATED_DIR}")
    print(f"Кропы номеров ({plate_crops} шт.): {PLATES_DIR}")


if __name__ == "__main__":
    main()
