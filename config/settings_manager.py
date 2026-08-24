import json
from pathlib import Path


# =========================================================
# SETTINGS FILE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE_DIR / "config" / "settings.json"


# =========================================================
# DEFAULT SETTINGS
# =========================================================

DEFAULT_SETTINGS = {
    # General
    "start_page": "Dashboard",
    "auto_refresh": 30,
    "dark_interface": True,

    # Market
    "default_index": "NIFTY 50",
    "option_expiry": "Nearest Expiry",

    # AI
    "minimum_confidence": 60,
    "minimum_probability": 60,
    "enable_ai_recommendations": True,

    # Risk
    "trading_capital": 50000.0,
    "risk_per_trade": 1.0,
    "daily_loss_limit": 1000.0,
    "daily_profit_target": 500.0,
}


# =========================================================
# LOAD
# =========================================================

def load_settings():
    """
    Load saved settings.

    If settings.json doesn't exist or is corrupted,
    return default settings.
    """

    try:
        SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not SETTINGS_FILE.exists():
            save_settings(DEFAULT_SETTINGS.copy())
            return DEFAULT_SETTINGS.copy()

        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            saved = json.load(file)

        settings = DEFAULT_SETTINGS.copy()
        settings.update(saved)

        return settings

    except Exception as e:

        print(
            f"Could not load settings: {e}"
        )

        return DEFAULT_SETTINGS.copy()


# =========================================================
# SAVE
# =========================================================

def save_settings(settings):
    """
    Save settings to config/settings.json
    """

    try:

        SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            SETTINGS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                settings,
                file,
                indent=4
            )

        return True

    except Exception as e:

        print(
            f"Could not save settings: {e}"
        )

        return False


# =========================================================
# GET ONE VALUE
# =========================================================

def get_setting(key, default=None):

    settings = load_settings()

    return settings.get(
        key,
        default
    )