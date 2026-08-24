# ============================================================
# TradingAI - LIVE MARKET DATA TEST
# ============================================================

from data_engine.unified_data import UnifiedMarketData


print("=" * 70)
print("TradingAI - LIVE MARKET DATA TEST")
print("=" * 70)


# ============================================================
# INITIALIZE
# ============================================================

market = UnifiedMarketData()


# ============================================================
# TEST
# ============================================================

print()
print("=" * 70)
print("TEST - NIFTY LIVE MARKET DATA")
print("=" * 70)

snapshot = market.get_live_market_data(
    symbol="NIFTY"
)


# ============================================================
# VALIDATION
# ============================================================

required_keys = [
    "timestamp",
    "symbol",
    "underlying_value",
    "option_chain",
    "futures",
]

missing = [
    key
    for key in required_keys
    if key not in snapshot
]

if missing:
    raise RuntimeError(
        f"Missing snapshot keys: {missing}"
    )


option_chain = snapshot["option_chain"]
futures = snapshot["futures"]


if option_chain is None or option_chain.empty:
    raise RuntimeError(
        "Option chain is empty"
    )


if futures is None or futures.empty:
    raise RuntimeError(
        "Futures data is empty"
    )


if snapshot["underlying_value"] is None:
    raise RuntimeError(
        "Underlying value is missing"
    )


# ============================================================
# OUTPUT
# ============================================================

print()
print("Snapshot timestamp:")
print(snapshot["timestamp"])

print()
print("Symbol:")
print(snapshot["symbol"])

print()
print("Underlying:")
print(snapshot["underlying_value"])

print()
print("Option rows:")
print(len(option_chain))

print()
print("Futures rows:")
print(len(futures))


print()
print("=" * 70)
print("OPTION CHAIN SAMPLE")
print("=" * 70)

print(
    option_chain[
        [
            "symbol",
            "expiry",
            "strike",
            "option_type",
            "last_price",
            "oi",
            "volume",
        ]
    ].head(5)
)


print()
print("=" * 70)
print("FUTURES SAMPLE")
print("=" * 70)

print(
    futures[
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
    ]
)


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 70)
print("LIVE MARKET DATA TEST PASSED")
print("=" * 70)