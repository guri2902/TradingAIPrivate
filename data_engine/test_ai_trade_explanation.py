# ============================================================
# TradingAI - AI TRADE EXPLANATION TEST
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.feature_engineering import FeatureEngineering
from data_engine.combined_ai_score import CombinedAIScore
from data_engine.ai_option_chain_analyst import (
    AIOptionChainAnalyst,
)
from data_engine.ai_trade_explanation import (
    AITradeExplanation,
)


print("=" * 70)
print("TradingAI - AI TRADE EXPLANATION TEST")
print("=" * 70)


SYMBOL = "RELIANCE"


# ============================================================
# TEST 1 - MARKET DATA
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD MARKET DATA")
print("=" * 70)

unified = UnifiedMarketData()

market_df = unified.get_stock_history(
    symbol=SYMBOL,
    source="eod2",
)

if market_df is None or market_df.empty:

    raise RuntimeError(
        "Market data is empty."
    )

print(
    f"Market rows: {len(market_df)}"
)


# ============================================================
# TEST 2 - FEATURES
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD FEATURES")
print("=" * 70)

features = FeatureEngineering()

feature_df = features.build_features(
    market_df.copy()
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
# TEST 4 - OPTION CHAIN
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - OPTION CHAIN")
print("=" * 70)

option_path = Path(
    "market_data/processed/nifty_option_history.parquet"
)

if not option_path.exists():

    raise RuntimeError(
        f"Option history not found: {option_path}"
    )

option_df = pd.read_parquet(
    option_path
)

if option_df.empty:

    raise RuntimeError(
        "Option history is empty."
    )

option_analyst = AIOptionChainAnalyst()

option_summary = (
    option_analyst.build_summary(
        option_df
    )
)

print(
    "Option summary built."
)


# ============================================================
# TEST 5 - AI TRADE EXPLANATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - AI TRADE EXPLANATION")
print("=" * 70)

trade_ai = AITradeExplanation()

explanation = (
    trade_ai.explain_result(
        score_row,
        option_data=option_summary,
    )
)

if not explanation:

    raise RuntimeError(
        "Trade explanation is empty."
    )

required_sections = [
    "TRADE BIAS:",
    "CONFIDENCE:",
    "WHY:",
    "SUPPORTING MODELS:",
    "OPTION CONTEXT:",
    "WEAKNESS:",
    "INVALIDATION:",
    "SUITABILITY:",
]

missing = [
    section
    for section in required_sections
    if section not in explanation
]

if missing:

    raise RuntimeError(
        f"Missing explanation sections: {missing}"
    )

print()
print(explanation)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("AI TRADE EXPLANATION TEST PASSED")
print("=" * 70)