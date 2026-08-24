# ============================================================
# TradingAI - NSE INDEX HISTORY TEST
# ============================================================

from datetime import date

from data_engine.nse_index_history import (
    NseIndexHistory,
)


print("=" * 70)
print(
    "TradingAI - NSE INDEX HISTORY TEST"
)
print("=" * 70)


source = NseIndexHistory()

df = source.get_history(
    symbol="NIFTY",
    from_date=date(2026, 1, 1),
    to_date=date(2026, 8, 20),
)

print(
    "\nColumns:"
)

print(
    df.columns.tolist()
)

print(
    "\nRows:",
    len(df)
)

print(
    "\nFirst:"
)

print(
    df.head(3).to_string(
        index=False
    )
)

print(
    "\nLast:"
)

print(
    df.tail(3).to_string(
        index=False
    )
)

required = [
    "timestamp",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

missing = [
    column
    for column in required
    if column not in df.columns
]

if missing:

    raise RuntimeError(
        f"Missing columns: {missing}"
    )

print("\n" + "=" * 70)
print(
    "NSE INDEX HISTORY TEST PASSED"
)
print("=" * 70)