import sys
import os

# Path to the folder with libraries
LIBS_PATH = os.path.join(os.path.dirname(__file__), "libs")

# Add to sys.path (if not already added)
if LIBS_PATH not in sys.path:
    sys.path.insert(0, LIBS_PATH)  # Priority higher than standard paths

import json
import sounddevice as sd
from collections import OrderedDict


def get_unique_microphones():
    """Get unique microphones by name and index"""
    devices = sd.query_devices()
    unique_mics = OrderedDict()

    for device in devices:
        if device['max_input_channels'] > 0:
            name = device['name'].strip()
            # Remove duplicates and empty names
            if name and name not in unique_mics:
                unique_mics[name] = device['index']

    return unique_mics


def select_microphone():
    """Interactive microphone selection"""
    mics = get_unique_microphones()

    if not mics:
        print("No microphones found!")
        return None

    print("\nAvailable microphones:")
    for i, name in enumerate(mics.keys()):
        print(f"{i}: {name}")

    try:
        choice = int(input("\nSelect the microphone number: "))
        selected_name = list(mics.keys())[choice]
        return mics[selected_name]
    except (ValueError, IndexError):
        print("Error: please enter a valid number")
        return None


def save_config(mic_index):
    """Update only the microphone_index parameter in the config"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)  # Load current settings
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}  # If the file does not exist or is empty, create a new dictionary

    config["microphone_index"] = mic_index  # Update only the required parameter

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\nConfiguration saved. Selected microphone with index: {mic_index}")


if __name__ == "__main__":
    print("=== Microphone Selection ===")
    if (mic_index := select_microphone()) is not None:
        save_config(mic_index)
