# ============================================================
# TradingAI - DIRECTION MODEL TEST
# ============================================================

import pandas as pd

from data_engine.direction_model import DirectionModel


DATASET = (
    "market_data/processed/"
    "direction_reliance.parquet"
)


print("=" * 70)
print("TradingAI - DIRECTION MODEL TEST")
print("=" * 70)


# ============================================================
# LOAD DATASET
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD DATASET")
print("=" * 70)

df = pd.read_parquet(
    DATASET
)

print(
    f"Rows: {len(df)}"
)

print(
    f"Columns: {len(df.columns)}"
)

print(
    f"Target distribution:"
)

print(
    df["target"].value_counts()
)


# ============================================================
# TRAIN
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - TRAIN DIRECTION MODEL")
print("=" * 70)

model = DirectionModel()

result = model.train(
    df
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - VALIDATION")
print("=" * 70)

if result["accuracy"] < 0.45:

    raise RuntimeError(
        "Direction model accuracy is unexpectedly low."
    )

print(
    f"Accuracy: "
    f"{result['accuracy']:.4f}"
)

print(
    f"Train rows: "
    f"{result['train_rows']}"
)

print(
    f"Test rows: "
    f"{result['test_rows']}"
)

print(
    f"Features: "
    f"{result['feature_count']}"
)


# ============================================================
# TEST PREDICTION
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - PREDICTION")
print("=" * 70)

loaded_model = DirectionModel()

loaded_model.load()

latest = (
    df
    .tail(1)
    .copy()
)

prediction = loaded_model.predict(
    latest
)

print(
    prediction.to_string(
        index=False
    )
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("DIRECTION MODEL TEST PASSED")
print("=" * 70)