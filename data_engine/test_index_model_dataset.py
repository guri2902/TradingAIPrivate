from data_engine.index_model_dataset import (
    IndexModelDataset,
)


print("=" * 70)
print(
    "TradingAI - INDEX MODEL DATASET TEST"
)
print("=" * 70)

builder = (
    IndexModelDataset()
)

df = (
    builder.build()
)

required = [
    "timestamp",
    "direction_target",
    "regime_target",
    "volatility_target",
]

missing = [
    column
    for column in required
    if column not in df.columns
]

if missing:

    raise RuntimeError(
        f"Missing dataset columns: {missing}"
    )

print(
    "\nDataset validation passed."
)

print(
    f"Rows: {len(df)}"
)

print(
    f"Features: "
    f"{len(builder.select_features(df))}"
)

print("\n" + "=" * 70)
print(
    "INDEX MODEL DATASET TEST PASSED"
)
print("=" * 70)