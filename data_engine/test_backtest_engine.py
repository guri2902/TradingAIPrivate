# ============================================================
# TradingAI - AI BACKTEST ENGINE TEST
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.backtest_engine import BacktestEngine


print("=" * 70)
print("TradingAI - AI BACKTEST ENGINE TEST")
print("=" * 70)


SYMBOL = "RELIANCE"


# ============================================================
# TEST 1 - LOAD DATA
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD HISTORICAL DATA")
print("=" * 70)

unified = UnifiedMarketData()

df = unified.get_stock_history(
    symbol=SYMBOL,
    source="eod2",
)

if df is None or df.empty:

    raise RuntimeError(
        "Historical data is empty."
    )

print(
    f"Rows: {len(df)}"
)


# ============================================================
# TEST 2 - RUN BACKTEST
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - RUN AI BACKTEST")
print("=" * 70)

engine = BacktestEngine(
    initial_capital=100000,
    position_size=10000,
    min_score=0.20,
)

result = engine.run(
    df
)

trades = result[
    "trades"
]

metrics = result[
    "metrics"
]


# ============================================================
# TEST 3 - REPORT
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - BACKTEST REPORT")
print("=" * 70)

engine.print_report(
    metrics
)

print(
    f"\nGenerated trades: "
    f"{len(trades)}"
)


# ============================================================
# TEST 4 - VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - RESULT VALIDATION")
print("=" * 70)

required_metrics = [
    "trades",
    "wins",
    "losses",
    "win_rate",
    "total_pnl",
    "avg_pnl",
    "profit_factor",
    "max_drawdown",
    "final_capital",
    "status",
]

missing = [
    key
    for key in required_metrics
    if key not in metrics
]

if missing:

    raise RuntimeError(
        f"Missing metrics: {missing}"
    )

if (
    metrics["trades"]
    > 0
):

    required_columns = [
        "timestamp",
        "entry",
        "exit",
        "signal",
        "score",
        "confidence",
        "regime",
        "volatility_regime",
        "actual_return",
        "strategy_return",
        "pnl",
        "prediction_correct",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in trades.columns
    ]

    if missing_columns:

        raise RuntimeError(
            f"Missing trade columns: "
            f"{missing_columns}"
        )


# ============================================================
# TEST 5 - SAVE
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - SAVE BACKTEST")
print("=" * 70)

if not trades.empty:

    saved = engine.save(
        trades
    )

    print(
        f"Saved: {saved}"
    )

    if not Path(
        saved
    ).exists():

        raise RuntimeError(
            "Backtest file was not saved."
        )

else:

    print(
        "No trades generated; nothing to save."
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("AI BACKTEST ENGINE TEST PASSED")
print("=" * 70)