# ============================================================
# TradingAI - NSE FUTURES HISTORY TEST
# ============================================================

from datetime import date

from data_engine.nse_futures_history import (
    NseFuturesHistory,
)


print("=" * 70)
print(
    "TradingAI - NSE FUTURES HISTORY TEST"
)
print("=" * 70)


source = NseFuturesHistory()


print(
    "\nTEST 1 - DIRECT NIFTY FUTURES"
)

df = source.get_history(
    symbol="NIFTY",
    from_date=date(2026, 8, 1),
    to_date=date(2026, 8, 20),
    expiry=date(2026, 8, 25),
)

print(
    "\nRows:",
    len(df)
)

print(
    "\nColumns:"
)

print(
    df.columns.tolist()
)

print(
    "\nData:"
)

print(
    df.tail(
        5
    ).to_string(
        index=False
    )
)


print(
    "\nTEST 2 - REQUIRED FIELDS"
)

required = [
    "timestamp",
    "symbol",
    "expiry",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "oi",
    "oi_change",
]

missing = [
    column
    for column in required
    if column not in df.columns
]

if missing:

    raise RuntimeError(
        f"Missing futures fields: "
        f"{missing}"
    )

if df.empty:

    raise RuntimeError(
        "Futures dataframe is empty."
    )

print(
    "Required futures schema valid."
)


print(
    "\nTEST 3 - LATEST"
)

latest = (
    source.get_latest(
        "NIFTY"
    )
)

print(
    latest
)


print("\n" + "=" * 70)
print(
    "NSE FUTURES HISTORY TEST PASSED"
)
print("=" * 70)