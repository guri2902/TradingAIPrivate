import os
import joblib
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report
)

from features import build_features


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "ml_data",
    "nifty",
    "nifty_2025-01-01_2026-08-17.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "nifty_daily_model.pkl"
)

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# ============================================================
# LOAD JUGAAD DATA
# ============================================================

print("=" * 70)
print("TRADINGAI ML TRAINING")
print("=" * 70)

print("\nLoading Jugaad-data dataset:")
print(DATA_FILE)

df = pd.read_csv(DATA_FILE)

print("\nRaw rows:", len(df))


# ============================================================
# FEATURES
# ============================================================

df = build_features(df)

print(
    "\nRows after feature generation:",
    len(df)
)


# ============================================================
# FEATURE LIST
# ============================================================

FEATURES = [
    "return_1d",
    "return_3d",
    "return_5d",
    "return_10d",

    "ema_12_distance",
    "ema_26_distance",

    "rsi",

    "macd",
    "macd_signal",
    "macd_hist",

    "atr_14",

    "volatility_10",

    "body_pct",
    "range_pct",

    "upper_wick",
    "lower_wick"
]


# ============================================================
# CLEAN
# ============================================================

df = df.replace(
    [float("inf"), float("-inf")],
    float("nan")
)

df = df.dropna(
    subset=FEATURES + ["target"]
)

print(
    "\nValid ML rows:",
    len(df)
)


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print("\nTarget distribution:")

print(
    df["target"]
    .value_counts()
    .sort_index()
)

print("\nTarget percentage:")

print(
    df["target"]
    .value_counts(
        normalize=True
    )
    .sort_index()
    .mul(100)
    .round(2)
)


# ============================================================
# SAFETY CHECK
# ============================================================

if len(df) < 100:

    raise RuntimeError(
        "Not enough valid rows for training."
    )


# ============================================================
# TIME SERIES SPLIT
# ============================================================

X = df[FEATURES]
y = df["target"]

split = int(
    len(df) * 0.80
)

X_train = X.iloc[:split]
X_test = X.iloc[split:]

y_train = y.iloc[:split]
y_test = y.iloc[split:]

print(
    "\nTraining rows:",
    len(X_train)
)

print(
    "Testing rows:",
    len(X_test)
)


# ============================================================
# TRAIN
# ============================================================

print("\nTraining model...")

model = HistGradientBoostingClassifier(
    max_iter=200,
    learning_rate=0.05,
    max_leaf_nodes=12,
    min_samples_leaf=10,
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

predictions = model.predict(
    X_test
)

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\n" + "=" * 70)
print("RESULT")
print("=" * 70)

print(
    f"\nAccuracy: {accuracy * 100:.2f}%"
)

print("\nClassification report:")

print(
    classification_report(
        y_test,
        predictions,
        labels=[-1, 0, 1],
        target_names=[
            "DOWN",
            "SIDEWAYS",
            "UP"
        ],
        zero_division=0
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

artifact = {
    "model": model,
    "features": FEATURES,
    "classes": {
        -1: "DOWN",
        0: "SIDEWAYS",
        1: "UP"
    }
}

joblib.dump(
    artifact,
    MODEL_FILE
)

print(
    "\nModel saved:"
)

print(MODEL_FILE)

print("\nTraining complete.")