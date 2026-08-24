"""
TradingAI - TRADE ENGINE TEST

Tests the Step 3 scoring contract:

1. TradeEngine imports correctly.
2. improve_trade_score() refines ai_score.
3. improve_trade_score() must NOT change probability.
4. Probability remains in a valid 0-100 range.
5. Recommendation still uses final score/probability.
"""

from engine.trade_engine import TradeEngine


print("=" * 70)
print("TradingAI - TRADE ENGINE TEST")
print("=" * 70)


# ============================================================
# TEST 1 - INITIALIZE
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - INITIALIZE TRADE ENGINE")
print("=" * 70)

engine = TradeEngine()

print("TradeEngine initialized.")


# ============================================================
# TEST 2 - SCORE / PROBABILITY CONTRACT
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - SCORE / PROBABILITY CONTRACT")
print("=" * 70)

trade = {
    "type": "CE",
    "ai_score": 60.0,
    "probability": 65.0,
    "greeks": {
        "delta": 0.50,
    },
    "reasons": [],
    "warnings": [],
}

market_score = {
    "bias": "Bullish",
}

chain = {
    "pcr": 1.20,
}

smc = {
    "bias": "bullish",
}

initial_score = trade["ai_score"]
initial_probability = trade["probability"]

engine.improve_trade_score(
    trade,
    market_score,
    chain,
    smc,
)

print(
    "Initial AI score:",
    initial_score,
)

print(
    "Final AI score:",
    trade["ai_score"],
)

print(
    "Initial probability:",
    initial_probability,
)

print(
    "Final probability:",
    trade["probability"],
)

# Score SHOULD be refined.
if trade["ai_score"] == initial_score:
    raise RuntimeError(
        "AI score was not refined."
    )

# Probability MUST remain authoritative.
if trade["probability"] != initial_probability:
    raise RuntimeError(
        "Probability changed inside "
        "improve_trade_score()."
    )

print(
    "Score refined and probability preserved."
)


# ============================================================
# TEST 3 - PROBABILITY VALIDITY
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - PROBABILITY VALIDATION")
print("=" * 70)

probability = float(
    trade["probability"]
)

if not (
    0.0
    <= probability
    <= 100.0
):

    raise RuntimeError(
        f"Invalid probability: {probability}"
    )

print(
    "Probability is valid:",
    probability,
)


# ============================================================
# TEST 4 - RECOMMENDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - RECOMMENDATION")
print("=" * 70)

recommendation = (
    engine.recommendation(
        trade["ai_score"],
        trade["probability"],
        trade["warnings"],
    )
)

print(
    "Recommendation:",
    recommendation,
)

if not isinstance(
    recommendation,
    str,
):
    raise RuntimeError(
        "Recommendation must be a string."
    )


# ============================================================
# TEST 5 - CONFLICT DOES NOT MUTATE PROBABILITY
# ============================================================

print("\n" + "=" * 70)
print(
    "TEST 5 - CONFLICT / PROBABILITY IMMUTABILITY"
)
print("=" * 70)

conflict_trade = {
    "type": "CE",
    "ai_score": 60.0,
    "probability": 72.0,
    "greeks": {
        "delta": 0.50,
    },
    "reasons": [],
    "warnings": [],
}

conflict_market = {
    "bias": "Bearish",
}

conflict_chain = {
    "pcr": 0.80,
}

conflict_smc = {
    "bias": "bearish",
}

conflict_probability = (
    conflict_trade["probability"]
)

engine.improve_trade_score(
    conflict_trade,
    conflict_market,
    conflict_chain,
    conflict_smc,
)

print(
    "Initial probability:",
    conflict_probability,
)

print(
    "Final probability:",
    conflict_trade["probability"],
)

if (
    conflict_trade["probability"]
    != conflict_probability
):

    raise RuntimeError(
        "Probability changed during "
        "conflict scoring."
    )

print(
    "Probability remains immutable."
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("TRADE ENGINE TEST PASSED")
print("=" * 70)