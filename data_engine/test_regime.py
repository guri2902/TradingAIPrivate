# ============================================================
# TradingAI - MARKET REGIME MODEL TEST
# ============================================================

from datetime import date, timedelta

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.regime_dataset import RegimeDataset
from data_engine.regime_model import RegimeModel


print("=" * 70)
print("TradingAI - MARKET REGIME MODEL TEST")
print("=" * 70)


# ============================================================
# CONFIGURATION
# ============================================================

SYMBOL = "RELIANCE"

# Use the COMPLETE historical dataset.
#
# DO NOT use tail(1679), tail(2000), etc.
#
# The model needs the full chronological history.
USE_FULL_DATASET = True


# ============================================================
# TEST 1 - LOAD HISTORICAL DATA
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD HISTORICAL MARKET DATA")
print("=" * 70)

unified = UnifiedMarketData()

df = unified.get_stock_history(
    symbol=SYMBOL,
    source="eod2"
)

if df is None or df.empty:
    raise RuntimeError(
        "Historical market data could not be loaded."
    )

print(
    f"[REGIME] Historical rows: {len(df)}"
)


# ============================================================
# IMPORTANT DATA CHECK
# ============================================================

if not USE_FULL_DATASET:

    raise RuntimeError(
        "USE_FULL_DATASET must remain True."
    )


# ============================================================
# TEST 2 - BUILD REGIME DATASET
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD REGIME DATASET")
print("=" * 70)

dataset_builder = RegimeDataset()

regime_df = dataset_builder.build(
    df,
    symbol=SYMBOL
)

if regime_df is None or regime_df.empty:
    raise RuntimeError(
        "Regime dataset is empty."
    )


# ============================================================
# SAMPLE
# ============================================================

print("\n" + "=" * 70)
print("REGIME DATASET SAMPLE")
print("=" * 70)

sample_columns = [
    c
    for c in [
        "timestamp",
        "symbol",
        "close",
        "regime",
        "regime_target",
    ]
    if c in regime_df.columns
]

print(
    regime_df[
        sample_columns
    ]
    .head(10)
    .to_string(index=False)
)


# ============================================================
# TEST 3 - DATASET VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - DATASET VALIDATION")
print("=" * 70)

feature_columns = (
    RegimeDataset._feature_columns(
        regime_df
    )
)

print(
    f"Rows: {len(regime_df)}"
)

print(
    f"Columns: {len(regime_df.columns)}"
)

print(
    f"Regime features: "
    f"{len(feature_columns)}"
)

print(
    "\nREGIME DISTRIBUTION:"
)

print(
    regime_df["regime"]
    .value_counts()
    .reindex(
        ["BEAR", "BULL", "SIDEWAYS"],
        fill_value=0
    )
    .to_string()
)

print(
    "\nREGIME TARGET DISTRIBUTION:"
)

print(
    regime_df["regime_target"]
    .value_counts()
    .sort_index()
    .to_string()
)


# ============================================================
# TEST 4 - TRAIN MODEL
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - TRAIN REGIME MODEL")
print("=" * 70)

model = RegimeModel()

training_result = model.train(
    regime_df
)


# ============================================================
# TEST 5 - MODEL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - MODEL VALIDATION")
print("=" * 70)

print(
    f"Accuracy: "
    f"{training_result['accuracy']:.4f}"
)

print(
    f"Balanced accuracy: "
    f"{training_result['balanced_accuracy']:.4f}"
)

print(
    f"Train rows: "
    f"{training_result['train_rows']}"
)

print(
    f"Test rows: "
    f"{training_result['test_rows']}"
)

print(
    f"Features: "
    f"{training_result['feature_count']}"
)


# ============================================================
# TEST 6 - LOAD MODEL
# ============================================================

print("\n" + "=" * 70)
print("TEST 6 - LOAD REGIME MODEL")
print("=" * 70)

loaded_model = RegimeModel()

loaded_model.load()


# ============================================================
# TEST 7 - CURRENT REGIME
# ============================================================

print("\n" + "=" * 70)
print("TEST 7 - CURRENT REGIME PREDICTION")
print("=" * 70)

current_features = regime_df.tail(1)

prediction = loaded_model.predict(
    current_features
)

print(
    prediction.to_string(
        index=False
    )
)


# ============================================================
# FINAL STATUS
# ============================================================

print("\n" + "=" * 70)
print("MARKET REGIME MODEL TEST PASSED")
print("=" * 70)