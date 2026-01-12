import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "theme": "rainbow",
    "show_streak": True,
    "show_heatmap": True,
    "simplicity": False,
    "category_colors": {}
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure default values for missing keys
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except IOError:
        pass

def get_theme():
    config = load_config()
    return config.get("theme", "rainbow")

def get_show_streak():
    config = load_config()
    return config.get("show_streak", True)

def get_show_heatmap():
    config = load_config()
    return config.get("show_heatmap", True)

def get_simplicity():
    config = load_config()
    return config.get("simplicity", False)

def get_category_colors():
    config = load_config()
    return config.get("category_colors", {})

def update_category_color(category: str, color: str):
    config = load_config()
    if "category_colors" not in config:
        config["category_colors"] = {}
    config["category_colors"][category] = color
    save_config(config)
