import json
import sounddevice as sd


def list_microphones():
    """Function to list available microphones."""
    devices = sd.query_devices()
    input_devices = [device for device in devices if device['max_input_channels'] > 0]

    # Remove duplicates by device name
    unique_devices = []
    seen_names = set()
    for device in input_devices:
        if device['name'] not in seen_names:
            seen_names.add(device['name'])
            unique_devices.append(device)

    print("Available microphones:")
    for i, device in enumerate(unique_devices):
        print(f"{i}: {device['name']}")


def select_microphone():
    """Function to select the default microphone."""
    list_microphones()
    try:
        choice = int(input("Select microphone number: "))
    except ValueError:
        print("Error: please enter a number.")
        return None

    devices = sd.query_devices()
    input_devices = [device for device in devices if device['max_input_channels'] > 0]

    # Remove duplicates by device name
    unique_devices = []
    seen_names = set()
    for device in input_devices:
        if device['name'] not in seen_names:
            seen_names.add(device['name'])
            unique_devices.append(device)

    if 0 <= choice < len(unique_devices):
        selected_device = unique_devices[choice]
        print(f"Selected microphone: {selected_device['name']}")
        return selected_device['index']
    else:
        print("Invalid choice. Please select a number from the list.")
        return None


def update_config(microphone_index):
    """Function to update the configuration file with the selected microphone."""
    config_file = "config.json"

    try:
        with open(config_file, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    config["microphone_index"] = microphone_index

    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)

    print(f"Configuration file updated (index: {microphone_index}).")


if __name__ == "__main__":
    microphone_index = select_microphone()
    if microphone_index is not None:
        update_config(microphone_index)
