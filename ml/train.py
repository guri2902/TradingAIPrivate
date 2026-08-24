import os
import sys
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix
)

from sklearn.utils.class_weight import compute_sample_weight

from ml.features import (
    create_features,
    FEATURE_COLUMNS
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "ml",
    "models"
)

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "market_direction_model.pkl"
)


# =========================================================
# CONFIG
# =========================================================

HORIZON = 5

THRESHOLD = 0.001

ATR_MULTIPLIER = 0.50


# =========================================================
# CREATE TARGET
# =========================================================

def create_target(
    df,
    horizon=HORIZON,
    threshold=THRESHOLD,
    atr_multiplier=ATR_MULTIPLIER
):

    data = df.copy()

    # -----------------------------------------------------
    # FUTURE PRICE
    # -----------------------------------------------------

    future_price = (
        data["close"]
        .shift(-horizon)
    )

    # -----------------------------------------------------
    # FUTURE RETURN
    # -----------------------------------------------------

    future_return = (
        future_price -
        data["close"]
    ) / data["close"]

    # -----------------------------------------------------
    # DYNAMIC THRESHOLD
    # -----------------------------------------------------

    if "atr_percent" in data.columns:

        dynamic_threshold = np.maximum(
            threshold,
            data["atr_percent"] *
            atr_multiplier
        )

    else:

        dynamic_threshold = threshold

    # -----------------------------------------------------
    # DEFAULT = SIDEWAYS
    #
    # 0 = DOWN
    # 1 = SIDEWAYS
    # 2 = UP
    # -----------------------------------------------------

    data["target"] = 1

    # DOWN
    data.loc[
        future_return <
        -dynamic_threshold,
        "target"
    ] = 0

    # UP
    data.loc[
        future_return >
        dynamic_threshold,
        "target"
    ] = 2

    return data


# =========================================================
# TRAIN MODEL
# =========================================================

