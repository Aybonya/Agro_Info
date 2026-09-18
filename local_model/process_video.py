"""
Умная система фиксации проездов транспорта через весовую / КПП.
Логика оптимизации:
1. Фильтр миганий (min_duration_sec >= 1.5s): одиночные случайные кадры отбрасываются.
2. Фильтр по госномеру (require_plate): сохраняются только реальные проезды с читаемым номером.
3. Формат "1 проезд = 1 карточка ТС":
   - vehicle_card.jpg: единое фото высокой четкости с врезкой номера (Picture-in-Picture) и инфо-плашкой.
   - license_plate.jpg: чистый кроп номера для систем OCR/1C.
   - info.json: метаданные проезда.
4. Автоудаление и очистка мусора.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

CLASS_COLORS = {
    "license plate": (0, 215, 255),  # Золотистый
    "truck": (255, 140, 0),          # Синий
    "trailer": (180, 105, 255),      # Фиолетовый
    "tractor": (50, 205, 50),        # Зеленый
}

TRUCK_CLASSES = {"truck", "trailer", "tractor", "car", "box"}
PLATE_CLASSES = {"license plate", "plate", "number plate"}

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    return f"{minutes:02d}:{secs:06.3f}"

def format_time_code(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}m_{secs:02d}s"

def is_youtube_url(url: str) -> bool:
    return bool(re.search(r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)", url))

def get_youtube_video_id(url: str) -> str:
    m = re.search(r"(?:v=|\/|shorts\/)([0-9A-Za-z_-]{11})", url)
    if m:
        return m.group(1)
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()[:12]

def download_youtube_video(url: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    vid_id = get_youtube_video_id(url)
    target_path = output_dir / f"yt_{vid_id}.mp4"
    if target_path.exists() and target_path.stat().st_size > 1024*1024:
        print(f"\n[YOUTUBE] Используется ранее загруженное видео ({vid_id}): {target_path}")
        return target_path

    print(f"\n[YOUTUBE] Скачивание видео с YouTube ({vid_id}) через yt-dlp...")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "136/134/best[ext=mp4]/best",
        "-o", str(target_path),
        "--force-overwrites",
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError(f"Ошибка загрузки YouTube: {res.stderr}")
    return target_path

def clamp_crop(image: np.ndarray, xyxy: list[int | float], padding: float = 0.12):
    h, w = image.shape[:2]
    x1, y1, x2, y2 = map(float, xyxy)
    pad_x = (x2 - x1) * padding
    pad_y = (y2 - y1) * padding
    left = max(0, int(x1 - pad_x))
    top = max(0, int(y1 - pad_y))
    right = min(w, int(x2 + pad_x))
    bottom = min(h, int(y2 + pad_y))
    return image[top:bottom, left:right], [left, top, right, bottom]

def make_composite_card(
    overview_img: np.ndarray,
    plate_crop: np.ndarray | None,
    vehicle_id: int,
    start_time_str: str,
    end_time_str: str,
    plate_conf: float | None,
    truck_conf: float | None,
    truck_class: str = "truck",
) -> np.ndarray:
    """
    Создает единую компактную карточку проезда:
    - Общий кадр ТС
    - Врезка увеличенного номера в верхнем правом углу
    - Нижняя плашка со статусом проезда и уверенностью
    """
    card = overview_img.copy()
    h, w = card.shape[:2]

    # 1. Врезка госномера (Picture-in-Picture)
    if plate_crop is not None and plate_crop.size > 0:
        ph, pw = plate_crop.shape[:2]
        inset_w = max(260, int(w * 0.24))
        inset_h = max(70, int(inset_w * (ph / max(1, pw))))
        inset_h = min(inset_h, int(h * 0.28))
        resized_plate = cv2.resize(plate_crop, (inset_w, inset_h), interpolation=cv2.INTER_LANCZOS4)

        margin = 16
        x2 = w - margin
        x1 = x2 - inset_w
        y1 = margin + 25
        y2 = y1 + inset_h

        # Темная подложка и золотая рамка
        cv2.rectangle(card, (x1 - 4, y1 - 4), (x2 + 4, y2 + 4), (20, 20, 20), -1)
        cv2.rectangle(card, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), (0, 215, 255), 2)
        card[y1:y2, x1:x2] = resized_plate

        badge_text = f"LICENSE PLATE: {plate_conf*100:.1f}%" if plate_conf else "LICENSE PLATE"
        cv2.putText(card, badge_text, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2, cv2.LINE_AA)

    # 2. Нижняя статусная плашка
    banner_h = 44
    cv2.rectangle(card, (0, h - banner_h), (w, h), (18, 18, 18), -1)
    cv2.line(card, (0, h - banner_h), (w, h - banner_h), (0, 215, 255), 2)

    time_str = f"VEHICLE #{vehicle_id:02d} | TIME: {start_time_str} - {end_time_str}"
    body_str = f" | BODY: {truck_class.upper()} ({truck_conf*100:.0f}%)" if truck_conf else ""
    plate_str = f" | PLATE: {plate_conf*100:.1f}%" if plate_conf else ""
    status_line = f"{time_str}{body_str}{plate_str}"

    cv2.putText(card, status_line, (16, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    return card

class SmartPassageSession:
    def __init__(self, session_id: int, start_time_sec: float, start_frame: int):
        self.session_id = session_id
        self.start_time_sec = start_time_sec
        self.last_seen_sec = start_time_sec
        self.start_frame = start_frame
        self.last_frame = start_frame
        self.detections_count = 0

        self.best_plate = None
        self.best_body = None
        self.best_overview_frame = None
        self.best_overview_score = 0.0

        self.has_truck = False
        self.has_plate = False

    def update(self, frame: np.ndarray, detections: list[dict], current_time_sec: float, frame_idx: int):
        self.last_seen_sec = current_time_sec
        self.last_frame = frame_idx
        self.detections_count += 1

        plates = [d for d in detections if d["class"] in PLATE_CLASSES]
        trucks = [d for d in detections if d["class"] in TRUCK_CLASSES]

        if plates:
            self.has_plate = True
            for p in plates:
                score = p["confidence"]
                if self.best_plate is None or score > self.best_plate["score"]:
                    crop, crop_bbox = clamp_crop(frame, p["bbox"], padding=0.15)
                    if crop.size > 0:
                        self.best_plate = {
                            "score": score,
                            "crop": crop.copy(),
                            "bbox": p["bbox"],
                            "time_sec": current_time_sec,
                        }

        if trucks:
            self.has_truck = True
            for t in trucks:
                score = t["confidence"]
                if self.best_body is None or score > self.best_body["score"]:
                    crop, crop_bbox = clamp_crop(frame, t["bbox"], padding=0.04)
                    if crop.size > 0:
                        self.best_body = {
                            "score": score,
                            "crop": crop.copy(),
                            "bbox": t["bbox"],
                            "time_sec": current_time_sec,
                            "class": t["class"],
                        }

        # Выбираем лучший общий кадр (где и номер, и машина видны максимально четко)
        score = 0.0
        if plates and trucks:
            score = 2.0 + max(p["confidence"] for p in plates) + max(t["confidence"] for t in trucks)
        elif plates:
            score = 1.0 + max(p["confidence"] for p in plates)
        elif trucks:
            score = max(t["confidence"] for t in trucks)

        if score > self.best_overview_score or self.best_overview_frame is None:
            self.best_overview_score = score
            self.best_overview_frame = frame.copy()

    @property
    def duration_sec(self) -> float:
        return max(0.0, self.last_seen_sec - self.start_time_sec)

    def is_valid_passage(self, min_duration: float = 1.5, require_plate: bool = True) -> bool:
        # 1. Отсеиваем мигания длительностью меньше min_duration
        if self.duration_sec < min_duration and self.detections_count < 2:
            return False

        # 2. Если требуется номер — отсеиваем машины без распознанного номера
        if require_plate and not self.has_plate:
            return False

        return self.has_plate or self.has_truck

    def finalize_and_save(self, output_events_dir: Path) -> dict | None:
        if not self.is_valid_passage():
            return None

        time_tag = format_time_code(self.start_time_sec)
        event_folder = output_events_dir / f"vehicle_{self.session_id:02d}_{time_tag}"
        event_folder.mkdir(parents=True, exist_ok=True)

        start_str = format_timestamp(self.start_time_sec)
        end_str = format_timestamp(self.last_seen_sec)
        plate_conf = self.best_plate["score"] if self.best_plate else None
        truck_conf = self.best_body["score"] if self.best_body else None
        truck_cls = self.best_body["class"] if self.best_body else "truck"

        # Создаем единую композитную карточку
        plate_crop = self.best_plate["crop"] if self.best_plate else None
        overview_frame = self.best_overview_frame if self.best_overview_frame is not None else np.zeros((720, 1280, 3), dtype=np.uint8)

        card_img = make_composite_card(
            overview_img=overview_frame,
            plate_crop=plate_crop,
            vehicle_id=self.session_id,
            start_time_str=start_str,
            end_time_str=end_str,
            plate_conf=plate_conf,
            truck_conf=truck_conf,
            truck_class=truck_cls,
        )

        # Сохраняем ТОЛЬКО 2 файла: карточку проезда и чистый кроп номера (для OCR/1C)
        card_file = event_folder / "vehicle_card.jpg"
        cv2.imwrite(str(card_file), card_img, [cv2.IMWRITE_JPEG_QUALITY, 95])

        saved_files = {"card": card_file.name}

        if plate_crop is not None:
            plate_file = event_folder / "license_plate.jpg"
            cv2.imwrite(str(plate_file), plate_crop, [cv2.IMWRITE_JPEG_QUALITY, 98])
            saved_files["license_plate"] = plate_file.name

        record = {
            "vehicle_id": self.session_id,
            "folder": str(event_folder.name),
            "start_time": start_str,
            "end_time": end_str,
            "duration_sec": round(self.duration_sec, 2),
            "plate_confidence": round(plate_conf, 3) if plate_conf else None,
            "truck_confidence": round(truck_conf, 3) if truck_conf else None,
            "saved_photos": saved_files,
        }

        with open(event_folder / "info.json", "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        return record

def process_video_optimized(
    source: str,
    weights_path: Path,
    output_dir: Path,
    conf_thresh: float = 0.30,
    sample_fps: float = 1.5,
    cooldown_sec: float = 8.0,
    min_duration_sec: float = 1.5,
    require_plate: bool = True,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    events_dir = output_dir / "vehicle_events"
    events_dir.mkdir(parents=True, exist_ok=True)

    if is_youtube_url(source):
        cache_dir = output_dir / "download_cache"
        video_path = download_youtube_video(source, cache_dir)
    else:
        video_path = Path(source)

    print(f"[МОДЕЛЬ] Загрузка YOLO11: {weights_path}")
    model = YOLO(str(weights_path))

    cap = cv2.VideoCapture(str(video_path))
    orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_frames / orig_fps

    print(f"\n[ПАРАМЕТРЫ] Видео: {video_w}x{video_h}, Длина: {format_timestamp(duration_sec)}")
    print(f"[ФИЛЬТРЫ]  Мин. длительность: {min_duration_sec}с (защита от миганий)")
    print(f"           Требовать номер:   {'Да' if require_plate else 'Нет'}")
    print(f"           Формат:            1 проезд = 1 карточка ТС + кроп номера\n")

    frame_step = max(1, int(round(orig_fps / sample_fps)))
    frame_idx = 0
    vehicle_counter = 0
    current_session: SmartPassageSession | None = None
    saved_passages = []

    start_scan_time = time.time()

    while cap.isOpened():
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        current_time_sec = frame_idx / orig_fps

        res = model.predict(frame, conf=conf_thresh, verbose=False)[0]

        detections = []
        for box in res.boxes:
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id].lower()
            conf = float(box.conf[0])
            xyxy = [int(v) for v in box.xyxy[0].tolist()]

            if cls_name in ["number plate", "plate"]:
                cls_name = "license plate"
            elif cls_name in ["car"]:
                cls_name = "truck"
            elif cls_name in ["box"]:
                cls_name = "trailer"

            detections.append({
                "class": cls_name,
                "confidence": round(conf, 3),
                "bbox": xyxy
            })

        has_interest = any(d["class"] in TRUCK_CLASSES or d["class"] in PLATE_CLASSES for d in detections)

        if has_interest:
            if current_session is None:
                vehicle_counter += 1
                current_session = SmartPassageSession(vehicle_counter, current_time_sec, frame_idx)
                print(f"[{format_timestamp(current_time_sec)}] Авто #{vehicle_counter} заезжает...")

            current_session.update(frame, detections, current_time_sec, frame_idx)
        else:
            if current_session is not None:
                idle_time = current_time_sec - current_session.last_seen_sec
                if idle_time >= cooldown_sec:
                    if current_session.is_valid_passage(min_duration=min_duration_sec, require_plate=require_plate):
                        result = current_session.finalize_and_save(events_dir)
                        if result:
                            saved_passages.append(result)
                            print(f"\n[ЗАФИКСИРОВАН ПРОЕЗД] Авто #{current_session.session_id}")
                            print(f"  Время:        {result['start_time']} -> {result['end_time']} ({result['duration_sec']}с)")
                            print(f"  Госномер:     {result['plate_confidence']*100:.1f}%" if result['plate_confidence'] else "  Госномер:     не зафиксирован")
                            print(f"  Карточка:     {events_dir / result['folder'] / 'vehicle_card.jpg'}\n")
                    else:
                        print(f"[{format_timestamp(current_time_sec)}] [ОТБРОШЕНО] Сессия #{current_session.session_id}: длительность {current_session.duration_sec:.1f}с или нет номера.")
                    current_session = None

        frame_idx += frame_step

    if current_session is not None:
        if current_session.is_valid_passage(min_duration=min_duration_sec, require_plate=require_plate):
            result = current_session.finalize_and_save(events_dir)
            if result:
                saved_passages.append(result)
                print(f"\n[ЗАФИКСИРОВАН ПРОЕЗД] Авто #{current_session.session_id}")
                print(f"  Карточка: {events_dir / result['folder'] / 'vehicle_card.jpg'}")
        else:
            print(f"[ОТБРОШЕНО] Последняя сессия не прошла по критериям.")

    cap.release()
    elapsed = time.time() - start_scan_time

    registry_file = output_dir / "passage_registry.json"
    with open(registry_file, "w", encoding="utf-8") as f:
        json.dump({
            "source": source,
            "total_vehicles_registered": len(saved_passages),
            "processing_time_sec": round(elapsed, 2),
            "vehicles": saved_passages
        }, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print(f"[ИТОГ] Анализ завершен за {elapsed:.1f} сек! Подтверждено реальных ТС: {len(saved_passages)} шт.")
    print(f"  Папка с карточками: {events_dir}")
    print(f"  Журнал:             {registry_file}")
    print("=" * 65 + "\n")

    return registry_file

def main():
    parser = argparse.ArgumentParser(description="Оптимизированная детекция проезда ТС (1 проезд = 1 карточка)")
    parser.add_argument("source", nargs="?", default="../videos/yt_NL0CO28eq9Q.mp4")
    parser.add_argument("--weights", default="weights/truck_plate_yolo11n.pt")
    parser.add_argument("--output", default="output/smart_events")
    parser.add_argument("--sample-fps", type=float, default=1.5)
    parser.add_argument("--conf", type=float, default=0.30)
    parser.add_argument("--cooldown", type=float, default=8.0)
    parser.add_argument("--min-duration", type=float, default=1.5, help="Минимальная длительность проезда (с)")
    parser.add_argument("--all-vehicles", action="store_true", default=False, help="Сохранять даже без номера")
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    source = args.source
    if not is_youtube_url(source):
        src_path = Path(source)
        if not src_path.is_absolute():
            src_path = (script_dir / src_path).resolve()
        source = str(src_path)

    weights_path = Path(args.weights)
    if not weights_path.is_absolute():
        weights_path = (script_dir / weights_path).resolve()

    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = (script_dir / output_dir).resolve()

    process_video_optimized(
        source=source,
        weights_path=weights_path,
        output_dir=output_dir,
        conf_thresh=args.conf,
        sample_fps=args.sample_fps,
        cooldown_sec=args.cooldown,
        min_duration_sec=args.min_duration,
        require_plate=not args.all_vehicles,
    )

if __name__ == "__main__":
    main()
