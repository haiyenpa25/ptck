import json
import os

APP_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "app_settings.json")

def load_app_settings() -> dict:
    if not os.path.exists(APP_SETTINGS_PATH):
        return {"resolution": "1D"}
    try:
        with open(APP_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except: 
        return {"resolution": "1D"}

def save_app_settings(settings: dict) -> bool:
    try:
        with open(APP_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        return True
    except: 
        return False