def train_model(csv_file):

    print()
    print("=" * 70)
    print("TRADINGAI ML MODEL")
    print("=" * 70)

    # =====================================================
    # CHECK FILE
    # =====================================================

    if not os.path.exists(csv_file):

        print()
        print(
            "ERROR: CSV file not found:"
        )

        print(
            csv_file
        )

        raise SystemExit(1)

    # =====================================================
    # LOAD DATA
    # =====================================================

    df = pd.read_csv(
        csv_file
    )

    print()
    print(
        f"Loaded rows: {len(df):,}"
    )

    # =====================================================
    # NORMALIZE COLUMN NAMES
    # =====================================================

    df.columns = [
        str(column)
        .strip()
        .lower()
        for column in df.columns
    ]

    # =====================================================
    # REQUIRED COLUMNS
    # =====================================================

    required_columns = [
        "open",
        "high",
        "low",
        "close"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            f"{missing_columns}"
        )

    # =====================================================
    # DATETIME
    # =====================================================

    if "datetime" in df.columns:

        print()
        print(
            "Processing datetime..."
        )

        df["datetime"] = pd.to_datetime(
            df["datetime"],
            errors="coerce",
            utc=True
        )

        df = df.dropna(
            subset=["datetime"]
        )

        # UTC -> IST
        df["datetime"] = (
            df["datetime"]
            .dt.tz_convert(
                "Asia/Kolkata"
            )
        )

        df = (
            df
            .sort_values(
                "datetime"
            )
            .reset_index(
                drop=True
            )
        )

        print(
            "Date range:"
        )

        print(
            f"  {df['datetime'].iloc[0]}"
        )

        print(
            f"  {df['datetime'].iloc[-1]}"
        )

    # =====================================================
    # NUMERIC DATA
    # =====================================================

    numeric_columns = [
        "open",
        "high",
        "low",
        "close"
    ]

    if "volume" in df.columns:

        numeric_columns.append(
            "volume"
        )

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=[
            "open",
            "high",
            "low",
            "close"
        ]
    )

    df = df.reset_index(
        drop=True
    )

    print()
    print(
        f"Rows after OHLC cleaning: "
        f"{len(df):,}"
    )

    # =====================================================
    # FEATURES
    # =====================================================

    print()
    print(
        "Creating features..."
    )

    df = create_features(
        df
    )

    print(
        f"Rows after features: "
        f"{len(df):,}"
    )

    # =====================================================
    # TARGET
    # =====================================================

    print()
    print(
        "Creating target..."
    )

    df = create_target(
        df
    )

    print(
        f"Rows after target: "
        f"{len(df):,}"
    )

    # =====================================================
    # TARGET DISTRIBUTION
    # =====================================================

    print()
    print(
        "Target distribution BEFORE cleaning:"
    )

    print(
        df["target"]
        .value_counts()
        .sort_index()
        .rename(
            index={
                0: "DOWN",
                1: "SIDEWAYS",
                2: "UP"
            }
        )
    )

    # =====================================================
    # REMOVE FUTURE ROWS
    # =====================================================

    df = df.iloc[
        :-HORIZON
    ].copy()

    print()
    print(
        "Rows after removing future-target rows:"
    )

    print(
        f"{len(df):,}"
    )

    # =====================================================
    # DETERMINE AVAILABLE FEATURES
    # =====================================================

    print()
    print(
        "Checking ML features..."
    )

    available_features = []

    unavailable_features = []

    for feature in FEATURE_COLUMNS:

        if feature not in df.columns:

            unavailable_features.append(
                feature
            )

            continue

        # Number of valid values
        valid_count = (
            df[feature]
            .notna()
            .sum()
        )

        # If feature has ZERO usable values,
        # don't use it.
        if valid_count == 0:

            unavailable_features.append(
                feature
            )

        else:

            available_features.append(
                feature
            )

    # =====================================================
    # SHOW REMOVED FEATURES
    # =====================================================

    if unavailable_features:

        print()
        print(
            "Unavailable features:"
        )

        for feature in unavailable_features:

            print(
                f"  - {feature}"
            )

    print()
    print(
        f"Available features: "
        f"{len(available_features)}"
    )

    print(
        f"Removed features: "
        f"{len(unavailable_features)}"
    )

    # =====================================================
    # CREATE X / Y
    # =====================================================

    X = df[
        available_features
    ].copy()

    y = df[
        "target"
    ].astype(int)

    # =====================================================
    # CLEAN INFINITE VALUES
    # =====================================================

    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # =====================================================
    # DROP ONLY ROWS WITH MISSING FEATURES
    #
    # This removes the initial indicator warm-up rows.
    # =====================================================

    valid_rows = X.notna().all(
        axis=1
    )

    X = X.loc[
        valid_rows
    ].reset_index(
        drop=True
    )

    y = y.loc[
        valid_rows
    ].reset_index(
        drop=True
    )

    # =====================================================
    # FINAL DATASET
    # =====================================================

    print()
    print(
        f"Final feature rows: "
        f"{len(X):,}"
    )

    if len(X) == 0:

        print()
        print(
            "ERROR: Training dataset is empty."
        )

        print()
        print(
            "NaN count by feature:"
        )

        print(
            df[
                available_features
            ]
            .isna()
            .sum()
            .sort_values(
                ascending=False
            )
            .head(30)
        )

        raise ValueError(
            "Training dataset is empty."
        )

    # =====================================================
    # CLASS DISTRIBUTION
    # =====================================================

    print()
    print(
        "Final class distribution:"
    )

    print(
        y.value_counts()
        .sort_index()
        .rename(
            index={
                0: "DOWN",
                1: "SIDEWAYS",
                2: "UP"
            }
        )
    )

    # =====================================================
    # TIME SPLIT
    # =====================================================

    split = int(
        len(X) * 0.80
    )

    X_train = X.iloc[
        :split
    ].copy()

    X_test = X.iloc[
        split:
    ].copy()

    y_train = y.iloc[
        :split
    ].copy()

    y_test = y.iloc[
        split:
    ].copy()

    print()
    print(
        f"Training rows: "
        f"{len(X_train):,}"
    )

    print(
        f"Testing rows : "
        f"{len(X_test):,}"
    )

    # =====================================================
    # CHECK
    # =====================================================

    if len(X_train) == 0:

        raise ValueError(
            "Training dataset is empty."
        )

    if len(X_test) == 0:

        raise ValueError(
            "Testing dataset is empty."
        )

    # =====================================================
    # TRAINING CLASS DISTRIBUTION
    # =====================================================

    print()
    print(
        "Training classes:"
    )

    print(
        y_train
        .value_counts()
        .sort_index()
        .rename(
            index={
                0: "DOWN",
                1: "SIDEWAYS",
                2: "UP"
            }
        )
    )

    # =====================================================
    # SAMPLE WEIGHTS
    # =====================================================

    sample_weights = (
        compute_sample_weight(
            class_weight="balanced",
            y=y_train
        )
    )

    # =====================================================
    # MODEL
    # =====================================================

    model = HistGradientBoostingClassifier(

        max_iter=400,

        learning_rate=0.04,

        max_leaf_nodes=31,

        min_samples_leaf=30,

        l2_regularization=2.0,

        random_state=42
    )

    # =====================================================
    # TRAIN
    # =====================================================

    print()
    print(
        "Training..."
    )

    model.fit(
        X_train,
        y_train,
        sample_weight=sample_weights
    )

    # =====================================================
    # PREDICTION
    # =====================================================

    predictions = model.predict(
        X_test
    )

    probabilities = model.predict_proba(
        X_test
    )

    # =====================================================
    # METRICS
    # =====================================================

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    balanced_accuracy = (
        balanced_accuracy_score(
            y_test,
            predictions
        )
    )

    print()
    print("=" * 70)

    print(
        f"Accuracy          : "
        f"{accuracy * 100:.2f}%"
    )

    print(
        f"Balanced Accuracy : "
        f"{balanced_accuracy * 100:.2f}%"
    )

    print("=" * 70)

    # =====================================================
    # CLASSIFICATION REPORT
    # =====================================================

    print()
    print(
        "Classification Report:"
    )

    print()

    print(
        classification_report(
            y_test,
            predictions,
            labels=[
                0,
                1,
                2
            ],
            target_names=[
                "DOWN",
                "SIDEWAYS",
                "UP"
            ],
            zero_division=0
        )
    )

    # =====================================================
    # CONFUSION MATRIX
    # =====================================================

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=[
            0,
            1,
            2
        ]
    )

    print(
        "Confusion Matrix:"
    )

    print()

    print(
        "             DOWN  SIDEWAYS  UP"
    )

    print(
        f"DOWN       "
        f"{matrix[0][0]:6d}"
        f"{matrix[0][1]:10d}"
        f"{matrix[0][2]:5d}"
    )

    print(
        f"SIDEWAYS   "
        f"{matrix[1][0]:6d}"
        f"{matrix[1][1]:10d}"
        f"{matrix[1][2]:5d}"
    )

    print(
        f"UP         "
        f"{matrix[2][0]:6d}"
        f"{matrix[2][1]:10d}"
        f"{matrix[2][2]:5d}"
    )

    # =====================================================
    # CONFIDENCE
    # =====================================================

    average_confidence = (
        probabilities
        .max(axis=1)
        .mean()
    )

    print()
    print(
        "Average model confidence:"
    )

    print(
        f"{average_confidence * 100:.2f}%"
    )

    # =====================================================
    # MODEL CLASSES
    # =====================================================

    print()
    print(
        "Model classes:"
    )

    print(
        model.classes_
    )

    # =====================================================
    # SAVE MODEL
    # =====================================================

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    payload = {

        "model": model,

        # IMPORTANT:
        # Save ONLY the features actually used.
        "features": available_features,

        "classes": {
            0: "DOWN",
            1: "SIDEWAYS",
            2: "UP"
        },

        "horizon": HORIZON,

        "threshold": THRESHOLD,

        "atr_multiplier":
            ATR_MULTIPLIER
    }

    joblib.dump(
        payload,
        MODEL_FILE
    )

    # =====================================================
    # DONE
    # =====================================================

    print()
    print("=" * 70)

    print(
        "MODEL SAVED SUCCESSFULLY"
    )

    print(
        MODEL_FILE
    )

    print("=" * 70)

    print()


# =========================================================
# COMMAND LINE
# =========================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print()
        print(
            "Usage:"
        )

        print()

        print(
            "python -m ml.train "
            "historical_data/nifty_5m_spot_6m.csv"
        )

        print()

        raise SystemExit(1)

    train_model(
        sys.argv[1]
    )