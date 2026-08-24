# ============================================================
# TradingAI - AI OPTION CHAIN ANALYST TEST
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.ai_option_chain_analyst import (
    AIOptionChainAnalyst
)


print("=" * 70)
print("TradingAI - AI OPTION CHAIN ANALYST TEST")
print("=" * 70)


# ============================================================
# TEST 1 - LOAD OPTION HISTORY
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD OPTION CHAIN")
print("=" * 70)

path = Path(
    "market_data/processed/nifty_option_history.parquet"
)

if not path.exists():

    raise RuntimeError(
        f"Option history not found: {path}"
    )

df = pd.read_parquet(
    path
)

if df.empty:

    raise RuntimeError(
        "Option history is empty."
    )

print(
    f"Rows: {len(df)}"
)

print(
    f"Snapshots: "
    f"{df['timestamp'].nunique()}"
)

print(
    f"Latest: "
    f"{df['timestamp'].max()}"
)


# ============================================================
# TEST 2 - BUILD OPTION SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD OPTION SUMMARY")
print("=" * 70)

analyst = AIOptionChainAnalyst()

summary = analyst.build_summary(
    df
)

for key, value in summary.items():

    print(
        f"{key}: {value}"
    )


# ============================================================
# TEST 3 - AI ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - AI OPTION CHAIN ANALYSIS")
print("=" * 70)

analysis = analyst.analyze(
    summary
)

if not analysis:

    raise RuntimeError(
        "AI option-chain analysis is empty."
    )

required_sections = [
    "OPTION BIAS:",
    "CONFIDENCE:",
    "POSITIONING:",
    "SUPPORT:",
    "RESISTANCE:",
    "VOLATILITY:",
    "INTERPRETATION:",
    "RISK:",
    "WATCH:",
]

missing = [
    section
    for section in required_sections
    if section not in analysis
]

if missing:

    raise RuntimeError(
        f"Missing sections: {missing}"
    )

print()
print(analysis)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("AI OPTION CHAIN ANALYST TEST PASSED")
print("=" * 70)