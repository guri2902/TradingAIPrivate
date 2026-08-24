# ============================================================
# TradingAI - NSE FUTURES SOURCE TEST
# ============================================================

from data_engine.nse_source import NseSource


print("=" * 70)
print("TradingAI - NSE FUTURES SOURCE TEST")
print("=" * 70)


source = NseSource(
    "market_data/raw/nse"
)


print("\n" + "=" * 70)
print("TEST - NIFTY FUTURES")
print("=" * 70)


df = source.get_futures(
    symbol="NIFTY"
)


print(
    f"\nRows: {len(df)}"
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
    df.to_string(index=False)
)


if df.empty:

    raise RuntimeError(
        "NIFTY futures returned no data."
    )


required = [
    "symbol",
    "expiry",
    "last_price",
    "open_interest",
    "underlying_value",
    "timestamp",
    "source",
]


missing = [
    column
    for column in required
    if column not in df.columns
]


if missing:

    raise RuntimeError(
        f"Missing futures columns: {missing}"
    )


print("\n" + "=" * 70)
print("NSE FUTURES SOURCE TEST PASSED")
print("=" * 70)