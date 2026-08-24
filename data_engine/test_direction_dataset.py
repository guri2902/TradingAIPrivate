# ============================================================
# TradingAI - DIRECTION DATASET TEST
# ============================================================

from data_engine.direction_dataset import DirectionDataset


print("=" * 70)
print("TradingAI - DIRECTION MODEL DATASET TEST")
print("=" * 70)


dataset_builder = DirectionDataset()


# ============================================================
# BUILD
# ============================================================

df = dataset_builder.build(
    symbol="RELIANCE",
    source="eod2"
)


# ============================================================
# BASIC VALIDATION
# ============================================================

if df.empty:
    raise RuntimeError(
        "Direction dataset is empty"
    )


required_columns = [
    "timestamp",
    "symbol",
    "close",
    "next_close",
    "target",
]


missing = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing:
    raise RuntimeError(
        f"Missing columns: {missing}"
    )


# ============================================================
# TARGET VALIDATION
# ============================================================

invalid_targets = set(
    df["target"].dropna().unique()
) - {0, 1}


if invalid_targets:
    raise RuntimeError(
        f"Invalid target values: {invalid_targets}"
    )


# ============================================================
# TIME ORDER VALIDATION
# ============================================================

if not df["timestamp"].is_monotonic_increasing:
    raise RuntimeError(
        "Dataset is not chronologically sorted"
    )


# ============================================================
# LEAKAGE CHECK
# ============================================================

for i in range(len(df) - 1):

    current_close = df.iloc[i]["close"]
    next_close = df.iloc[i]["next_close"]

    expected_target = int(
        next_close > current_close
    )

    actual_target = int(
        df.iloc[i]["target"]
    )

    if actual_target != expected_target:
        raise RuntimeError(
            f"Target mismatch at row {i}"
        )


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 70)
print("DATASET SAMPLE")
print("=" * 70)

print(
    df[
        [
            "timestamp",
            "symbol",
            "close",
            "next_close",
            "target",
        ]
    ].head(10)
)


print()
print("=" * 70)
print("DATASET VALIDATION")
print("=" * 70)

print(
    f"Rows: {len(df)}"
)

print(
    f"Columns: {len(df.columns)}"
)

print(
    f"UP: {(df['target'] == 1).sum()}"
)

print(
    f"DOWN: {(df['target'] == 0).sum()}"
)

print(
    f"Start: {df['timestamp'].min()}"
)

print(
    f"End: {df['timestamp'].max()}"
)


print()
print("=" * 70)
print("DIRECTION DATASET TEST PASSED")
print("=" * 70)