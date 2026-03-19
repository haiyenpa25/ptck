import os
import requests
import json

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "telegram_config.json")

def load_telegram_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {"bot_token": "", "chat_id": ""}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"bot_token": "", "chat_id": ""}

def save_telegram_config(config: dict) -> bool:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except:
        return False

def send_alert(message: str):
    """Sends alert to real Telegram API if token is set, else mocks it."""
    config = load_telegram_config()
    token = config.get("bot_token")
    chat_id = config.get("chat_id")
    
    if token and chat_id and token.strip() != "":
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        try:
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code == 200:
                print("📱 Telegram alert sent successfully.")
            else:
                print(f"⚠️ Telegram API Error: {res.text}")
        except Exception as e:
            print(f"⚠️ Failed to send telegram alert: {e}")
    else:
        # Fallback Mock if API not set up
        print(f"Mock Telegram Alert:\n{message}")
