import sys
import os

# Путь к папке с библиотеками
libs_path = os.path.join(os.path.dirname(__file__), "libs")

# Добавляем в sys.path (если ещё не добавлен)
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)  # Приоритет выше стандартных путей

import json
import sounddevice as sd
import numpy as np
from PIL import Image
import threading
import pyvirtualcam
import random

# Load configuration from the file
def load_config(file_path="config.json"):
    with open(file_path, "r") as f:
        return json.load(f)

# Load configuration
config = load_config()

# Determine the folder based on the "old_Version" setting
base_folder = "oldVersion" if config.get("old_Version", False) else "defaultVersion"

# Load images based on the selected folder
frames_data = [
    {"path": f"{base_folder}/image1.gif", "threshold": None},
    {"path": f"{base_folder}/image2.png", "threshold": 1},
    {"path": f"{base_folder}/image4.png", "threshold": 2},
    {"path": f"{base_folder}/image5.png", "threshold": 3}
]

# Preloading images
try:
    original_images = [Image.open(frame["path"]).convert("RGBA") for frame in frames_data]
except FileNotFoundError as e:
    print(f"Error loading images: {e}")
    exit(1)

# Load eyes image
eyes_path = f"{base_folder}/eyes.png"
try:
    eyes_image = Image.open(eyes_path).convert("RGBA")
except FileNotFoundError:
    print(f"Error: 'eyes.png' not found in {base_folder}. Please ensure the file exists.")
    exit(1)

# Example debug output
print(f"Loaded images from folder: {base_folder}")

# Load configuration
config = load_config()
use_old_version = config.get("old_Version", False)

# Path to the eyes image
eyes_path = f"{base_folder}/eyes.png"

# Loading the eyes image
try:
    eyes_image = Image.open(eyes_path).convert("RGBA")
except FileNotFoundError:
    print(f"Error: 'eyes.png' not found in {base_folder}. Please ensure the file exists.")
    exit(1)

# Background color settings
use_green_background = config.get("background_color", "green") == "green"
custom_background_rgba = config.get("custom_background_rgba", None)

# Create standard backgrounds
green_background = Image.new("RGBA", original_images[0].size, (0, 255, 0, 255))
gray_background = Image.new("RGBA", original_images[0].size, (30, 31, 34, 255))

# Select the custom background if defined
if custom_background_rgba:
    custom_background = Image.new("RGBA", original_images[0].size, tuple(custom_background_rgba))
else:
    custom_background = None

# Variables to store the current frame and GIF status
current_frame = 0
is_gif_active = True
frame_lock = threading.Lock()

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
sd.default.device = config.get("microphone_index", None)  # Use the selected microphone

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

            # Select the base image
            if custom_background:
                base_image = custom_background.copy()
            elif use_green_background:
                base_image = green_background.copy()
            else:
                base_image = gray_background.copy()  # Use gray background if green is not selected

            # Overlay the GIF if active
            if is_gif_active:
                base_image = Image.alpha_composite(base_image, original_images[0])

            # Overlay the current frame on top of the base image
            base_image = Image.alpha_composite(base_image, current_frame_data)

            # Resize the eyes image to match the base image
            eyes_resized = eyes_image.resize(base_image.size, Image.Resampling.LANCZOS)

            # Manage the visibility of the eyes
            time_since_last_disappear += 1 / 30  # Update the timer (30 FPS)
            if not eyes_visible:
                if time_since_last_disappear >= disappear_duration:
                    # Eyes reappear
                    eyes_visible = True
                    time_since_last_disappear = 0
                    next_disappear_time = random.randint(60 // disappear_count_per_minute, 60 // disappear_count_per_minute * 2)
                    disappear_duration = random.uniform(min_disappear_time, max_disappear_time)
            else:
                if time_since_last_disappear >= next_disappear_time:
                    # Eyes disappear
                    eyes_visible = False
                    time_since_last_disappear = 0

            # Overlay the eyes on the final image if visible
            if eyes_visible:
                base_image = Image.alpha_composite(base_image, eyes_resized)

            # Convert the image to RGB for the virtual camera
            frame = np.array(base_image.convert("RGB"))

            # Send the current frame to the virtual camera
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