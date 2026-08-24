# ============================================================
# TradingAI - FAST NIFTY ML TRAINING
# Source: jugaad-data NIFTY historical data
# ============================================================

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "ml_data",
    "nifty",
    "nifty_2025-01-01_2026-08-17.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "ml_models"
)

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "nifty_direction_model.pkl"
)

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

FUTURE_BARS = 3

UP_THRESHOLD = 0.001
DOWN_THRESHOLD = -0.001


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "return_1",
    "return_3",
    "return_5",
    "return_10",

    "range_pct",
    "body_pct",
    "upper_wick",
    "lower_wick",

    "close_vs_sma5",
    "close_vs_sma20",

    "ema5_vs_ema20",

    "volatility_5",
    "volatility_10",
    "volatility_20",
]


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("TradingAI - FAST NIFTY ML TRAINING")
print("=" * 70)

print("\nLoading:")
print(DATA_FILE)

if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(DATA_FILE)

df = pd.read_csv(DATA_FILE)

print("\nRaw rows:", len(df))

# ============================================================
# NORMALIZE
# ============================================================

df["timestamp"] = pd.to_datetime(
    df["HistoricalDate"],
    errors="coerce"
)

for col in [
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE"
]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = (
    df.sort_values("timestamp")
      .drop_duplicates("timestamp")
      .reset_index(drop=True)
)


# ============================================================
# FEATURES
# ============================================================

print("\nCreating features...")


df["return_1"] = df["CLOSE"].pct_change(1)
df["return_3"] = df["CLOSE"].pct_change(3)
df["return_5"] = df["CLOSE"].pct_change(5)
df["return_10"] = df["CLOSE"].pct_change(10)


df["range"] = df["HIGH"] - df["LOW"]

df["range_pct"] = (
    df["range"] / df["CLOSE"]
)


df["body"] = (
    df["CLOSE"] - df["OPEN"]
)

df["body_pct"] = (
    df["body"] / df["OPEN"]
)


df["upper_wick"] = (
    df["HIGH"]
    - df[["OPEN", "CLOSE"]].max(axis=1)
)

df["lower_wick"] = (
    df[["OPEN", "CLOSE"]].min(axis=1)
    - df["LOW"]
)


# ============================================================
# MOVING AVERAGES
# ============================================================

df["sma_5"] = (
    df["CLOSE"]
    .rolling(5)
    .mean()
)

df["sma_20"] = (
    df["CLOSE"]
    .rolling(20)
    .mean()
)


df["ema_5"] = (
    df["CLOSE"]
    .ewm(
        span=5,
        adjust=False
    )
    .mean()
)

df["ema_20"] = (
    df["CLOSE"]
    .ewm(
        span=20,
        adjust=False
    )
    .mean()
)


df["close_vs_sma5"] = (
    df["CLOSE"] /
    df["sma_5"] - 1
)

df["close_vs_sma20"] = (
    df["CLOSE"] /
    df["sma_20"] - 1
)

df["ema5_vs_ema20"] = (
    df["ema_5"] /
    df["ema_20"] - 1
)


# ============================================================
# VOLATILITY
# ============================================================

df["volatility_5"] = (
    df["return_1"]
    .rolling(5)
    .std()
)

df["volatility_10"] = (
    df["return_1"]
    .rolling(10)
    .std()
)

df["volatility_20"] = (
    df["return_1"]
    .rolling(20)
    .std()
)


# ============================================================
# TARGET
# ============================================================

df["future_close"] = (
    df["CLOSE"]
    .shift(-FUTURE_BARS)
)

df["future_return"] = (
    df["future_close"] /
    df["CLOSE"] - 1
)


def create_target(value):

    if pd.isna(value):
        return np.nan

    if value >= UP_THRESHOLD:
        return 1

    if value <= DOWN_THRESHOLD:
        return -1

    return 0


df["target"] = (
    df["future_return"]
    .apply(create_target)
)


# ============================================================
# DATASET
# ============================================================

model_df = df[
    FEATURES + ["target"]
].copy()

model_df = (
    model_df
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
    .dropna()
)


print("\nFeature count:", len(FEATURES))
print("Usable rows:", len(model_df))


if len(model_df) < 100:

    raise RuntimeError(
        f"Only {len(model_df)} usable rows. "
        "Need more historical data."
    )


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print("\nTarget distribution:")

print(
    model_df["target"]
    .value_counts()
    .sort_index()
)


# ============================================================
# TIME SPLIT
# ============================================================

X = model_df[FEATURES]

y = (
    model_df["target"]
    .astype(int)
)


split = int(
    len(X) * 0.80
)

X_train = X.iloc[:split]
X_test = X.iloc[split:]

y_train = y.iloc[:split]
y_test = y.iloc[split:]


print("\nTraining rows:", len(X_train))
print("Testing rows :", len(X_test))


# ============================================================
# MODEL
# ============================================================

print("\nTraining model...")

model = HistGradientBoostingClassifier(
    max_iter=200,
    learning_rate=0.05,
    max_leaf_nodes=15,
    min_samples_leaf=8,
    l2_regularization=1.0,
    random_state=42
)

model.fit(
    X_train,
    y_train
)


# ============================================================
# TEST
# ============================================================

pred = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    pred
)


print("\n" + "=" * 70)
print("MODEL RESULTS")
print("=" * 70)

print(
    f"\nAccuracy: {accuracy:.2%}"
)

print("\nClassification report:")

print(
    classification_report(
        y_test,
        pred,
        labels=[-1, 0, 1],
        target_names=[
            "DOWN",
            "NEUTRAL",
            "UP"
        ],
        zero_division=0
    )
)


# ============================================================
# SAVE EVERYTHING TO ONE FILE
# ============================================================

artifact = {

    "model": model,

    "features": FEATURES,

    "future_bars": FUTURE_BARS,

    "up_threshold": UP_THRESHOLD,

    "down_threshold": DOWN_THRESHOLD,

    "classes": {
        -1: "DOWN",
        0: "NEUTRAL",
        1: "UP"
    },

    "accuracy": float(accuracy),

    "trained_rows": len(X_train),

    "test_rows": len(X_test)
}


joblib.dump(
    artifact,
    MODEL_FILE
)


print("\nModel saved:")
print(MODEL_FILE)

print("\nTraining complete.")