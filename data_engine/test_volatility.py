# ============================================================
# TradingAI - VOLATILITY MODEL TEST
# ============================================================

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.volatility_dataset import VolatilityDataset
from data_engine.volatility_model import VolatilityModel


print("=" * 70)
print("TradingAI - VOLATILITY MODEL TEST")
print("=" * 70)


# ============================================================
# CONFIGURATION
# ============================================================

SYMBOL = "RELIANCE"

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
    source="eod2",
)

if df is None or df.empty:
    raise RuntimeError(
        "Historical market data could not be loaded."
    )

print(
    f"[VOLATILITY] Historical rows: "
    f"{len(df)}"
)


if not USE_FULL_DATASET:

    raise RuntimeError(
        "USE_FULL_DATASET must remain True."
    )


# ============================================================
# TEST 2 - BUILD DATASET
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD VOLATILITY DATASET")
print("=" * 70)

dataset_builder = VolatilityDataset()

volatility_df = dataset_builder.build(
    df,
    symbol=SYMBOL,
)

if (
    volatility_df is None
    or volatility_df.empty
):

    raise RuntimeError(
        "Volatility dataset is empty."
    )


# ============================================================
# SAMPLE
# ============================================================

print("\n" + "=" * 70)
print("VOLATILITY DATASET SAMPLE")
print("=" * 70)

sample_columns = [
    c
    for c in [
        "timestamp",
        "symbol",
        "close",
        "future_volatility",
        "volatility_target",
        "volatility_regime",
    ]
    if c in volatility_df.columns
]

print(
    volatility_df[
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
    VolatilityDataset._feature_columns(
        volatility_df
    )
)

print(
    f"Rows: {len(volatility_df)}"
)

print(
    f"Columns: {len(volatility_df.columns)}"
)

print(
    f"Volatility features: "
    f"{len(feature_columns)}"
)


# ------------------------------------------------------------
# Target statistics
# ------------------------------------------------------------

if "volatility_target" in volatility_df.columns:

    print(
        "\nVOLATILITY TARGET STATISTICS:"
    )

    print(
        volatility_df[
            "volatility_target"
        ]
        .describe()
        .to_string()
    )


# ------------------------------------------------------------
# Regime distribution
# ------------------------------------------------------------

print(
    "\nVOLATILITY REGIME DISTRIBUTION:"
)

print(
    volatility_df[
        "volatility_regime"
    ]
    .value_counts()
    .reindex(
        [
            "LOW",
            "NORMAL",
            "HIGH",
        ],
        fill_value=0,
    )
    .to_string()
)


# ============================================================
# TEST 4 - TRAIN MODEL
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - TRAIN VOLATILITY MODEL")
print("=" * 70)

model = VolatilityModel()

training_result = model.train(
    volatility_df
)


# ============================================================
# TEST 5 - MODEL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - MODEL VALIDATION")
print("=" * 70)

print(
    f"MAE: "
    f"{training_result['mae']:.6f}"
)

print(
    f"RMSE: "
    f"{training_result['rmse']:.6f}"
)

print(
    f"R²: "
    f"{training_result['r2']:.4f}"
)

print(
    f"Regime accuracy: "
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
print("TEST 6 - LOAD VOLATILITY MODEL")
print("=" * 70)

loaded_model = VolatilityModel()

loaded_model.load()


# ============================================================
# TEST 7 - CURRENT VOLATILITY
# ============================================================

print("\n" + "=" * 70)
print("TEST 7 - CURRENT VOLATILITY PREDICTION")
print("=" * 70)

current_features = (
    volatility_df.tail(1)
)

prediction = loaded_model.predict(
    current_features
)

print(
    prediction.to_string(
        index=False
    )
)


# ============================================================
# TEST 8 - PREDICTION SANITY CHECK
# ============================================================

print("\n" + "=" * 70)
print("TEST 8 - PREDICTION SANITY CHECK")
print("=" * 70)

latest = prediction.iloc[0]

probabilities = [
    float(latest["low_probability"]),
    float(latest["normal_probability"]),
    float(latest["high_probability"]),
]

probability_sum = sum(
    probabilities
)

if abs(
    probability_sum - 1.0
) > 0.01:

    raise RuntimeError(
        "Volatility probabilities do not sum to 1."
    )


predicted_volatility = float(
    latest["predicted_volatility"]
)

if predicted_volatility < 0:

    raise RuntimeError(
        "Predicted volatility cannot be negative."
    )


if (
    latest["volatility_regime"]
    not in [
        "LOW",
        "NORMAL",
        "HIGH",
    ]
):

    raise RuntimeError(
        "Invalid volatility regime."
    )


print(
    f"[VOLATILITY] Probability sum: "
    f"{probability_sum:.6f}"
)

print(
    f"[VOLATILITY] Predicted volatility: "
    f"{predicted_volatility:.6f}"
)

print(
    f"[VOLATILITY] Regime: "
    f"{latest['volatility_regime']}"
)

print(
    f"[VOLATILITY] Confidence: "
    f"{float(latest['confidence']):.4f}"
)

print(
    f"[VOLATILITY] Confidence level: "
    f"{latest['confidence_level']}"
)


# ============================================================
# FINAL STATUS
# ============================================================

print("\n" + "=" * 70)
print("VOLATILITY MODEL TEST PASSED")
print("=" * 70)