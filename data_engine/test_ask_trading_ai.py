# ============================================================
# TradingAI - ASK TRADINGAI TEST
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.feature_engineering import FeatureEngineering
from data_engine.ask_trading_ai import AskTradingAI


print("=" * 70)
print("TradingAI - ASK TRADINGAI TEST")
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

print(
    f"Feature columns: {len(feature_df.columns)}"
)


# ============================================================
# TEST 3 - OPTION HISTORY
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - LOAD OPTION HISTORY")
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

print(
    f"Option rows: {len(option_df)}"
)

print(
    f"Snapshots: "
    f"{option_df['timestamp'].nunique()}"
)


# ============================================================
# TEST 4 - BUILD CONTEXT
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - BUILD TRADINGAI CONTEXT")
print("=" * 70)

ask_ai = AskTradingAI()

context = ask_ai.build_context(
    market_features=feature_df,
    option_history=option_df,
)

print(
    "Context sections:",
    list(context.keys())
)


# ============================================================
# TEST 5 - ASK QUESTIONS
# ============================================================

questions = [
    "What is the current market bias and why?",
    "What are the strongest option-chain support and resistance levels?",
    "How are volatility and the option chain affecting the current setup?",
]


for number, question in enumerate(
    questions,
    start=1
):

    print(
        "\n" + "=" * 70
    )

    print(
        f"QUESTION {number}"
    )

    print(
        "=" * 70
    )

    print(
        f"Q: {question}"
    )

    answer = ask_ai.ask(
        question=question,
        context=context,
    )

    if not answer:

        raise RuntimeError(
            "Ask TradingAI returned an empty answer."
        )

    print(
        f"\nA: {answer}"
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("ASK TRADINGAI TEST PASSED")
print("=" * 70)