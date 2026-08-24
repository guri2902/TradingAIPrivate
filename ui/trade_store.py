import json
import os
from datetime import date


# =========================================================
# STORAGE
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

JOURNAL_FILE = os.path.join(
    BASE_DIR,
    "trade_journal.json"
)

# Active/persisted trades are deliberately kept separate from
# the journal. The journal is for completed/history records;
# this file is for trades that must survive an app restart.
TRACKED_TRADES_FILE = os.path.join(
    BASE_DIR,
    "tracked_trades.json"
)


# =========================================================
# JOURNAL LOAD
# =========================================================

def load_trades():
    """Load all trades from the journal."""

    if not os.path.exists(JOURNAL_FILE):
        return []

    try:
        with open(
            JOURNAL_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except Exception as e:
        print("Trade store load error:", e)

    return []


# =========================================================
# JOURNAL SAVE
# =========================================================

def save_trades(trades):
    """Save trades to the journal."""

    try:
        with open(
            JOURNAL_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                trades,
                file,
                indent=4
            )

        return True

    except Exception as e:
        print("Trade store save error:", e)
        return False


# =========================================================
# ACTIVE / TRACKED TRADES
# =========================================================

def load_tracked_trades():
    """
    Load trades that are currently being tracked.

    These are not journal records. They contain the fixed trade
    definition (entry/SL/targets/quantity) plus the last known
    state so the tracking screen can be restored after restart.
    """

    if not os.path.exists(TRACKED_TRADES_FILE):
        return []

    try:
        with open(
            TRACKED_TRADES_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            return []

        # Ignore malformed records instead of allowing one bad
        # record to break application startup.
        cleaned = []
        for trade in data:
            if isinstance(trade, dict):
                cleaned.append(trade)

        return cleaned

    except Exception as e:
        print("Tracked trades load error:", e)
        return []


def save_tracked_trades(trades):
    """Persist currently tracked trades safely."""

    try:
        os.makedirs(BASE_DIR, exist_ok=True)

        # Atomic replace prevents a half-written JSON file if the
        # process is interrupted during a save.
        temp_file = TRACKED_TRADES_FILE + ".tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                list(trades or []),
                file,
                indent=4
            )
            file.flush()
            os.fsync(file.fileno())

        os.replace(
            temp_file,
            TRACKED_TRADES_FILE
        )

        return True

    except Exception as e:
        print("Tracked trades save error:", e)

        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass

        return False


def delete_tracked_trades():
    """Remove the persisted active-trade file."""

    try:
        if os.path.exists(TRACKED_TRADES_FILE):
            os.remove(TRACKED_TRADES_FILE)
        return True
    except Exception as e:
        print("Tracked trades delete error:", e)
        return False


# =========================================================
# TODAY
# =========================================================

def today_trades():
    """Return today's trades."""

    today = date.today().isoformat()

    return [
        trade
        for trade in load_trades()
        if str(trade.get("date", "")) == today
    ]


# =========================================================
# TODAY P&L
# =========================================================

def today_pnl():
    """Calculate today's realised P&L."""

    return sum(
        float(trade.get("pnl", 0) or 0)
        for trade in today_trades()
    )


# =========================================================
# TODAY TRADE COUNT
# =========================================================

def today_trade_count():
    return len(today_trades())


# =========================================================
# WIN RATE
# =========================================================

def today_win_rate():

    trades = today_trades()

    if not trades:
        return 0.0

    wins = sum(
        1
        for trade in trades
        if str(
            trade.get("result", "")
        ).upper() == "WIN"
    )

    return (
        wins /
        len(trades) *
        100
    )


# =========================================================
# BEST TRADE
# =========================================================

def best_trade():

    trades = today_trades()

    if not trades:
        return None

    return max(
        trades,
        key=lambda trade:
        float(trade.get("pnl", 0) or 0)
    )


# =========================================================
# WORST TRADE
# =========================================================

def worst_trade():

    trades = today_trades()

    if not trades:
        return None

    return min(
        trades,
        key=lambda trade:
        float(trade.get("pnl", 0) or 0)
    )


# =========================================================
# TOTAL P&L
# =========================================================

def total_pnl():

    return sum(
        float(trade.get("pnl", 0) or 0)
        for trade in load_trades()
    )


# =========================================================
# TOTAL TRADES
# =========================================================

def total_trade_count():

    return len(load_trades())