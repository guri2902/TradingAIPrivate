# ============================================================
# TradingAI - INTRADAY MONITOR TEST
# ============================================================

from data_engine.intraday_monitor import IntradayMonitor


print("=" * 70)
print("TradingAI - INTRADAY MONITOR TEST")
print("=" * 70)


# ============================================================
# TEST 1 - INITIALIZE
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - INITIALIZE MONITOR")
print("=" * 70)

monitor = IntradayMonitor(
    symbol="RELIANCE"
)

print(
    "Intraday Monitor initialized."
)


# ============================================================
# TEST 2 - CURRENT STATE
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - CURRENT MARKET STATE")
print("=" * 70)

state = (
    monitor.get_current_state()
)

print(
    f"Symbol: {state['symbol']}"
)

print(
    f"Price: {state['price']}"
)

print(
    f"Direction: "
    f"{state['direction_prediction']}"
)

print(
    f"Regime: "
    f"{state['regime_prediction']}"
)

print(
    f"Volatility: "
    f"{state['volatility_regime']}"
)

print(
    f"Combined score: "
    f"{state['combined_score']:.4f}"
)

print(
    f"Confidence: "
    f"{state['confidence']:.4f}"
)


# ============================================================
# TEST 3 - FIRST CHECK
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - FIRST INTRADAY CHECK")
print("=" * 70)

first = (
    monitor.check_once()
)

if not first:

    raise RuntimeError(
        "First intraday check returned empty output."
    )

print()
print(first)


# ============================================================
# TEST 4 - SIMULATED CHANGE DETECTION
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - CHANGE DETECTION")
print("=" * 70)

previous = state.copy()

current = state.copy()

# Simulate meaningful model changes.
current[
    "direction_prediction"
] = (
    "UP"
    if previous[
        "direction_prediction"
    ] == 0
    else "DOWN"
)

current[
    "up_probability"
] = 0.75

current[
    "down_probability"
] = 0.25

current[
    "regime_prediction"
] = "BULL"

current[
    "volatility_regime"
] = "HIGH"

current[
    "predicted_volatility"
] = (
    previous[
        "predicted_volatility"
    ] + 0.10
)

current[
    "combined_score"
] = 0.35

changes = (
    monitor.detect_changes(
        previous,
        current,
    )
)

print(
    "Detected changes:"
)

for key, value in changes.items():

    print(
        f"{key}: {value}"
    )

if changes["status"] == "UNCHANGED":

    raise RuntimeError(
        "Simulated material changes were not detected."
    )


# ============================================================
# TEST 5 - AI ALERT
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - AI INTRADAY ALERT")
print("=" * 70)

alert = (
    monitor.generate_alert(
        previous,
        current,
        changes,
    )
)

if not alert:

    raise RuntimeError(
        "AI intraday alert is empty."
    )

required_sections = [
    "STATUS:",
    "MARKET BIAS:",
    "CHANGE SUMMARY:",
    "DIRECTION CHANGE:",
    "REGIME CHANGE:",
    "VOLATILITY CHANGE:",
    "OPTION CHANGE:",
    "RISK:",
    "ACTION:",
]

missing = [
    section
    for section in required_sections
    if section not in alert
]

if missing:

    raise RuntimeError(
        f"Missing sections: {missing}"
    )

print()
print(alert)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("INTRADAY MONITOR TEST PASSED")
print("=" * 70)