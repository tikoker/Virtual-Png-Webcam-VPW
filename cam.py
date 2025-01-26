import json
import sounddevice as sd
import numpy as np
from PIL import Image
import threading
import pyvirtualcam
import random

# Загружаем конфигурацию из файла
def load_config(file_path="config.json"):
    with open(file_path, "r") as f:
        return json.load(f)

# List of images
frames_data = [
    {"path": "image1.gif", "threshold": None},
    {"path": "image2.png", "threshold": 2},
    {"path": "image4.png", "threshold": 3},
    {"path": "image5.png", "threshold": 6}
]
original_images = [Image.open(frame["path"]).convert("RGBA") for frame in frames_data]

# Variables to store the current frame and GIF status
current_frame = 0
is_gif_active = True
frame_lock = threading.Lock()

# Preloading images
original_images = []
for frame in frames_data:
    img = Image.open(frame["path"]).convert("RGBA")
    original_images.append(img)

# Применение настроек из конфигурационного файла
config = load_config()

# Loading the eyes image (eyes.png)
eyes_image = Image.open("eyes.png").convert("RGBA")

# Цвет фона (по умолчанию зеленый, если значение некорректное)
use_green_background = config.get("background_color", "green") == "green"

# Цвет кастомного фона RGBA (используется только если определён)
custom_background_rgba = config.get("custom_background_rgba", None)

# Создание стандартных фонов
green_background = Image.new("RGBA", original_images[0].size, (0, 255, 0, 255))
gray_background = Image.new("RGBA", original_images[0].size, (30, 31, 34, 255))

# Выбор фона на основе настроек
if custom_background_rgba:
    custom_background = Image.new("RGBA", original_images[0].size, tuple(custom_background_rgba))
else:
    custom_background = None

# Audio frame processing function
def audio_callback(indata, frames, time, status):
    if status:
        print(status, flush=True)

    with frame_lock:
        global current_frame, is_gif_active
        current_frame = 0  # The GIF index is always 0

        # Find the index of the image with the highest threshold that exceeds the volume
        for i, frame in enumerate(frames_data[1:], start=1):  # Start from 1 because 0 is the GIF
            if frame["threshold"] is not None and np.linalg.norm(indata) * 10 > frame["threshold"]:
                current_frame = i
                is_gif_active = False  # If another image is activated, the GIF becomes inactive
        else:
            is_gif_active = True  # Otherwise, the GIF remains active

# Setting audio parameters
sd.default.samplerate = config.get("samplerate", 44100)

# Starting the audio stream
stream = sd.InputStream(callback=audio_callback)
stream.start()

# Parameters for eye disappearance
min_disappear_time = 1  # Minimum time (in seconds) for which the eyes disappear
max_disappear_time = 3  # Maximum time (in seconds) for which the eyes disappear
disappear_count_per_minute = 3  # Number of times the eyes disappear per minute

# Flags and timer for managing eye disappearance
eyes_visible = True
next_disappear_time = random.randint(0, 60 // disappear_count_per_minute)  # Time until the next disappearance
disappear_duration = random.uniform(min_disappear_time, max_disappear_time)  # Duration of disappearance
time_since_last_disappear = 0  # Timer to control disappearances

# Function to send images to the virtual webcam
def send_to_virtual_cam(images):
    global eyes_visible, next_disappear_time, disappear_duration, time_since_last_disappear

    with pyvirtualcam.Camera(width=images[0].width, height=images[0].height, fps=30) as cam:
        while True:
            with frame_lock:
                current_frame_data = original_images[current_frame]

            # Выбор базового изображения
            if custom_background:
                base_image = custom_background.copy()
            elif use_green_background:
                base_image = green_background.copy()
            else:
                base_image = gray_background.copy()  # Используем серый фон, если зеленый не выбран

            # Если GIF активен, добавляем его поверх базового изображения
            if is_gif_active:
                base_image = Image.alpha_composite(base_image, original_images[0])

            # Наложение текущего кадра поверх базового изображения
            base_image = Image.alpha_composite(base_image, current_frame_data)

            # Изменение размера изображения глаз
            eyes_resized = eyes_image.resize(base_image.size, Image.Resampling.LANCZOS)

            # Управление видимостью глаз
            time_since_last_disappear += 1 / 30  # Обновление таймера (30 FPS)
            if not eyes_visible:
                if time_since_last_disappear >= disappear_duration:
                    # Глаза появляются
                    eyes_visible = True
                    time_since_last_disappear = 0
                    next_disappear_time = random.randint(60 // disappear_count_per_minute, 60 // disappear_count_per_minute * 2)
                    disappear_duration = random.uniform(min_disappear_time, max_disappear_time)
            else:
                if time_since_last_disappear >= next_disappear_time:
                    # Глаза исчезают
                    eyes_visible = False
                    time_since_last_disappear = 0

            # Наложение глаз на итоговое изображение, если они видимы
            if eyes_visible:
                base_image = Image.alpha_composite(base_image, eyes_resized)

            # Конвертация изображения в RGB для отправки в виртуальную камеру
            frame = np.array(base_image.convert("RGB"))

            # Отправка текущего кадра в виртуальную камеру
            cam.send(frame)
            cam.sleep_until_next_frame()


# Create and start a thread for sending images to the virtual webcam
cam_thread = threading.Thread(target=send_to_virtual_cam, args=(original_images,))
cam_thread.start()

# Wait for the thread to finish
cam_thread.join()

# Stop the audio stream
stream.stop()
stream.close()