from data_engine.unified_data import UnifiedMarketData


print("=" * 70)
print("TradingAI - UNIFIED FUTURES TEST")
print("=" * 70)


market = UnifiedMarketData()


print("\n" + "=" * 70)
print("TEST - NIFTY FUTURES")
print("=" * 70)


df = market.get_futures(
    symbol="NIFTY"
)


print(
    f"\nRows: {len(df)}"
)

print(
    "\nColumns:"
)

print(
    list(df.columns)
)

print(
    "\nData:"
)

print(
    df[
        [
            "symbol",
            "expiry",
            "last_price",
            "open",
            "high",
            "low",
            "volume",
            "open_interest",
            "open_interest_change",
            "underlying_value",
        ]
    ].to_string(index=False)
)


required = [
    "symbol",
    "expiry",
    "last_price",
    "open",
    "high",
    "low",
    "volume",
    "open_interest",
    "open_interest_change",
    "underlying_value",
]


missing = [
    column
    for column in required
    if column not in df.columns
]


if missing:

    raise RuntimeError(
        f"Missing unified futures columns: "
        f"{missing}"
    )


if df.empty:

    raise RuntimeError(
        "Unified futures returned no data."
    )


print("\n" + "=" * 70)
print("UNIFIED FUTURES TEST PASSED")
print("=" * 70)