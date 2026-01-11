import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "theme": "rainbow"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
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
