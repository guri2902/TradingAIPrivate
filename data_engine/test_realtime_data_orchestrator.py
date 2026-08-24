# ============================================================
# TradingAI - REAL-TIME DATA ORCHESTRATOR TEST
# ============================================================

from data_engine.realtime_data_orchestrator import (
    RealtimeDataOrchestrator,
)


print("=" * 70)
print(
    "TradingAI - REAL-TIME DATA ORCHESTRATOR TEST"
)
print("=" * 70)


# ============================================================
# TEST 1 - INITIALIZE
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - INITIALIZE")
print("=" * 70)

orchestrator = (
    RealtimeDataOrchestrator()
)

print(
    "Orchestrator initialized."
)


# ============================================================
# TEST 2 - BUILD NIFTY STATE
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD NIFTY STATE")
print("=" * 70)

state = (
    orchestrator.build_state(
        "NIFTY"
    )
)


if not isinstance(
    state,
    dict,
):

    raise RuntimeError(
        "State must be a dictionary."
    )

print(
    "Instrument:",
    state[
        "instrument"
    ]
)

print(
    "Current:",
    state[
        "current"
    ]
)


# ============================================================
# TEST 3 - MARKET
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - MARKET")
print("=" * 70)

market = (
    state[
        "market"
    ]
)

print(
    "Rows:",
    market.get(
        "rows"
    )
)

print(
    "Source:",
    market.get(
        "source"
    )
)

print(
    "Latest:",
    market.get(
        "latest_timestamp"
    )
)

if not market.get(
    "available"
):

    raise RuntimeError(
        "Market history unavailable."
    )


# ============================================================
# TEST 4 - OPTIONS
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - LIVE OPTIONS")
print("=" * 70)

options = (
    state[
        "options"
    ]
)

print(
    "Available:",
    options.get(
        "available"
    )
)

print(
    "Rows:",
    options.get(
        "rows"
    )
)

print(
    "Underlying:",
    options.get(
        "underlying"
    )
)

print(
    "Expiry:",
    options.get(
        "expiry"
    )
)

if not options.get(
    "available"
):

    raise RuntimeError(
        "Live option chain unavailable."
    )


# ============================================================
# TEST 5 - FUTURES
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - LIVE FUTURES")
print("=" * 70)

futures = (
    state[
        "futures"
    ]
)

print(
    "Available:",
    futures.get(
        "available"
    )
)

print(
    "Rows:",
    futures.get(
        "rows"
    )
)

print(
    "Expiry:",
    futures.get(
        "expiry"
    )
)

if not futures.get(
    "available"
):

    raise RuntimeError(
        "Live futures unavailable."
    )


# ============================================================
# TEST 6 - FRESHNESS
# ============================================================

print("\n" + "=" * 70)
print("TEST 6 - DATA FRESHNESS")
print("=" * 70)

freshness = (
    state[
        "freshness"
    ]
)

print(
    freshness
)

required_freshness = [
    "generated_at",
    "market_timestamp",
    "market_age_hours",
    "options_live",
    "futures_live",
    "current_price_source",
]

missing = [
    key
    for key in required_freshness
    if key not in freshness
]

if missing:

    raise RuntimeError(
        f"Missing freshness fields: {missing}"
    )


# ============================================================
# TEST 7 - CURRENT PRICE
# ============================================================

print("\n" + "=" * 70)
print("TEST 7 - CURRENT PRICE")
print("=" * 70)

current = (
    state[
        "current"
    ]
)

price = current.get(
    "price"
)

print(
    "Price:",
    price
)

print(
    "Source:",
    current.get(
        "price_source"
    )
)

if price is None:

    raise RuntimeError(
        "Current price unavailable."
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print(
    "REAL-TIME DATA ORCHESTRATOR TEST PASSED"
)
print("=" * 70)