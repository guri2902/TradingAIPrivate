# ============================================================
# TradingAI - COMBINED AI SCORE TEST
# ============================================================

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.feature_engineering import FeatureEngineering
from data_engine.combined_ai_score import CombinedAIScore


print("=" * 70)
print("TradingAI - COMBINED AI SCORE TEST")
print("=" * 70)


# ============================================================
# CONFIGURATION
# ============================================================

SYMBOL = "RELIANCE"


# ============================================================
# TEST 1 - LOAD MARKET DATA
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD HISTORICAL MARKET DATA")
print("=" * 70)

unified = UnifiedMarketData()

df = unified.get_stock_history(
    symbol=SYMBOL,
    source="eod2",
)

if df is None or df.empty:

    raise RuntimeError(
        "Historical market data could not be loaded."
    )

print(
    f"Historical rows: {len(df)}"
)


# ============================================================
# TEST 2 - BUILD TECHNICAL FEATURES
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD TECHNICAL FEATURES")
print("=" * 70)

features = FeatureEngineering()

feature_df = features.build_features(
    df.copy()
)

print(
    f"Feature rows: {len(feature_df)}"
)

print(
    f"Feature columns: {len(feature_df.columns)}"
)


# ============================================================
# TEST 3 - LOAD MODELS
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - LOAD QUANT MODELS")
print("=" * 70)

combined = CombinedAIScore()

combined.load()


# ============================================================
# TEST 4 - CALCULATE SCORE
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - CALCULATE COMBINED AI SCORE")
print("=" * 70)

latest = feature_df.tail(1)

result = combined.predict(
    latest
)

if result is None or result.empty:

    raise RuntimeError(
        "Combined AI score is empty."
    )

print(
    result.to_string(
        index=False
    )
)


# ============================================================
# TEST 5 - VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - SCORE VALIDATION")
print("=" * 70)

row = result.iloc[0]

required_columns = [
    "combined_score",
    "direction_score",
    "regime_score",
    "volatility_modifier",
    "confidence",
    "signal",
    "strength",
    "trade_suitability",
]

missing = [
    column
    for column in required_columns
    if column not in result.columns
]

if missing:

    raise RuntimeError(
        f"Missing combined score columns: {missing}"
    )


score = float(
    row["combined_score"]
)

confidence = float(
    row["confidence"]
)

if not -1.0 <= score <= 1.0:

    raise RuntimeError(
        f"Combined score out of range: {score}"
    )

if not 0.0 <= confidence <= 1.0:

    raise RuntimeError(
        f"Confidence out of range: {confidence}"
    )

if row["signal"] not in [
    "BULLISH",
    "BEARISH",
    "NEUTRAL",
]:

    raise RuntimeError(
        "Invalid signal."
    )

if row["strength"] not in [
    "STRONG",
    "MODERATE",
    "WEAK",
    "NONE",
]:

    raise RuntimeError(
        "Invalid strength."
    )

if row["trade_suitability"] not in [
    "FAVORABLE",
    "CAUTION",
    "AVOID",
]:

    raise RuntimeError(
        "Invalid trade suitability."
    )


print(
    f"Combined Score: {score:.4f}"
)

print(
    f"Confidence: {confidence:.4f}"
)

print(
    f"Signal: {row['signal']}"
)

print(
    f"Strength: {row['strength']}"
)

print(
    f"Trade suitability: "
    f"{row['trade_suitability']}"
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("COMBINED AI SCORE TEST PASSED")
print("=" * 70)