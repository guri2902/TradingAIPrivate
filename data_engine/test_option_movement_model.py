# ============================================================
# TradingAI - OPTION MOVEMENT MODEL TEST
# ============================================================

from pathlib import Path
import pandas as pd

from data_engine.option_movement_model import (
    OptionMovementModel,
)


BASE_DIR = Path(
    __file__
).resolve().parent.parent

DATASET_PATH = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "option_movement_nifty.parquet"
)


print("=" * 70)
print(
    "TradingAI - OPTION MOVEMENT MODEL TEST"
)
print("=" * 70)


# ============================================================
# TEST 1 - LOAD DATASET
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD OPTION MOVEMENT DATASET")
print("=" * 70)

if not DATASET_PATH.exists():

    raise RuntimeError(
        f"Dataset not found: {DATASET_PATH}"
    )

df = pd.read_parquet(
    DATASET_PATH
)

print(
    f"Rows: {len(df)}"
)

print(
    f"Columns: {len(df.columns)}"
)

print(
    f"Snapshots: "
    f"{df['timestamp'].nunique()}"
)

print(
    "\nTarget distribution:"
)

print(
    df["target"]
    .value_counts()
    .sort_index()
)


# ============================================================
# TEST 2 - DATA VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - VALIDATE TRAINING DATA")
print("=" * 70)

required_columns = [
    "timestamp",
    "symbol",
    "expiry",
    "strike",
    "option_type",
    "last_price",
    "future_last_price",
    "premium_change",
    "premium_return",
    "target",
]

missing = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing:

    raise RuntimeError(
        f"Missing required columns: {missing}"
    )

if df["target"].nunique() < 2:

    raise RuntimeError(
        "Not enough target classes for training."
    )

non_zero = (
    df["premium_return"]
    .abs()
    .gt(1e-12)
    .sum()
)

print(
    f"Non-zero premium returns: {non_zero}"
)

if non_zero == 0:

    raise RuntimeError(
        "No real option movement detected."
    )

print(
    "Training dataset validation passed."
)

print(
    "\nSelected raw dataset columns:"
)

leakage_columns = {
    "future_last_price",
    "future_premium",
    "future_premium_return",
    "premium_return",
    "premium_change",
    "target",
    "movement_target",
    "movement",
}

feature_candidates = [
    c
    for c in df.columns
    if c not in leakage_columns
    and pd.api.types.is_numeric_dtype(df[c])
]

print(
    "Potential leakage columns excluded:"
)
print(
    sorted(
        leakage_columns
        & set(df.columns)
    )
)
# ============================================================
# TEST 3 - TRAIN MODEL
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - TRAIN OPTION MOVEMENT MODEL")
print("=" * 70)

model = OptionMovementModel()

metrics = model.train(
    df
)


# ============================================================
# TEST 4 - METRICS
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - MODEL METRICS")
print("=" * 70)

for key, value in metrics.items():

    print(
        f"{key}: {value}"
    )


# ============================================================
# TEST 5 - LOAD MODEL
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - RELOAD SAVED MODEL")
print("=" * 70)

loaded_model = (
    OptionMovementModel()
)

loaded_model.load()

print(
    f"Feature count: "
    f"{len(loaded_model.feature_columns)}"
)


# ============================================================
# TEST 6 - PREDICTION
# ============================================================

print("\n" + "=" * 70)
print("TEST 6 - RUN SAMPLE PREDICTIONS")
print("=" * 70)

sample = df.tail(
    min(10, len(df))
).copy()

predictions = (
    loaded_model.predict(
        sample
    )
)

print(
    predictions.to_string(
        index=False
    )
)


# ============================================================
# TEST 7 - OUTPUT SANITY
# ============================================================

print("\n" + "=" * 70)
print("TEST 7 - OUTPUT SANITY")
print("=" * 70)

prediction_column = "movement_prediction"

if prediction_column not in predictions.columns:

    raise RuntimeError(
        f"Missing prediction column: "
        f"{prediction_column}"
    )

valid_labels = {
    "DOWN",
    "SIDEWAYS",
    "UP",
}

actual_predictions = set(
    predictions[
        prediction_column
    ]
    .astype(str)
    .str.upper()
    .unique()
)

unexpected = (
    actual_predictions
    - valid_labels
)

if unexpected:

    raise RuntimeError(
        f"Unexpected prediction labels: "
        f"{unexpected}"
    )

print(
    "Prediction labels are valid:"
)

print(
    sorted(
        actual_predictions
    )
)

print(
    "Prediction probabilities are valid."
)

probability_columns = [
    "down_probability",
    "sideways_probability",
    "up_probability",
]

for column in probability_columns:

    if column not in predictions.columns:

        raise RuntimeError(
            f"Missing probability column: "
            f"{column}"
        )

    values = pd.to_numeric(
        predictions[column],
        errors="coerce",
    )

    if values.isna().any():

        raise RuntimeError(
            f"Invalid probability values in "
            f"{column}"
        )

    if (
        (values < 0).any()
        or (values > 1).any()
    ):

        raise RuntimeError(
            f"Probability out of range in "
            f"{column}"
        )

# Probability rows should approximately sum to 1.
probability_sum = (
    predictions[
        probability_columns
    ].sum(axis=1)
)

if not (
    probability_sum
    .between(
        0.999,
        1.001,
    )
    .all()
):

    raise RuntimeError(
        "Prediction probabilities do not "
        "sum to approximately 1."
    )

print(
    "Probability sums validated."
)

print(
    "Output sanity validation passed."
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print(
    "OPTION MOVEMENT MODEL TEST PASSED"
)
print("=" * 70)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print(
    "OPTION MOVEMENT MODEL TEST PASSED"
)
print("=" * 70)