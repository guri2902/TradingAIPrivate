# ============================================================
# TradingAI - DIRECTION MODEL
# ============================================================

from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


class DirectionModel:

    def __init__(
        self,
        model_dir="market_data/models"
    ):

        self.model_dir = Path(model_dir)

        self.model_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.model = None
        self.feature_columns = []

    # ========================================================
    # TRAIN
    # ========================================================

    def train(
        self,
        df,
        target_column="target"
    ):

        if df is None or df.empty:
            raise ValueError(
                "Direction dataset is empty."
            )

        df = df.copy()

        if target_column not in df.columns:
            raise ValueError(
                f"Missing target column: {target_column}"
            )

        # ----------------------------------------------------
        # Remove non-feature columns
        # ----------------------------------------------------

        excluded_columns = {
            target_column,
            "timestamp",
            "symbol",
            "source",
            "date",
            "next_close",
        }

        feature_columns = [
            column
            for column in df.columns
            if column not in excluded_columns
        ]

        # ----------------------------------------------------
        # Keep numeric features only
        # ----------------------------------------------------

        feature_columns = [
            column
            for column in feature_columns
            if pd.api.types.is_numeric_dtype(
                df[column]
            )
        ]

        if not feature_columns:
            raise ValueError(
                "No numeric features available."
            )

        self.feature_columns = feature_columns

        X = df[feature_columns].copy()
        y = df[target_column].copy()

        # ----------------------------------------------------
        # Remove invalid rows
        # ----------------------------------------------------

        valid_rows = (
            X.notna().all(axis=1)
            & y.notna()
        )

        X = X.loc[valid_rows]
        y = y.loc[valid_rows]

        if len(X) < 100:
            raise ValueError(
                "Not enough valid rows to train."
            )

        # ----------------------------------------------------
        # Chronological split
        #
        # IMPORTANT:
        # No random shuffle for market data.
        # ----------------------------------------------------

        split_index = int(
            len(X) * 0.80
        )

        X_train = X.iloc[:split_index]
        y_train = y.iloc[:split_index]

        X_test = X.iloc[split_index:]
        y_test = y.iloc[split_index:]

        print(
            f"[DIRECTION] Training rows: "
            f"{len(X_train)}"
        )

        print(
            f"[DIRECTION] Testing rows: "
            f"{len(X_test)}"
        )

        print(
            f"[DIRECTION] Features: "
            f"{len(feature_columns)}"
        )

        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------

        self.model = RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        )

        print(
            "[DIRECTION] Training Random Forest..."
        )

        self.model.fit(
            X_train,
            y_train
        )

        # ----------------------------------------------------
        # TEST
        # ----------------------------------------------------

        predictions = self.model.predict(
            X_test
        )

        probabilities = self.model.predict_proba(
            X_test
        )

        accuracy = accuracy_score(
            y_test,
            predictions
        )

        print(
            f"\n[DIRECTION] Accuracy: "
            f"{accuracy:.4f}"
        )

        print(
            "\n[DIRECTION] Classification report:"
        )

        print(
            classification_report(
                y_test,
                predictions,
                zero_division=0
            )
        )

        print(
            "[DIRECTION] Confusion matrix:"
        )

        print(
            confusion_matrix(
                y_test,
                predictions
            )
        )

        # ----------------------------------------------------
        # FEATURE IMPORTANCE
        # ----------------------------------------------------

        importance = pd.DataFrame({
            "feature": feature_columns,
            "importance": self.model.feature_importances_,
        })

        importance = (
            importance
            .sort_values(
                "importance",
                ascending=False
            )
            .reset_index(drop=True)
        )

        print(
            "\n[DIRECTION] Top features:"
        )

        print(
            importance.head(15).to_string(
                index=False
            )
        )

        # ----------------------------------------------------
        # SAVE MODEL
        # ----------------------------------------------------

        model_path = (
            self.model_dir
            / "direction_model.pkl"
        )

        metadata_path = (
            self.model_dir
            / "direction_model_features.parquet"
        )

        joblib.dump(
            self.model,
            model_path
        )

        pd.DataFrame({
            "feature": feature_columns
        }).to_parquet(
            metadata_path,
            index=False
        )

        print(
            f"\n[DIRECTION] Model saved: "
            f"{model_path}"
        )

        print(
            f"[DIRECTION] Features saved: "
            f"{metadata_path}"
        )

        return {
            "accuracy": accuracy,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "feature_count": len(feature_columns),
            "predictions": predictions,
            "probabilities": probabilities,
            "importance": importance,
        }

    # ========================================================
    # LOAD
    # ========================================================

    def load(self):

        model_path = (
            self.model_dir
            / "direction_model.pkl"
        )

        metadata_path = (
            self.model_dir
            / "direction_model_features.parquet"
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}"
            )

        self.model = joblib.load(
            model_path
        )

        if metadata_path.exists():

            features = pd.read_parquet(
                metadata_path
            )

            self.feature_columns = (
                features["feature"]
                .tolist()
            )

        print(
            f"[DIRECTION] Model loaded: "
            f"{model_path}"
        )

        return self

    # ========================================================
    # PREDICT
    # ========================================================

    def predict(self, df):

        if self.model is None:
            raise RuntimeError(
                "Model is not loaded or trained."
            )

        if not self.feature_columns:
            raise RuntimeError(
                "Feature columns are not available."
            )

        X = df[
            self.feature_columns
        ].copy()

        X = X.fillna(0)

        prediction = self.model.predict(
            X
        )

        probabilities = (
            self.model.predict_proba(X)
        )

        result = pd.DataFrame({
            "prediction": prediction,
            "down_probability": probabilities[:, 0],
            "up_probability": probabilities[:, 1],
        })

        return result