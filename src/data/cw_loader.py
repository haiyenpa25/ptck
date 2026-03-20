import json
import os
import re

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cw_config.json")
APP_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "app_settings.json")

def load_cw_config() -> dict:
    """Load the CW Greeks and properties from the static config."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cw_config(config: dict) -> bool:
    """Save updated configs to JSON"""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except:
        return False

def load_app_settings() -> dict:
    if not os.path.exists(APP_SETTINGS_PATH):
        return {"resolution": "1D"}
    try:
        with open(APP_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {"resolution": "1D"}

def save_app_settings(settings: dict) -> bool:
    try:
        with open(APP_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        return True
    except: return False

def get_all_symbols() -> list:
    """Gets list of all active symbols tracked."""
    return list(load_cw_config().keys())

def get_cw_metrics(symbol: str) -> dict:
    """Return Greeks for a symbol. Default to 1.0 if not found (Underlying)."""
    configs = load_cw_config()
    return configs.get(symbol, {"is_cw": False, "delta": 1.0, "gearing": 1.0})

def extract_underlying_from_cw(symbol: str) -> str:
    """Auto-extract underlying from CW symbol (e.g. CFPT2305 -> FPT)."""
    symbol = symbol.strip().upper()
    # Check if this is a standard HOSE CW format: C + XXX + YYNN
    m = re.match(r'^C([A-Z]{3})\d+$', symbol)
    if m: return m.group(1)
    return symbol
def fetch_warrant_metadata(symbol: str) -> dict:
    """Fetch full metadata for a CW from VNDirect API."""
    import requests
    url = f"https://finfo-api.vndirect.com.vn/v4/stocks?q=symbol:{symbol}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        data = r.json().get('data', [])
        if data:
            item = data[0]
            return {
                "issuer": item.get("issuerName", "Unknown"),
                "strike_price": item.get("strikePrice", 0),
                "ratio": item.get("exerciseRatio", "1:1"),
                "maturity_date": item.get("maturityDate", "N/A")
            }
    except:
        pass
    return {}
