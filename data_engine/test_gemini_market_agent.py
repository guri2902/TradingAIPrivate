# ============================================================
# TradingAI - GEMINI MARKET ANALYST TEST
# ============================================================

from data_engine.realtime_data_orchestrator import (
    RealtimeDataOrchestrator,
)

from data_engine.gemini_market_agent import (
    GeminiMarketAgent,
)


print("=" * 70)
print(
    "TradingAI - GEMINI MARKET ANALYST TEST"
)
print("=" * 70)


# ============================================================
# TEST 1 - LOAD MARKET STATE
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD TRADINGAI STATE")
print("=" * 70)

orchestrator = (
    RealtimeDataOrchestrator()
)

state = (
    orchestrator.build_state(
        "NIFTY"
    )
)

print(
    "Current:",
    state.get(
        "current"
    )
)

print(
    "Options:",
    state.get(
        "options",
        {}
    ).get(
        "available"
    )
)

print(
    "Futures:",
    state.get(
        "futures",
        {}
    ).get(
        "available"
    )
)


# ============================================================
# TEST 2 - INITIALIZE GEMINI
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - INITIALIZE GEMINI")
print("=" * 70)

agent = (
    GeminiMarketAgent()
)

print(
    "Model:",
    agent.model
)


# ============================================================
# TEST 3 - ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - GEMINI ANALYSIS")
print("=" * 70)

result = (
    agent.analyze(
        state
    )
)

print(
    "\nSummary:"
)

print(
    result["summary"]
)

print(
    "\nBias:",
    result["market_bias"]
)

print(
    "Confidence:",
    result["confidence"]
)

print(
    "\nTechnical:",
    result["technical_view"]
)

print(
    "\nOptions:",
    result["options_view"]
)

print(
    "\nFutures:",
    result["futures_view"]
)

print(
    "\nRisk:",
    result["risk_view"]
)

print(
    "\nBullish factors:"
)

for item in (
    result["bullish_factors"]
):

    print(
        " -",
        item
    )

print(
    "\nBearish factors:"
)

for item in (
    result["bearish_factors"]
):

    print(
        " -",
        item
    )

print(
    "\nWatch levels:"
)

for item in (
    result["watch_levels"]
):

    print(
        " -",
        item
    )

print(
    "\nWarnings:"
)

for item in (
    result["warnings"]
):

    print(
        " -",
        item
    )


# ============================================================
# TEST 4 - OUTPUT SANITY
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - OUTPUT SANITY")
print("=" * 70)

required = [
    "summary",
    "market_bias",
    "confidence",
    "technical_view",
    "options_view",
    "futures_view",
    "risk_view",
    "bullish_factors",
    "bearish_factors",
    "watch_levels",
    "warnings",
]

for key in required:

    if key not in result:

        raise RuntimeError(
            f"Missing Gemini output field: {key}"
        )

if result[
    "market_bias"
] not in {
    "BULLISH",
    "BEARISH",
    "NEUTRAL",
    "INSUFFICIENT_DATA",
}:

    raise RuntimeError(
        "Invalid market bias."
    )

confidence = float(
    result["confidence"]
)

if not (
    0.0
    <= confidence
    <= 1.0
):

    raise RuntimeError(
        "Invalid confidence."
    )

print(
    "Output structure valid."
)

print("\n" + "=" * 70)
print(
    "GEMINI MARKET ANALYST TEST PASSED"
)
print("=" * 70)