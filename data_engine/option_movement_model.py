# ============================================================
# TradingAI - OPTION MOVEMENT MODEL
# ============================================================

from pathlib import Path
import json
import pickle

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


class OptionMovementModel:

    MODEL_PATH = Path(
        "market_data/models/option_movement_model.pkl"
    )

    FEATURES_PATH = Path(
        "market_data/models/option_movement_model_features.parquet"
    )

    METADATA_PATH = Path(
        "market_data/models/option_movement_model_metadata.json"
    )

    LABELS = {
        -1: "DOWN",
        0: "SIDEWAYS",
        1: "UP",
    }

    # ========================================================
    # INITIALIZE
    # ========================================================

    def __init__(self):

        self.model = None
        self.feature_columns = []

    # ========================================================
    # TRAIN
    # ========================================================

    def train(
        self,
        df,
    ):

        if df is None or df.empty:

            raise ValueError(
                "Option movement dataset is empty."
            )

        if "target" not in df.columns:

            raise ValueError(
                "Missing target column."
            )

        df = df.copy()

        # ----------------------------------------------------
        # Sort chronologically BEFORE splitting.
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce",
            )

            df = (
                df
                .dropna(
                    subset=["timestamp"]
                )
                .sort_values("timestamp")
                .reset_index(drop=True)
            )

        # ----------------------------------------------------
        # Select ONLY point-in-time features.
        # ----------------------------------------------------

        feature_columns = (
            self._feature_columns(df)
        )

        if not feature_columns:

            raise ValueError(
                "No usable model features."
            )

        print(
            "\n[OPTION MOVEMENT] "
            "Selected features:"
        )

        for feature in feature_columns:

            print(
                f"  - {feature}"
            )

        # ----------------------------------------------------
        # Numeric conversion.
        # ----------------------------------------------------

        for column in feature_columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        df["target"] = pd.to_numeric(
            df["target"],
            errors="coerce",
        )

        df = df.replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )

        # ----------------------------------------------------
        # Remove invalid rows.
        # ----------------------------------------------------

        df = df.dropna(
            subset=(
                feature_columns
                + ["target"]
            )
        ).reset_index(
            drop=True
        )

        # ----------------------------------------------------
        # Target validation.
        # ----------------------------------------------------

        df = df[
            df["target"].isin(
                [
                    -1,
                    0,
                    1,
                ]
            )
        ].copy()

        if len(df) < 100:

            raise ValueError(
                "Not enough valid option movement "
                "rows to train model."
            )

        if df["target"].nunique() < 2:

            raise ValueError(
                "Option movement dataset contains "
                "fewer than two target classes."
            )

        X = df[
            feature_columns
        ].copy()

        y = (
            df["target"]
            .astype(int)
        )

        # ----------------------------------------------------
        # Chronological 80/20 split.
        # ----------------------------------------------------

        split = int(
            len(df) * 0.80
        )

        split = max(
            1,
            min(
                split,
                len(df) - 1,
            ),
        )

        X_train = (
            X.iloc[:split]
            .copy()
        )

        X_test = (
            X.iloc[split:]
            .copy()
        )

        y_train = (
            y.iloc[:split]
            .copy()
        )

        y_test = (
            y.iloc[split:]
            .copy()
        )

        print(
            f"\n[OPTION MOVEMENT] "
            f"Training rows: {len(X_train)}"
        )

        print(
            f"[OPTION MOVEMENT] "
            f"Testing rows: {len(X_test)}"
        )

        print(
            f"[OPTION MOVEMENT] "
            f"Features: {len(feature_columns)}"
        )

        print(
            "\n[OPTION MOVEMENT] "
            "Training distribution:"
        )

        print(
            y_train
            .map(self.LABELS)
            .value_counts()
            .reindex(
                [
                    "DOWN",
                    "SIDEWAYS",
                    "UP",
                ],
                fill_value=0,
            )
            .to_string()
        )

        print(
            "\n[OPTION MOVEMENT] "
            "Testing distribution:"
        )

        print(
            y_test
            .map(self.LABELS)
            .value_counts()
            .reindex(
                [
                    "DOWN",
                    "SIDEWAYS",
                    "UP",
                ],
                fill_value=0,
            )
            .to_string()
        )

        # ----------------------------------------------------
        # Model.
        # ----------------------------------------------------

        self.model = RandomForestClassifier(
            n_estimators=500,
            max_depth=12,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )

        print(
            "\n[OPTION MOVEMENT] "
            "Training Random Forest..."
        )

        self.model.fit(
            X_train,
            y_train,
        )

        # ----------------------------------------------------
        # Evaluation.
        # ----------------------------------------------------

        predictions = (
            self.model.predict(
                X_test
            )
        )

        accuracy = (
            accuracy_score(
                y_test,
                predictions,
            )
        )

        balanced_accuracy = (
            balanced_accuracy_score(
                y_test,
                predictions,
            )
        )

        macro_f1 = (
            f1_score(
                y_test,
                predictions,
                average="macro",
                zero_division=0,
            )
        )

        print(
            f"\n[OPTION MOVEMENT] "
            f"Accuracy: {accuracy:.4f}"
        )

        print(
            f"[OPTION MOVEMENT] "
            f"Balanced accuracy: "
            f"{balanced_accuracy:.4f}"
        )

        print(
            f"[OPTION MOVEMENT] "
            f"Macro F1: {macro_f1:.4f}"
        )

        print(
            "\n[OPTION MOVEMENT] "
            "Classification report:"
        )

        print(
            classification_report(
                y_test,
                predictions,
                labels=[
                    -1,
                    0,
                    1,
                ],
                target_names=[
                    "DOWN",
                    "SIDEWAYS",
                    "UP",
                ],
                zero_division=0,
            )
        )

        print(
            "[OPTION MOVEMENT] "
            "Confusion matrix:"
        )

        cm = confusion_matrix(
            y_test,
            predictions,
            labels=[
                -1,
                0,
                1,
            ],
        )

        print(
            pd.DataFrame(
                cm,
                index=[
                    "Actual DOWN",
                    "Actual SIDEWAYS",
                    "Actual UP",
                ],
                columns=[
                    "Pred DOWN",
                    "Pred SIDEWAYS",
                    "Pred UP",
                ],
            ).to_string()
        )

        # ----------------------------------------------------
        # Feature importance.
        # ----------------------------------------------------

        importance = (
            pd.DataFrame(
                {
                    "feature":
                        feature_columns,

                    "importance":
                        self.model
                        .feature_importances_,
                }
            )
            .sort_values(
                "importance",
                ascending=False,
            )
        )

        print(
            "\n[OPTION MOVEMENT] "
            "Top features:"
        )

        print(
            importance
            .head(20)
            .to_string(
                index=False
            )
        )

        # ----------------------------------------------------
        # Save model.
        # ----------------------------------------------------

        self.feature_columns = (
            feature_columns
        )

        self.MODEL_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            self.MODEL_PATH,
            "wb",
        ) as file:

            pickle.dump(
                self.model,
                file,
            )

        pd.DataFrame(
            {
                "feature":
                    feature_columns
            }
        ).to_parquet(
            self.FEATURES_PATH,
            index=False,
        )

        metadata = {

            "model":
                "RandomForestClassifier",

            "labels":
                self.LABELS,

            "accuracy":
                float(accuracy),

            "balanced_accuracy":
                float(
                    balanced_accuracy
                ),

            "macro_f1":
                float(macro_f1),

            "train_rows":
                int(
                    len(X_train)
                ),

            "test_rows":
                int(
                    len(X_test)
                ),

            "feature_count":
                int(
                    len(feature_columns)
                ),

            "feature_columns":
                feature_columns,

            "leakage_protection":
                True,
        }

        with open(
            self.METADATA_PATH,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                indent=2,
            )

        print(
            f"\n[OPTION MOVEMENT] "
            f"Model saved: "
            f"{self.MODEL_PATH}"
        )

        print(
            f"[OPTION MOVEMENT] "
            f"Features saved: "
            f"{self.FEATURES_PATH}"
        )

        print(
            f"[OPTION MOVEMENT] "
            f"Metadata saved: "
            f"{self.METADATA_PATH}"
        )

        return {
            "accuracy":
                accuracy,

            "balanced_accuracy":
                balanced_accuracy,

            "macro_f1":
                macro_f1,

            "train_rows":
                len(X_train),

            "test_rows":
                len(X_test),

            "feature_count":
                len(feature_columns),
        }

    # ========================================================
    # LOAD
    # ========================================================

    def load(
        self,
    ):

        if not self.MODEL_PATH.exists():

            raise FileNotFoundError(
                f"Option movement model not found: "
                f"{self.MODEL_PATH}"
            )

        if not self.FEATURES_PATH.exists():

            raise FileNotFoundError(
                f"Option movement feature file "
                f"not found: {self.FEATURES_PATH}"
            )

        with open(
            self.MODEL_PATH,
            "rb",
        ) as file:

            self.model = (
                pickle.load(
                    file
                )
            )

        features_df = (
            pd.read_parquet(
                self.FEATURES_PATH
            )
        )

        if "feature" not in features_df.columns:

            raise RuntimeError(
                "Saved option movement feature "
                "file is invalid."
            )

        self.feature_columns = (
            features_df[
                "feature"
            ]
            .astype(str)
            .tolist()
        )

        # ----------------------------------------------------
        # Defensive leakage check when loading.
        # ----------------------------------------------------

        leakage = (
            set(
                self.feature_columns
            )
            & self._TARGET_LEAKAGE_COLUMNS()
        )

        if leakage:

            raise RuntimeError(
                "Saved option movement model "
                "contains target leakage features: "
                f"{sorted(leakage)}"
            )

        print(
            f"[OPTION MOVEMENT] "
            f"Model loaded: "
            f"{self.MODEL_PATH}"
        )

        print(
            f"[OPTION MOVEMENT] "
            f"Features loaded: "
            f"{len(self.feature_columns)}"
        )

        return self

    # ========================================================
    # PREDICT
    # ========================================================

    def predict(
        self,
        df,
    ):

        if self.model is None:

            self.load()

        missing = [
            column
            for column in self.feature_columns
            if column not in df.columns
        ]

        if missing:

            raise ValueError(
                "Prediction dataframe is missing "
                f"features: {missing}"
            )

        X = df[
            self.feature_columns
        ].copy()

        X = X.replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        ).fillna(0)

        prediction = (
            self.model.predict(X)
        )

        probabilities = (
            self.model.predict_proba(X)
        )

        classes = list(
            self.model.classes_
        )

        output = []

        for index in range(
            len(X)
        ):

            probs = {

                int(cls):
                    float(
                        probabilities[
                            index
                        ][class_index]
                    )

                for (
                    class_index,
                    cls
                )
                in enumerate(classes)
            }

            down = (
                probs.get(
                    -1,
                    0.0,
                )
            )

            sideways = (
                probs.get(
                    0,
                    0.0,
                )
            )

            up = (
                probs.get(
                    1,
                    0.0,
                )
            )

            values = [
                down,
                sideways,
                up,
            ]

            sorted_values = sorted(
                values,
                reverse=True,
            )

            confidence = (
                sorted_values[0]
            )

            margin = (
                sorted_values[0]
                - sorted_values[1]
            )

            if confidence >= 0.70:

                confidence_level = (
                    "HIGH"
                )

            elif confidence >= 0.55:

                confidence_level = (
                    "MEDIUM"
                )

            else:

                confidence_level = (
                    "LOW"
                )

            label = self.LABELS.get(
                int(
                    prediction[index]
                )
            )

            if label is None:

                raise RuntimeError(
                    "Unexpected option movement "
                    f"class: "
                    f"{prediction[index]}"
                )

            output.append(
                {

                    "prediction":
                        label,

                    "movement_prediction":
                        label,

                    "down_probability":
                        down,

                    "sideways_probability":
                        sideways,

                    "up_probability":
                        up,

                    "confidence":
                        confidence,

                    "confidence_margin":
                        margin,

                    "confidence_level":
                        confidence_level,
                }
            )

        return pd.DataFrame(
            output
        )

    # ========================================================
    # TARGET-LEAKAGE COLUMNS
    # ========================================================

    @staticmethod
    def _TARGET_LEAKAGE_COLUMNS():

        return {

            # Future raw information
            "future_last_price",
            "future_premium",
            "future_premium_return",

            # Target-derived information
            "target",
            "movement",
            "movement_target",

            # Future movement calculations
            "premium_return",
            "premium_change",
        }

    # ========================================================
    # FEATURE SELECTION
    # ========================================================

    @classmethod
    def _feature_columns(
        cls,
        df,
    ):

        excluded = {

            # Metadata
            "timestamp",
            "date",
            "symbol",
            "source",
            "series",
            "expiry",
            "option_type",
            "future_timestamp",

            # ------------------------------------------------
            # FUTURE / TARGET LEAKAGE
            # ------------------------------------------------

            "future_last_price",
            "future_premium",
            "future_premium_return",

            "premium_return",
            "premium_change",

            "target",
            "movement_target",
            "movement",
        }

        candidates = [
            column
            for column in df.columns
            if (
                column not in excluded
                and pd.api.types
                .is_numeric_dtype(
                    df[column]
                )
            )
        ]

        # ----------------------------------------------------
        # Defensive final check.
        # ----------------------------------------------------

        leakage = (
            set(candidates)
            & cls._TARGET_LEAKAGE_COLUMNS()
        )

        if leakage:

            raise RuntimeError(
                "Target leakage detected in "
                f"feature selection: "
                f"{sorted(leakage)}"
            )

        return candidates