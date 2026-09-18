"""
Универсальный скрипт для обработки видео (файл или ссылка на YouTube).
Делает скриншоты при проезде транспорта, находит кузов (truck/trailer) и госномер (license plate),
сохраняет кропы номеров и кузовов, а также JSON-отчёт.

Использование:
  python process_video.py "https://www.youtube.com/watch?v=h-M8QVE5q9o"
  python process_video.py videos/my_video.mp4
  python process_video.py videos/my_video.mp4 --sample-fps 2.0 --conf 0.35
"""
import sys
from pathlib import Path

# Импортируем из локального модуля
local_dir = Path(__file__).parent / "local_model"
sys.path.insert(0, str(local_dir))

from process_video import main

if __name__ == "__main__":
    main()
