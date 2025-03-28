import sys
import os
# Путь к папке с библиотеками
LIBS_PATH = os.path.join(os.path.dirname(__file__), "libs")

# Добавляем в sys.path (если ещё не добавлен)
if LIBS_PATH not in sys.path:
    sys.path.insert(0, LIBS_PATH)  # Приоритет выше стандартных путей

import json
import sounddevice as sd
from collections import OrderedDict


def get_unique_microphones():
    """Получаем уникальные микрофоны по имени и индексу"""
    devices = sd.query_devices()
    unique_mics = OrderedDict()

    for device in devices:
        if device['max_input_channels'] > 0:
            name = device['name'].strip()
            # Убираем дубликаты и пустые имена
            if name and name not in unique_mics:
                unique_mics[name] = device['index']

    return unique_mics


def select_microphone():
    """Интерактивный выбор микрофона"""
    mics = get_unique_microphones()

    if not mics:
        print("Микрофоны не найдены!")
        return None

    print("\nДоступные микрофоны:")
    for i, name in enumerate(mics.keys()):
        print(f"{i}: {name}")

    try:
        choice = int(input("\nВыберите номер микрофона: "))
        selected_name = list(mics.keys())[choice]
        return mics[selected_name]
    except (ValueError, IndexError):
        print("Ошибка: введите корректный номер")
        return None


def save_config(mic_index):
    """Обновляем только параметр microphone_index в конфиге"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)  # Загружаем текущие настройки
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}  # Если файла нет или он пустой, создаем новый словарь

    config["microphone_index"] = mic_index  # Обновляем только нужный параметр

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\nКонфигурация сохранена. Выбран микрофон с индексом: {mic_index}")


if __name__ == "__main__":
    print("=== Выбор микрофона ===")
    if (mic_index := select_microphone()) is not None:
        save_config(mic_index)