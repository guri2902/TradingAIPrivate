# ============================================================
# TradingAI - FEATURE ENGINEERING TEST
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.feature_engineering import (
    FeatureEngineering
)


print("=" * 70)
print("TradingAI - FEATURE ENGINEERING TEST")
print("=" * 70)


# ============================================================
# LOAD EXISTING PARQUET
# ============================================================

path = Path(
    "market_data/processed/stock_reliance.parquet"
)

print("\n" + "=" * 70)
print("TEST DATA")
print("=" * 70)

df = pd.read_parquet(path)

print(
    f"Rows: {len(df)}"
)

print(
    f"Columns: {list(df.columns)}"
)


# ============================================================
# BUILD FEATURES
# ============================================================

print("\n" + "=" * 70)
print("BUILDING FEATURES")
print("=" * 70)

engine = FeatureEngineering()

features = engine.build_features(
    df
)


# ============================================================
# RESULTS
# ============================================================

print(
    f"\nFeature rows: {len(features)}"
)

print(
    f"Feature columns: {len(features.columns)}"
)

print("\nFeature columns:")

print(
    features.columns.tolist()
)


# ============================================================
# SAMPLE
# ============================================================

print("\n" + "=" * 70)
print("FIRST 5 ROWS")
print("=" * 70)

print(
    features.head()
)


# ============================================================
# FEATURE CHECK
# ============================================================

expected_features = [
    "return",
    "log_return",
    "sma_5",
    "sma_20",
    "sma_50",
    "ema_9",
    "ema_21",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_histogram",
    "atr_14",
    "bb_upper",
    "bb_middle",
    "bb_lower",
    "volume_ratio",
    "volatility_20",
    "momentum_20",
]


print("\n" + "=" * 70)
print("FEATURE VALIDATION")
print("=" * 70)

missing = [
    feature
    for feature in expected_features
    if feature not in features.columns
]

if missing:

    print(
        "FAILED"
    )

    print(
        f"Missing features: {missing}"
    )

    raise SystemExit(1)


print(
    "All expected features present."
)


# ============================================================
# SAVE
# ============================================================

output_path = Path(
    "market_data/processed/"
    "features_reliance.parquet"
)

engine.save_features(
    features,
    output_path
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("FEATURE ENGINEERING TEST PASSED")
print("=" * 70)