# ============================================================
# TradingAI - OPTION MOVEMENT DATASET TEST
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.option_movement_dataset import (
    OptionMovementDataset,
)


PATH = Path(
    "market_data/processed/nifty_option_history.parquet"
)


print("=" * 70)
print("TradingAI - OPTION MOVEMENT DATASET TEST")
print("=" * 70)


# ============================================================
# TEST 1 - LOAD HISTORY
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD OPTION CHAIN HISTORY")
print("=" * 70)

if not PATH.exists():
    raise RuntimeError(
        f"Option history not found: {PATH}"
    )

history = pd.read_parquet(PATH)

print(f"Rows: {len(history)}")
print(f"Columns: {len(history.columns)}")
print(
    f"Timestamps: "
    f"{history['timestamp'].nunique()}"
)

print(
    f"Start: {history['timestamp'].min()}"
)

print(
    f"End: {history['timestamp'].max()}"
)


# ============================================================
# TEST 2 - SNAPSHOT VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - SNAPSHOT VALIDATION")
print("=" * 70)

timestamps = (
    history["timestamp"]
    .drop_duplicates()
    .sort_values()
)

print("\nTIMESTAMP DISTRIBUTION:")
print(
    history.groupby("timestamp")
    .size()
    .to_string()
)

if len(timestamps) < 2:
    raise RuntimeError(
        "At least 2 option-chain snapshots are required."
    )

print(
    f"\nSnapshots available: {len(timestamps)}"
)


# ============================================================
# TEST 3 - BUILD DATASET
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - BUILD OPTION MOVEMENT DATASET")
print("=" * 70)

builder = OptionMovementDataset(
    output_dir="market_data/processed"
)

dataset = builder.build(
    history,
    symbol="NIFTY",
    horizon=1,
    min_snapshots=2,
)


# ============================================================
# TEST 4 - VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - DATASET VALIDATION")
print("=" * 70)

print(f"Rows: {len(dataset)}")
print(f"Columns: {len(dataset.columns)}")

if "movement_target" in dataset.columns:
    print("\nMOVEMENT TARGET:")
    print(
        dataset["movement_target"]
        .value_counts()
        .sort_index()
        .to_string()
    )

if "premium_return" in dataset.columns:
    print("\nPREMIUM RETURN:")
    print(
        dataset["premium_return"]
        .describe()
        .to_string()
    )


# ============================================================
# TEST 5 - OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - OUTPUT CHECK")
print("=" * 70)

output_path = Path(
    "market_data/processed/option_movement_nifty.parquet"
)

if not output_path.exists():
    raise RuntimeError(
        f"Dataset was not saved: {output_path}"
    )

saved = pd.read_parquet(output_path)

print(f"Saved: {output_path}")
print(f"Saved rows: {len(saved)}")
print(f"Saved columns: {len(saved.columns)}")


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("OPTION MOVEMENT DATASET TEST PASSED")
print("=" * 70)