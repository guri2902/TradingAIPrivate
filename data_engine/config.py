from pathlib import Path


# ============================================================
# TRADINGAI DATA ENGINE CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------
# DATA DIRECTORIES
# ------------------------------------------------------------

MARKET_DATA_DIR = BASE_DIR / "market_data"

RAW_DIR = MARKET_DATA_DIR / "raw"

JUGAAD_RAW_DIR = RAW_DIR / "jugaad"
EOD2_RAW_DIR = RAW_DIR / "eod2"
NSE_RAW_DIR = RAW_DIR / "nse"

PROCESSED_DIR = MARKET_DATA_DIR / "processed"

NIFTY_DIR = PROCESSED_DIR / "nifty"
STOCKS_DIR = PROCESSED_DIR / "stocks"
FUTURES_DIR = PROCESSED_DIR / "futures"
OPTIONS_DIR = PROCESSED_DIR / "options"

LIVE_DIR = MARKET_DATA_DIR / "live"


# ------------------------------------------------------------
# CREATE DIRECTORIES
# ------------------------------------------------------------

for directory in [
    JUGAAD_RAW_DIR,
    EOD2_RAW_DIR,
    NSE_RAW_DIR,
    NIFTY_DIR,
    STOCKS_DIR,
    FUTURES_DIR,
    OPTIONS_DIR,
    LIVE_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True
    )


# ------------------------------------------------------------
# DEFAULT SYMBOLS
# ------------------------------------------------------------

INDEX_SYMBOLS = [
    "NIFTY 50",
    "NIFTY BANK",
]


WATCHLIST = [
    "RELIANCE",
    "HDFCBANK",
    "ICICIBANK",
    "INFY",
    "TCS",
    "SBIN",
]


# ------------------------------------------------------------
# PRIMARY INDEX
# ------------------------------------------------------------

PRIMARY_INDEX = "NIFTY 50"