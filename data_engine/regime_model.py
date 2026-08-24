# ============================================================
# TradingAI - MARKET REGIME MODEL
# ============================================================

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)


class RegimeModel:

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

        self.regime_names = {
            0: "BEAR",
            1: "SIDEWAYS",
            2: "BULL",
        }

        self.regime_order = [
            "BEAR",
            "SIDEWAYS",
            "BULL",
        ]

    # ========================================================
    # FEATURE SELECTION
    # ========================================================

    @staticmethod
    def _get_feature_columns(df, target_column):

        excluded = {
            target_column,
            "timestamp",
            "symbol",
            "source",
            "date",
            "series",

            # Target / label columns
            "regime",
            "future_close",
            "future_return_20",

            # Explicit leakage protection
            "regime_score",
            "regime_strength",
            "regime_trend_strength",
            "regime_prediction",
            "bear_probability",
            "sideways_probability",
            "bull_probability",
            "confidence",
            "confidence_margin",
        }

        columns = []

        for column in df.columns:

            if column in excluded:
                continue

            if not pd.api.types.is_numeric_dtype(
                df[column]
            ):
                continue

            columns.append(column)

        return columns

    # ========================================================
    # TRAIN
    # ========================================================

    def train(
        self,
        df,
        target_column="regime_target"
    ):

        if df is None or df.empty:
            raise ValueError(
                "Regime dataset is empty."
            )

        df = df.copy()

        if target_column not in df.columns:
            raise ValueError(
                f"Missing target column: {target_column}"
            )

        # ----------------------------------------------------
        # Sort chronologically
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            df["timestamp"] = pd.to_datetime(
                df["timestamp"]
            )

            df = (
                df
                .sort_values("timestamp")
                .reset_index(drop=True)
            )

        # ----------------------------------------------------
        # Feature selection
        # ----------------------------------------------------

        feature_columns = self._get_feature_columns(
            df,
            target_column
        )

        if not feature_columns:
            raise ValueError(
                "No numeric regime features found."
            )

        self.feature_columns = feature_columns

        X = df[feature_columns].copy()
        y = df[target_column].copy()

        # ----------------------------------------------------
        # Replace infinite values
        # ----------------------------------------------------

        X = X.replace(
            [np.inf, -np.inf],
            np.nan
        )

        # ----------------------------------------------------
        # Remove invalid rows
        # ----------------------------------------------------

        valid = (
            X.notna().all(axis=1)
            & y.notna()
        )

        X = X.loc[valid].reset_index(drop=True)
        y = y.loc[valid].reset_index(drop=True)

        if len(X) < 500:
            raise ValueError(
                "Not enough valid rows to train regime model."
            )

        # ----------------------------------------------------
        # Ensure all three classes exist
        # ----------------------------------------------------

        classes = sorted(
            y.astype(int).unique().tolist()
        )

        if classes != [0, 1, 2]:

            raise ValueError(
                "Training dataset must contain "
                "BEAR(0), SIDEWAYS(1), and BULL(2). "
                f"Found classes: {classes}"
            )

        # ----------------------------------------------------
        # Overall distribution
        # ----------------------------------------------------

        print(
            "\n[REGIME] Target distribution:"
        )

        distribution = (
            y.value_counts()
            .reindex(
                [0, 1, 2],
                fill_value=0
            )
        )

        print(
            f"  BEAR     : {distribution[0]}"
        )

        print(
            f"  SIDEWAYS : {distribution[1]}"
        )

        print(
            f"  BULL     : {distribution[2]}"
        )

        # ----------------------------------------------------
        # Chronological split
        #
        # No random shuffle.
        # No future information in training.
        # ----------------------------------------------------

        split_index = int(
            len(X) * 0.80
        )

        X_train = X.iloc[:split_index].copy()
        y_train = y.iloc[:split_index].copy()

        X_test = X.iloc[split_index:].copy()
        y_test = y.iloc[split_index:].copy()

        print(
            f"\n[REGIME] Training rows: "
            f"{len(X_train)}"
        )

        print(
            f"[REGIME] Testing rows: "
            f"{len(X_test)}"
        )

        print(
            f"[REGIME] Features: "
            f"{len(feature_columns)}"
        )

        print(
            "\n[REGIME] Training distribution:"
        )

        print(
            y_train
            .value_counts()
            .reindex(
                [0, 1, 2],
                fill_value=0
            )
            .rename(index={
                0: "BEAR",
                1: "SIDEWAYS",
                2: "BULL",
            })
            .to_string()
        )

        print(
            "\n[REGIME] Testing distribution:"
        )

        print(
            y_test
            .value_counts()
            .reindex(
                [0, 1, 2],
                fill_value=0
            )
            .rename(index={
                0: "BEAR",
                1: "SIDEWAYS",
                2: "BULL",
            })
            .to_string()
        )

        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------
        #
        # Balanced class weights prevent the model from
        # simply favoring the majority class.
        #
        # More trees improve stability.
        # Moderate depth reduces overfitting.
        # ----------------------------------------------------

        self.model = RandomForestClassifier(
            n_estimators=700,
            max_depth=14,
            min_samples_split=12,
            min_samples_leaf=5,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        )

        print(
            "\n[REGIME] Training Random Forest..."
        )

        self.model.fit(
            X_train,
            y_train
        )

        # ----------------------------------------------------
        # PREDICTIONS
        # ----------------------------------------------------

        predictions = self.model.predict(
            X_test
        )

        probabilities = (
            self.model.predict_proba(X_test)
        )

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

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

        macro_f1 = f1_score(
            y_test,
            predictions,
            average="macro",
            zero_division=0
        )

        print(
            f"\n[REGIME] Accuracy: "
            f"{accuracy:.4f}"
        )

        print(
            f"[REGIME] Balanced accuracy: "
            f"{balanced_accuracy:.4f}"
        )

        print(
            f"[REGIME] Macro F1: "
            f"{macro_f1:.4f}"
        )

        # ----------------------------------------------------
        # CLASSIFICATION REPORT
        # ----------------------------------------------------

        print(
            "\n[REGIME] Classification report:"
        )

        print(
            classification_report(
                y_test,
                predictions,
                labels=[0, 1, 2],
                target_names=[
                    "BEAR",
                    "SIDEWAYS",
                    "BULL",
                ],
                zero_division=0
            )
        )

        # ----------------------------------------------------
        # CONFUSION MATRIX
        # ----------------------------------------------------

        matrix = confusion_matrix(
            y_test,
            predictions,
            labels=[0, 1, 2]
        )

        print(
            "[REGIME] Confusion matrix:"
        )

        print(
            pd.DataFrame(
                matrix,
                index=[
                    "Actual BEAR",
                    "Actual SIDEWAYS",
                    "Actual BULL",
                ],
                columns=[
                    "Pred BEAR",
                    "Pred SIDEWAYS",
                    "Pred BULL",
                ]
            ).to_string()
        )

        # ----------------------------------------------------
        # FEATURE IMPORTANCE
        # ----------------------------------------------------

        importance = pd.DataFrame({
            "feature": feature_columns,
            "importance": (
                self.model.feature_importances_
            ),
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
            "\n[REGIME] Top features:"
        )

        print(
            importance
            .head(20)
            .to_string(index=False)
        )

        # ----------------------------------------------------
        # SAVE MODEL
        # ----------------------------------------------------

        model_path = (
            self.model_dir
            / "regime_model.pkl"
        )

        metadata_path = (
            self.model_dir
            / "regime_model_features.parquet"
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
            f"\n[REGIME] Model saved: "
            f"{model_path}"
        )

        print(
            f"[REGIME] Features saved: "
            f"{metadata_path}"
        )

        return {
            "accuracy": accuracy,
            "balanced_accuracy": balanced_accuracy,
            "macro_f1": macro_f1,
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
            / "regime_model.pkl"
        )

        metadata_path = (
            self.model_dir
            / "regime_model_features.parquet"
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

        if not self.feature_columns:
            raise RuntimeError(
                "Regime feature columns unavailable."
            )

        print(
            f"[REGIME] Model loaded: "
            f"{model_path}"
        )

        print(
            f"[REGIME] Features loaded: "
            f"{len(self.feature_columns)}"
        )

        return self

    # ========================================================
    # PREDICT
    # ========================================================

    def predict(self, df):

        if self.model is None:
            raise RuntimeError(
                "Regime model is not loaded."
            )

        if not self.feature_columns:
            raise RuntimeError(
                "Regime feature columns unavailable."
            )

        missing = [
            c
            for c in self.feature_columns
            if c not in df.columns
        ]

        if missing:

            raise ValueError(
                "Missing regime features: "
                f"{missing}"
            )

        X = (
            df[self.feature_columns]
            .copy()
            .replace(
                [np.inf, -np.inf],
                np.nan
            )
            .fillna(0)
        )

        prediction = self.model.predict(
            X
        )

        probabilities = (
            self.model.predict_proba(X)
        )

        results = []

        for i, predicted in enumerate(
            prediction
        ):

            probs = probabilities[i]

            # ----------------------------------------------
            # Probability ordering
            # ----------------------------------------------

            probability_map = {
                int(cls): float(prob)
                for cls, prob in zip(
                    self.model.classes_,
                    probs
                )
            }

            bear_probability = (
                probability_map.get(0, 0.0)
            )

            sideways_probability = (
                probability_map.get(1, 0.0)
            )

            bull_probability = (
                probability_map.get(2, 0.0)
            )

            ordered = sorted(
                probability_map.values(),
                reverse=True
            )

            confidence = (
                ordered[0]
                if ordered
                else 0.0
            )

            second_probability = (
                ordered[1]
                if len(ordered) > 1
                else 0.0
            )

            confidence_margin = (
                confidence
                - second_probability
            )

            # ----------------------------------------------
            # Regime strength
            #
            # Measures directional conviction:
            #
            # BULL -> bull - bear
            # BEAR -> bear - bull
            # SIDEWAYS -> 1 - abs(bull - bear)
            # ----------------------------------------------

            directional_edge = (
                bull_probability
                - bear_probability
            )

            if int(predicted) == 2:

                regime_strength = (
                    max(
                        0.0,
                        directional_edge
                    )
                )

            elif int(predicted) == 0:

                regime_strength = (
                    max(
                        0.0,
                        -directional_edge
                    )
                )

            else:

                regime_strength = (
                    max(
                        0.0,
                        1.0
                        - abs(
                            directional_edge
                        )
                    )
                )

            # ----------------------------------------------
            # Confidence level
            # ----------------------------------------------

            if confidence >= 0.70:

                confidence_level = "HIGH"

            elif confidence >= 0.50:

                confidence_level = "MEDIUM"

            else:

                confidence_level = "LOW"

            results.append({
                "regime_prediction":
                    self.regime_names[
                        int(predicted)
                    ],

                "bear_probability":
                    bear_probability,

                "sideways_probability":
                    sideways_probability,

                "bull_probability":
                    bull_probability,

                "confidence":
                    confidence,

                "confidence_margin":
                    confidence_margin,

                "confidence_level":
                    confidence_level,

                "regime_strength":
                    regime_strength,
            })

        return pd.DataFrame(results)