import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cw_config.json")

def load_cw_config() -> dict:
    """Load the CW Greeks and properties from the static config."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_cw_metrics(symbol: str) -> dict:
    """Return Greeks for a symbol. Default to 1.0 if not found (Underlying)."""
    configs = load_cw_config()
    return configs.get(symbol, {"is_cw": False, "delta": 1.0, "gearing": 1.0})
