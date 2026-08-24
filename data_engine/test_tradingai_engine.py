# ============================================================
# TradingAI - UNIFIED TRADING AI ENGINE TEST
# ============================================================

from data_engine.tradingai_engine import (
    TradingAIEngine,
)


print("=" * 70)
print(
    "TradingAI - UNIFIED TRADING AI ENGINE TEST"
)
print("=" * 70)


SYMBOL = "NIFTY"


# ============================================================
# TEST 1 - INITIALIZE ENGINE
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - INITIALIZE ENGINE")
print("=" * 70)

engine = TradingAIEngine()

print(
    "TradingAIEngine initialized."
)


# ============================================================
# TEST 2 - RESOLVE INSTRUMENT
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - RESOLVE INSTRUMENT")
print("=" * 70)

config = engine.resolve_instrument(
    SYMBOL
)

print(
    config
)

print(
    f"Market source: "
    f"{config.market_source}"
)

if SYMBOL == "NIFTY":

    if config.market_source != "nse":

        raise RuntimeError(
            "NIFTY must use NSE market source."
        )


# ============================================================
# TEST 3 - UNIFIED ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - RUN UNIFIED ANALYSIS")
print("=" * 70)

result = engine.analyze(
    SYMBOL
)

print(
    f"Symbol: "
    f"{result['symbol']}"
)

print(
    f"Market source: "
    f"{result['source']}"
)

print(
    f"Price: "
    f"{result['market']['close']}"
)


# ============================================================
# TEST 4 - TECHNICAL / QUANT
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - TECHNICAL / QUANT")
print("=" * 70)

for key, value in (
    result["technical"].items()
):

    if value is not None:

        print(
            f"{key}: {value}"
        )


# ============================================================
# TEST 5 - ML
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - ML")
print("=" * 70)

for key, value in (
    result["ml"].items()
):

    print(
        f"{key}: {value}"
    )


# ============================================================
# TEST 6 - OPTIONS
# ============================================================

print("\n" + "=" * 70)
print("TEST 6 - OPTIONS")
print("=" * 70)

options = result[
    "options"
]

print(
    f"Available: "
    f"{options['available']}"
)

print(
    f"Underlying: "
    f"{options.get('underlying')}"
)

print(
    f"Rows: "
    f"{options.get('rows')}"
)

print(
    f"Snapshots: "
    f"{options.get('snapshots', 0)}"
)

if options[
    "available"
]:

    summary = (
        options[
            "summary"
        ]
    )

    print(
        f"ATM: "
        f"{summary.get('atm_strike')}"
    )

    print(
        f"PCR: "
        f"{summary.get('put_call_oi_ratio')}"
    )

    print(
        f"Support: "
        f"{summary.get('support')}"
    )

    print(
        f"Resistance: "
        f"{summary.get('resistance')}"
    )


# ============================================================
# TEST 7 - FUTURES
# ============================================================

print("\n" + "=" * 70)
print("TEST 7 - FUTURES")
print("=" * 70)

futures = result[
    "futures"
]

print(
    f"Available: "
    f"{futures['available']}"
)

print(
    f"Underlying: "
    f"{futures.get('underlying')}"
)

print(
    f"Rows: "
    f"{futures.get('rows')}"
)

if not futures[
    "available"
]:

    print(
        f"Reason: "
        f"{futures.get('reason')}"
    )


# ============================================================
# TEST 8 - UNIFIED STRUCTURE
# ============================================================

print("\n" + "=" * 70)
print("TEST 8 - UNIFIED STRUCTURE")
print("=" * 70)

required_sections = [
    "timestamp",
    "instrument",
    "symbol",
    "source",
    "market",
    "technical",
    "ml",
    "options",
    "futures",
    "engine",
]

missing = [
    section
    for section in required_sections
    if section not in result
]

if missing:

    raise RuntimeError(
        f"Missing sections: {missing}"
    )

engine.validate_result(
    result
)

print(
    "Unified TradingAI context is valid."
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print(
    "UNIFIED TRADINGAI ENGINE TEST PASSED"
)
print("=" * 70)