# ============================================================
# TradingAI - POSTMARKET ANALYST TEST
# ============================================================

from data_engine.postmarket_analyst import PostmarketAnalyst


print("=" * 70)
print("TradingAI - POSTMARKET ANALYST TEST")
print("=" * 70)


SYMBOL = "RELIANCE"


# ============================================================
# TEST 1 - INITIALIZE
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - INITIALIZE POSTMARKET ANALYST")
print("=" * 70)

analyst = PostmarketAnalyst()

print(
    "Postmarket Analyst initialized."
)


# ============================================================
# TEST 2 - BUILD CONTEXT
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD SESSION CONTEXT")
print("=" * 70)

context = analyst.build_context(
    symbol=SYMBOL
)

print(
    "Context sections:",
    list(context.keys())
)

print(
    "Recent market rows:",
    len(context["recent_market"])
)

print(
    "Quant available:",
    bool(context["quant"])
)

print(
    "Option data available:",
    bool(context["option_chain"])
)

print(
    "Journal trades:",
    len(context["journal"])
)


# ============================================================
# TEST 3 - GENERATE REPORT
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - GENERATE POSTMARKET REPORT")
print("=" * 70)

report = analyst.run(
    symbol=SYMBOL
)

if not report:

    raise RuntimeError(
        "Postmarket report is empty."
    )


# ============================================================
# TEST 4 - VALIDATION
# ============================================================

required_sections = [
    "MARKET RECAP:",
    "SESSION BIAS:",
    "QUANT PERFORMANCE:",
    "OPTION CHAIN RECAP:",
    "WHAT WENT RIGHT:",
    "WHAT WENT WRONG:",
    "RISK REVIEW:",
    "NEXT SESSION WATCH:",
    "OVERALL ASSESSMENT:",
]

missing = [
    section
    for section in required_sections
    if section not in report
]

if missing:

    raise RuntimeError(
        f"Missing postmarket sections: {missing}"
    )


print()
print(report)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("POSTMARKET ANALYST TEST PASSED")
print("=" * 70)