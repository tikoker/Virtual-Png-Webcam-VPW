import json
import os

def load_config():
    with open("config.json", "r") as file:
        return json.load(file)

def save_config(config):
    with open("config.json", "w") as file:
        json.dump(config, file, indent=4)

def run_default_microphone():
    os.system("python default_microphone.py")

def change_dispenser_version(config):
    print("\n  - 1.oldVersion\n  - 2.defaultVersion\n")
    choice = input("Select version (1/2): ")
    config["old_Version"] = choice == "1"
    save_config(config)

def change_background_color(config):
    print("\n - 1.gray\n - 2.green\n")
    choice = input("Select color (1/2): ")
    config["background_color"] = "gray" if choice == "1" else "green"
    save_config(config)

def change_custom_background_rgba(config):
    print("\n - Enter the RGBA or RGB color (separated by a space)")
    print(f"Current color: {config['custom_background_rgba']}")
    color_input = input("Enter new color or leave empty to reset: ")
    if color_input:
        new_values = list(map(int, color_input.split()))
        config["custom_background_rgba"] = new_values
    else:
        config["custom_background_rgba"] = []
    save_config(config)

def main():
    while True:
        config = load_config()
        print("\nSettings Menu:")
        print("1) Default Microphone")
        print("2) Dispenser Version")
        print("3) Background Color")
        print("4) Custom Background RGBA")
        print("5) Exit")
        choice = input("Select an option: ")

        if choice == "1":
            run_default_microphone()
        elif choice == "2":
            change_dispenser_version(config)
        elif choice == "3":
            change_background_color(config)
        elif choice == "4":
            change_custom_background_rgba(config)
        elif choice == "5":
            break
        else:
            print("Invalid option, please try again.")

if __name__ == "__main__":
    main()
