# ============================================================
# TradingAI - AI MARKET ANALYST TEST
# ============================================================

from data_engine.unified_data import UnifiedMarketData
from data_engine.feature_engineering import FeatureEngineering
from data_engine.combined_ai_score import CombinedAIScore
from data_engine.ai_market_analyst import AIMarketAnalyst


print("=" * 70)
print("TradingAI - AI MARKET ANALYST TEST")
print("=" * 70)


SYMBOL = "RELIANCE"


# ============================================================
# TEST 1 - MARKET DATA
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD MARKET DATA")
print("=" * 70)

unified = UnifiedMarketData()

df = unified.get_stock_history(
    symbol=SYMBOL,
    source="eod2",
)

if df is None or df.empty:
    raise RuntimeError(
        "Market data is empty."
    )

print(
    f"Historical rows: {len(df)}"
)


# ============================================================
# TEST 2 - FEATURES
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD FEATURES")
print("=" * 70)

features = FeatureEngineering()

feature_df = features.build_features(
    df.copy()
)

latest = feature_df.tail(1)

print(
    f"Feature columns: {len(feature_df.columns)}"
)


# ============================================================
# TEST 3 - COMBINED AI SCORE
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - COMBINED AI SCORE")
print("=" * 70)

combined = CombinedAIScore()

combined.load()

score = combined.predict(
    latest
)

if score is None or score.empty:

    raise RuntimeError(
        "Combined AI score is empty."
    )

score_row = score.iloc[0]

print(
    score.to_string(
        index=False
    )
)


# ============================================================
# TEST 4 - GEMINI MARKET ANALYST
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - AI MARKET ANALYST")
print("=" * 70)

analyst = AIMarketAnalyst()

analysis = analyst.analyze_result(
    score_row
)

if not analysis:

    raise RuntimeError(
        "AI Market Analyst returned empty output."
    )

required_sections = [
    "MARKET BIAS:",
    "CONFIDENCE:",
    "QUANT SIGNALS:",
    "MARKET INTERPRETATION:",
    "RISK:",
    "TRADE CONTEXT:",
    "WATCH:",
]

missing_sections = [
    section
    for section in required_sections
    if section not in analysis
]

if missing_sections:

    raise RuntimeError(
        "Missing analyst sections: "
        f"{missing_sections}"
    )

print()
print(analysis)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("AI MARKET ANALYST TEST PASSED")
print("=" * 70)