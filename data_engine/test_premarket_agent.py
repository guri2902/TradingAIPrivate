# ============================================================
# TradingAI - PREMARKET AGENT TEST
# ============================================================

from data_engine.premarket_agent import PremarketAgent


print("=" * 70)
print("TradingAI - PREMARKET AGENT TEST")
print("=" * 70)


SYMBOL = "RELIANCE"


# ============================================================
# TEST 1 - INITIALIZE
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - INITIALIZE PREMARKET AGENT")
print("=" * 70)

agent = PremarketAgent()

print(
    "Premarket Agent initialized."
)


# ============================================================
# TEST 2 - BUILD CONTEXT
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD MARKET CONTEXT")
print("=" * 70)

context = agent.build_context(
    symbol=SYMBOL
)

print(
    "Context sections:",
    list(context.keys())
)

print(
    "Quant data available:",
    bool(context["quant"])
)

print(
    "Option-chain data available:",
    bool(context["option_chain"])
)

print(
    "Recent market rows:",
    len(context["recent_market"])
)


# ============================================================
# TEST 3 - GENERATE BRIEF
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - GENERATE PREMARKET BRIEF")
print("=" * 70)

brief = agent.run(
    symbol=SYMBOL
)

if not brief:

    raise RuntimeError(
        "Premarket Agent returned empty output."
    )


# ============================================================
# TEST 4 - VALIDATION
# ============================================================

required_sections = [
    "MARKET BIAS:",
    "CONFIDENCE:",
    "MARKET SUMMARY:",
    "QUANT VIEW:",
    "OPTION VIEW:",
    "KEY SUPPORT:",
    "KEY RESISTANCE:",
    "VOLATILITY VIEW:",
    "RISKS:",
    "WATCHLIST:",
    "SESSION PLAN:",
]

missing = [
    section
    for section in required_sections
    if section not in brief
]

if missing:

    raise RuntimeError(
        f"Missing sections: {missing}"
    )


print()
print(brief)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("PREMARKET AGENT TEST PASSED")
print("=" * 70)