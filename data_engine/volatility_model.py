# ============================================================
# TradingAI - VOLATILITY MODEL
# ============================================================

from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
)

warnings.filterwarnings("ignore")


class VolatilityModel:

    # ========================================================
    # CONFIGURATION
    # ========================================================

    MODEL_DIR = Path("market_data/models")

    MODEL_PATH = (
        MODEL_DIR / "volatility_model.pkl"
    )

    FEATURES_PATH = (
        MODEL_DIR / "volatility_model_features.parquet"
    )

    METADATA_PATH = (
        MODEL_DIR / "volatility_model_metadata.json"
    )

    RANDOM_STATE = 42

    TRAIN_RATIO = 0.80

    # Number of trees
    N_ESTIMATORS = 500

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self):

        self.MODEL_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        self.regressor = None
        self.classifier = None

        self.feature_columns = []

        self.low_threshold = None
        self.high_threshold = None

        self.metadata = {}

    # ========================================================
    # FEATURE SELECTION
    # ========================================================

    @staticmethod
    def _feature_columns(df):

        excluded = {
            "timestamp",
            "date",
            "symbol",
            "source",
            "series",

            # Targets
            "future_volatility",
            "volatility_target",
            "volatility_regime",
        }

        features = [
            c
            for c in df.columns
            if c not in excluded
            and pd.api.types.is_numeric_dtype(
                df[c]
            )
        ]

        return features

    # ========================================================
    # TRAIN
    # ========================================================

    def train(self, df):

        if df is None or df.empty:
            raise ValueError(
                "Volatility training dataset is empty."
            )

        df = df.copy()

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
        # Validate target
        # ----------------------------------------------------

        target = "volatility_target"

        if target not in df.columns:

            raise ValueError(
                "Missing volatility_target column."
            )

        df = df[
            df[target].notna()
        ].copy()

        df = df[
            np.isfinite(
                df[target]
            )
        ].copy()

        if len(df) < 100:

            raise ValueError(
                "Not enough rows to train volatility model."
            )

        # ----------------------------------------------------
        # Features
        # ----------------------------------------------------

        features = self._feature_columns(df)

        if not features:

            raise ValueError(
                "No numeric volatility features found."
            )

        # ----------------------------------------------------
        # Remove rows with invalid feature values
        # ----------------------------------------------------

        X = df[features].copy()

        X = X.replace(
            [np.inf, -np.inf],
            np.nan
        )

        valid_mask = X.notna().all(axis=1)

        X = X.loc[
            valid_mask
        ].copy()

        y = df.loc[
            valid_mask,
            target
        ].astype(float)

        df_clean = df.loc[
            valid_mask
        ].copy()

        # ----------------------------------------------------
        # Chronological split
        # ----------------------------------------------------

        split_index = int(
            len(df_clean)
            * self.TRAIN_RATIO
        )

        if split_index <= 0 or split_index >= len(df_clean):

            raise ValueError(
                "Invalid chronological train/test split."
            )

        X_train = X.iloc[
            :split_index
        ].copy()

        X_test = X.iloc[
            split_index:
        ].copy()

        y_train = y.iloc[
            :split_index
        ].copy()

        y_test = y.iloc[
            split_index:
        ].copy()

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Thresholds are calculated ONLY from training data.
        #
        # This prevents future/test information from leaking
        # into the classifier.
        # ----------------------------------------------------

        self.low_threshold = float(
            y_train.quantile(
                0.3333
            )
        )

        self.high_threshold = float(
            y_train.quantile(
                0.6667
            )
        )

        if (
            self.low_threshold
            >= self.high_threshold
        ):

            raise ValueError(
                "Invalid volatility thresholds."
            )

        print(
            f"[VOLATILITY] Selected features: "
            f"{len(features)}"
        )

        print(
            f"[VOLATILITY] Training rows: "
            f"{len(X_train)}"
        )

        print(
            f"[VOLATILITY] Testing rows: "
            f"{len(X_test)}"
        )

        print(
            f"[VOLATILITY] Features: "
            f"{len(features)}"
        )

        print(
            "\n[VOLATILITY] Training thresholds:"
        )

        print(
            f"LOW <= {self.low_threshold:.6f}"
        )

        print(
            f"HIGH >= {self.high_threshold:.6f}"
        )

        # ====================================================
        # REGRESSION MODEL
        # ====================================================

        print(
            "\n[VOLATILITY] Training regression model..."
        )

        self.regressor = RandomForestRegressor(
            n_estimators=self.N_ESTIMATORS,
            random_state=self.RANDOM_STATE,
            n_jobs=-1,
            min_samples_leaf=5,
            max_features="sqrt",
        )

        self.regressor.fit(
            X_train,
            y_train
        )

        regression_prediction = (
            self.regressor.predict(
                X_test
            )
        )

        mae = mean_absolute_error(
            y_test,
            regression_prediction
        )

        rmse = np.sqrt(
            mean_squared_error(
                y_test,
                regression_prediction
            )
        )

        r2 = r2_score(
            y_test,
            regression_prediction
        )

        print(
            f"\n[VOLATILITY] MAE: "
            f"{mae:.6f}"
        )

        print(
            f"[VOLATILITY] RMSE: "
            f"{rmse:.6f}"
        )

        print(
            f"[VOLATILITY] R²: "
            f"{r2:.4f}"
        )

        # ====================================================
        # CLASSIFICATION TARGET
        # ====================================================

        def make_regime(values):

            return np.select(
                [
                    values <= self.low_threshold,
                    values >= self.high_threshold,
                ],
                [
                    "LOW",
                    "HIGH",
                ],
                default="NORMAL"
            )

        y_train_regime = make_regime(
            y_train.values
        )

        y_test_regime = make_regime(
            y_test.values
        )

        print(
            "\n[VOLATILITY] Training regime distribution:"
        )

        print(
            pd.Series(
                y_train_regime,
                name="volatility_regime"
            )
            .value_counts()
            .reindex(
                [
                    "LOW",
                    "NORMAL",
                    "HIGH"
                ],
                fill_value=0
            )
            .to_string()
        )

        print(
            "\n[VOLATILITY] Testing regime distribution:"
        )

        print(
            pd.Series(
                y_test_regime,
                name="volatility_regime"
            )
            .value_counts()
            .reindex(
                [
                    "LOW",
                    "NORMAL",
                    "HIGH"
                ],
                fill_value=0
            )
            .to_string()
        )

        # ====================================================
        # CLASSIFIER
        # ====================================================

        print(
            "\n[VOLATILITY] Training regime classifier..."
        )

        self.classifier = RandomForestClassifier(
            n_estimators=self.N_ESTIMATORS,
            random_state=self.RANDOM_STATE,
            n_jobs=-1,

            # Helps prevent the NORMAL class from dominating
            class_weight="balanced_subsample",

            min_samples_leaf=5,
            max_features="sqrt",
        )

        self.classifier.fit(
            X_train,
            y_train_regime
        )

        regime_prediction = (
            self.classifier.predict(
                X_test
            )
        )

        accuracy = accuracy_score(
            y_test_regime,
            regime_prediction
        )

        balanced_accuracy = (
            balanced_accuracy_score(
                y_test_regime,
                regime_prediction
            )
        )

        print(
            f"\n[VOLATILITY] Regime accuracy: "
            f"{accuracy:.4f}"
        )

        print(
            f"[VOLATILITY] Balanced accuracy: "
            f"{balanced_accuracy:.4f}"
        )

        print(
            "\n[VOLATILITY] Classification report:"
        )

        print(
            classification_report(
                y_test_regime,
                regime_prediction,
                labels=[
                    "LOW",
                    "NORMAL",
                    "HIGH",
                ],
                zero_division=0
            )
        )

        print(
            "[VOLATILITY] Confusion matrix:"
        )

        matrix = confusion_matrix(
            y_test_regime,
            regime_prediction,
            labels=[
                "LOW",
                "NORMAL",
                "HIGH",
            ]
        )

        print(
            pd.DataFrame(
                matrix,
                index=[
                    "Actual LOW",
                    "Actual NORMAL",
                    "Actual HIGH",
                ],
                columns=[
                    "Pred LOW",
                    "Pred NORMAL",
                    "Pred HIGH",
                ]
            )
            .to_string()
        )

        print(
            "\n[VOLATILITY] Predicted regime distribution:"
        )

        print(
            pd.Series(
                regime_prediction,
                name="volatility_regime"
            )
            .value_counts()
            .reindex(
                [
                    "LOW",
                    "NORMAL",
                    "HIGH"
                ],
                fill_value=0
            )
            .to_string()
        )

        # ====================================================
        # FEATURE IMPORTANCE
        # ====================================================

        importance = pd.DataFrame(
            {
                "feature": features,
                "importance": (
                    self.regressor.feature_importances_
                ),
            }
        ).sort_values(
            "importance",
            ascending=False
        )

        print(
            "\n[VOLATILITY] Top features:"
        )

        print(
            importance
            .head(20)
            .to_string(index=False)
        )

        # ====================================================
        # SAVE MODEL
        # ====================================================

        bundle = {
            "regressor": self.regressor,
            "classifier": self.classifier,
            "feature_columns": features,
            "low_threshold": self.low_threshold,
            "high_threshold": self.high_threshold,
        }

        joblib.dump(
            bundle,
            self.MODEL_PATH
        )

        # ----------------------------------------------------
        # Save feature names
        # ----------------------------------------------------

        feature_df = pd.DataFrame(
            {
                "feature": features
            }
        )

        feature_df.to_parquet(
            self.FEATURES_PATH,
            index=False
        )

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

        self.metadata = {
            "model_type": "random_forest",
            "regressor_type": "RandomForestRegressor",
            "classifier_type": "RandomForestClassifier",

            "feature_count": len(features),

            "train_rows": len(X_train),
            "test_rows": len(X_test),

            "train_ratio": self.TRAIN_RATIO,

            "n_estimators": self.N_ESTIMATORS,

            "low_threshold": self.low_threshold,
            "high_threshold": self.high_threshold,

            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2),

            "accuracy": float(accuracy),
            "balanced_accuracy": float(
                balanced_accuracy
            ),

            "features": features,
        }

        with open(
            self.METADATA_PATH,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.metadata,
                f,
                indent=2
            )

        self.feature_columns = features

        print(
            f"\n[VOLATILITY] Model saved: "
            f"{self.MODEL_PATH}"
        )

        print(
            f"[VOLATILITY] Features saved: "
            f"{self.FEATURES_PATH}"
        )

        print(
            f"[VOLATILITY] Metadata saved: "
            f"{self.METADATA_PATH}"
        )

        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2),

            "accuracy": float(accuracy),
            "balanced_accuracy": float(
                balanced_accuracy
            ),

            "train_rows": len(X_train),
            "test_rows": len(X_test),

            "feature_count": len(features),

            "low_threshold": self.low_threshold,
            "high_threshold": self.high_threshold,
        }

    # ========================================================
    # LOAD
    # ========================================================

    def load(self):

        if not self.MODEL_PATH.exists():

            raise FileNotFoundError(
                f"Volatility model not found: "
                f"{self.MODEL_PATH}"
            )

        bundle = joblib.load(
            self.MODEL_PATH
        )

        self.regressor = bundle[
            "regressor"
        ]

        self.classifier = bundle[
            "classifier"
        ]

        self.feature_columns = bundle[
            "feature_columns"
        ]

        self.low_threshold = bundle.get(
            "low_threshold"
        )

        self.high_threshold = bundle.get(
            "high_threshold"
        )

        # ----------------------------------------------------
        # Backward compatibility
        # ----------------------------------------------------

        if (
            self.low_threshold is None
            or self.high_threshold is None
        ):

            if self.METADATA_PATH.exists():

                with open(
                    self.METADATA_PATH,
                    "r",
                    encoding="utf-8"
                ) as f:

                    metadata = json.load(f)

                self.low_threshold = metadata.get(
                    "low_threshold"
                )

                self.high_threshold = metadata.get(
                    "high_threshold"
                )

        if (
            self.low_threshold is None
            or self.high_threshold is None
        ):

            raise RuntimeError(
                "Volatility model thresholds are missing."
            )

        print(
            f"[VOLATILITY] Model loaded: "
            f"{self.MODEL_PATH}"
        )

        print(
            f"[VOLATILITY] Features loaded: "
            f"{len(self.feature_columns)}"
        )

        return self

    # ========================================================
    # PREDICT
    # ========================================================

    def predict(self, df):

        if self.regressor is None:

            self.load()

        if df is None or df.empty:

            raise ValueError(
                "Prediction dataframe is empty."
            )

        df = df.copy()

        # ----------------------------------------------------
        # Validate features
        # ----------------------------------------------------

        missing = [
            c
            for c in self.feature_columns
            if c not in df.columns
        ]

        if missing:

            raise ValueError(
                "Missing volatility features: "
                f"{missing}"
            )

        X = df[
            self.feature_columns
        ].copy()

        X = X.replace(
            [np.inf, -np.inf],
            np.nan
        )

        # ----------------------------------------------------
        # Fill missing feature values
        #
        # Usually the latest row should already be complete.
        # This prevents prediction from crashing because of
        # an isolated NaN.
        # ----------------------------------------------------

        X = X.ffill().bfill()

        if X.isna().any().any():

            raise ValueError(
                "Volatility features contain unresolved NaN values."
            )

        # ====================================================
        # REGRESSION
        # ====================================================

        predicted_volatility = (
            self.regressor.predict(X)
        )

        predicted_volatility = np.maximum(
            predicted_volatility,
            0.0
        )

        # ====================================================
        # CLASSIFICATION
        # ====================================================

        regime_prediction = (
            self.classifier.predict(X)
        )

        probabilities = (
            self.classifier.predict_proba(X)
        )

        classes = list(
            self.classifier.classes_
        )

        # ----------------------------------------------------
        # Probability extraction
        # ----------------------------------------------------

        def probability_for(
            class_name,
            row
        ):

            if class_name in classes:

                index = classes.index(
                    class_name
                )

                return float(
                    row[index]
                )

            return 0.0

        rows = []

        for i in range(len(X)):

            probs = probabilities[i]

            low_probability = (
                probability_for(
                    "LOW",
                    probs
                )
            )

            normal_probability = (
                probability_for(
                    "NORMAL",
                    probs
                )
            )

            high_probability = (
                probability_for(
                    "HIGH",
                    probs
                )
            )

            sorted_probs = sorted(
                probs,
                reverse=True
            )

            confidence = float(
                sorted_probs[0]
            )

            if len(sorted_probs) > 1:

                confidence_margin = (
                    float(sorted_probs[0])
                    - float(sorted_probs[1])
                )

            else:

                confidence_margin = confidence

            # ------------------------------------------------
            # Confidence level
            # ------------------------------------------------

            if confidence >= 0.75:

                confidence_level = "HIGH"

            elif confidence >= 0.60:

                confidence_level = "MEDIUM"

            elif confidence >= 0.50:

                confidence_level = "LOW"

            else:

                confidence_level = "VERY_LOW"

            # ------------------------------------------------
            # Regime strength
            #
            # Measures how strongly the classifier prefers
            # the winning regime.
            # ------------------------------------------------

            regime_strength = (
                confidence
                * max(
                    confidence_margin,
                    0.0
                )
            )

            rows.append(
                {
                    "predicted_volatility":
                        float(
                            predicted_volatility[i]
                        ),

                    "volatility_regime":
                        str(
                            regime_prediction[i]
                        ),

                    "low_probability":
                        low_probability,

                    "normal_probability":
                        normal_probability,

                    "high_probability":
                        high_probability,

                    "confidence":
                        confidence,

                    "confidence_margin":
                        confidence_margin,

                    "confidence_level":
                        confidence_level,

                    "regime_strength":
                        float(
                            regime_strength
                        ),
                }
            )

        return pd.DataFrame(
            rows
        )