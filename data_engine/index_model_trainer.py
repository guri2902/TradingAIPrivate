# ============================================================
# TradingAI - NIFTY INDEX MODEL TRAINER
# ============================================================

from __future__ import annotations

from pathlib import Path
import json
import pickle

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATASET_PATH = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "nifty_index_ml_dataset.parquet"
)

MODEL_DIR = (
    BASE_DIR
    / "market_data"
    / "models"
)


# ============================================================
# TARGETS
# ============================================================

TARGET_CONFIG = {

    "direction": {
        "target": "direction_target",
        "model_file": (
            "index_direction_model.pkl"
        ),
        "features_file": (
            "index_direction_model_features.parquet"
        ),
        "metadata_file": (
            "index_direction_model_metadata.json"
        ),
        "type": "classification",
        "labels": {
            0: "DOWN",
            1: "UP",
        },
    },

    "regime": {
        "target": "regime_target",
        "model_file": (
            "index_regime_model.pkl"
        ),
        "features_file": (
            "index_regime_model_features.parquet"
        ),
        "metadata_file": (
            "index_regime_model_metadata.json"
        ),
        "type": "classification",
        "labels": {
            -1: "BEAR",
            0: "SIDEWAYS",
            1: "BULL",
        },
    },

    "volatility": {
        "target": "volatility_target",
        "model_file": (
            "index_volatility_model.pkl"
        ),
        "features_file": (
            "index_volatility_model_features.parquet"
        ),
        "metadata_file": (
            "index_volatility_model_metadata.json"
        ),
        "type": "regression",
    },
}


# ============================================================
# TRAINER
# ============================================================

class IndexModelTrainer:

    # Future/target-derived fields that must never become
    # model features.
    LEAKAGE_COLUMNS = {
        "future_close",
        "future_return",
        "future_return_5",

        "direction_target",
        "regime_target",
        "volatility_target",
    }

    # Metadata / non-feature fields.
    METADATA_COLUMNS = {
        "timestamp",
        "symbol",
        "series",
    }

    # Delivery / stock-specific fields are not appropriate for
    # the index model and are deliberately excluded.
    INDEX_UNSUPPORTED_COLUMNS = {
        "total_trades",
        "qty_per_trade",
        "dlv_qty",
        "p/e",
    }

    # ========================================================
    # LOAD DATASET
    # ========================================================

    def load_dataset(
        self,
    ) -> pd.DataFrame:

        if not DATASET_PATH.exists():

            raise FileNotFoundError(
                f"NIFTY index dataset not found: "
                f"{DATASET_PATH}"
            )

        df = pd.read_parquet(
            DATASET_PATH
        )

        if df.empty:

            raise RuntimeError(
                "NIFTY index dataset is empty."
            )

        if "timestamp" not in df.columns:

            raise RuntimeError(
                "NIFTY index dataset is missing "
                "timestamp."
            )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

        df = (
            df
            .dropna(
                subset=["timestamp"]
            )
            .sort_values(
                "timestamp"
            )
            .reset_index(
                drop=True
            )
        )

        print(
            f"[INDEX-TRAIN] Dataset rows: "
            f"{len(df)}"
        )

        print(
            f"[INDEX-TRAIN] "
            f"Date range: "
            f"{df['timestamp'].min()} "
            f"-> "
            f"{df['timestamp'].max()}"
        )

        return df

    # ========================================================
    # FEATURE SELECTION
    # ========================================================

    def select_features(
        self,
        df: pd.DataFrame,
    ) -> list[str]:

        excluded = (
            self.LEAKAGE_COLUMNS
            | self.METADATA_COLUMNS
            | self.INDEX_UNSUPPORTED_COLUMNS
        )

        candidates = []

        for column in df.columns:

            if column in excluded:
                continue

            if not pd.api.types.is_numeric_dtype(
                df[column]
            ):
                continue

            candidates.append(
                column
            )

        if not candidates:

            raise RuntimeError(
                "No numeric index model "
                "features were found."
            )

        return candidates

    # ========================================================
    # SANITIZE FEATURES
    # ========================================================

    @staticmethod
    def sanitize_features(
        df: pd.DataFrame,
        feature_columns: list[str],
    ) -> pd.DataFrame:

        X = (
            df[
                feature_columns
            ]
            .copy()
        )

        X = X.replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )

        # Forward/backward fill is safe here because it uses
        # only feature history and is applied inside the
        # chronological dataset.
        X = (
            X
            .ffill()
            .bfill()
        )

        if X.isna().any().any():

            bad_columns = (
                X.columns[
                    X.isna().any()
                ]
                .tolist()
            )

            raise RuntimeError(
                "NaN values remain in "
                f"features: {bad_columns}"
            )

        return X

    # ========================================================
    # CHRONOLOGICAL SPLIT
    # ========================================================

    @staticmethod
    def chronological_split(
        X,
        y,
        split_ratio=0.80,
    ):

        split_index = int(
            len(X)
            * split_ratio
        )

        if split_index <= 0:

            raise RuntimeError(
                "Training split is empty."
            )

        if split_index >= len(X):

            raise RuntimeError(
                "Testing split is empty."
            )

        return (
            X.iloc[
                :split_index
            ].copy(),

            X.iloc[
                split_index:
            ].copy(),

            y.iloc[
                :split_index
            ].copy(),

            y.iloc[
                split_index:
            ].copy(),
        )

    # ========================================================
    # SAVE CLASSIFICATION MODEL
    # ========================================================

    def save_classification_model(
        self,
        config,
        model,
        feature_columns,
        metrics,
    ):

        MODEL_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        model_path = (
            MODEL_DIR
            / config["model_file"]
        )

        features_path = (
            MODEL_DIR
            / config["features_file"]
        )

        metadata_path = (
            MODEL_DIR
            / config["metadata_file"]
        )

        with open(
            model_path,
            "wb",
        ) as file:

            pickle.dump(
                model,
                file,
            )

        pd.DataFrame(
            {
                "feature":
                    feature_columns,
            }
        ).to_parquet(
            features_path,
            index=False,
        )

        metadata = {
            "model_type":
                "RandomForestClassifier",

            "task":
                config["type"],

            "labels":
                config.get(
                    "labels",
                    {}
                ),

            "feature_count":
                len(
                    feature_columns
                ),

            "feature_columns":
                feature_columns,

            "metrics":
                metrics,

            "chronological_split":
                True,

            "leakage_protection":
                True,
        }

        with open(
            metadata_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                indent=2,
                default=float,
            )

        print(
            f"[INDEX-TRAIN] "
            f"Model saved: {model_path}"
        )

        print(
            f"[INDEX-TRAIN] "
            f"Features saved: {features_path}"
        )

        print(
            f"[INDEX-TRAIN] "
            f"Metadata saved: {metadata_path}"
        )

    # ========================================================
    # SAVE REGRESSION MODEL
    # ========================================================

    def save_regression_model(
        self,
        config,
        model,
        feature_columns,
        metrics,
    ):

        MODEL_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        model_path = (
            MODEL_DIR
            / config["model_file"]
        )

        features_path = (
            MODEL_DIR
            / config["features_file"]
        )

        metadata_path = (
            MODEL_DIR
            / config["metadata_file"]
        )

        with open(
            model_path,
            "wb",
        ) as file:

            pickle.dump(
                model,
                file,
            )

        pd.DataFrame(
            {
                "feature":
                    feature_columns,
            }
        ).to_parquet(
            features_path,
            index=False,
        )

        metadata = {
            "model_type":
                "RandomForestRegressor",

            "task":
                config["type"],

            "feature_count":
                len(
                    feature_columns
                ),

            "feature_columns":
                feature_columns,

            "metrics":
                metrics,

            "chronological_split":
                True,

            "leakage_protection":
                True,
        }

        with open(
            metadata_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                indent=2,
                default=float,
            )

        print(
            f"[INDEX-TRAIN] "
            f"Model saved: {model_path}"
        )

        print(
            f"[INDEX-TRAIN] "
            f"Features saved: {features_path}"
        )

        print(
            f"[INDEX-TRAIN] "
            f"Metadata saved: {metadata_path}"
        )

    # ========================================================
    # TRAIN DIRECTION
    # ========================================================

    def train_direction(
        self,
        df,
        feature_columns,
    ):

        config = (
            TARGET_CONFIG[
                "direction"
            ]
        )

        target = config[
            "target"
        ]

        working = (
            df[
                feature_columns
                + [target]
            ]
            .copy()
        )

        working[target] = pd.to_numeric(
            working[target],
            errors="coerce",
        )

        working = working.dropna(
            subset=[target]
        )

        X = self.sanitize_features(
            working,
            feature_columns,
        )

        y = (
            working[target]
            .astype(int)
        )

        (
            X_train,
            X_test,
            y_train,
            y_test,
        ) = self.chronological_split(
            X,
            y,
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "INDEX DIRECTION MODEL"
        )

        print(
            "=" * 70
        )

        print(
            f"Train rows: {len(X_train)}"
        )

        print(
            f"Test rows: {len(X_test)}"
        )

        print(
            "\nTraining distribution:"
        )

        print(
            y_train
            .map(config["labels"])
            .value_counts()
            .sort_index()
            .to_string()
        )

        print(
            "\nTesting distribution:"
        )

        print(
            y_test
            .map(config["labels"])
            .value_counts()
            .sort_index()
            .to_string()
        )

        model = (
            RandomForestClassifier(
                n_estimators=500,
                max_depth=12,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )
        )

        print(
            "\n[INDEX-TRAIN] "
            "Training direction model..."
        )

        model.fit(
            X_train,
            y_train,
        )

        predictions = (
            model.predict(
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
            f"\nAccuracy: "
            f"{accuracy:.4f}"
        )

        print(
            f"Balanced accuracy: "
            f"{balanced_accuracy:.4f}"
        )

        print(
            f"Macro F1: "
            f"{macro_f1:.4f}"
        )

        print(
            "\nClassification report:"
        )

        print(
            classification_report(
                y_test,
                predictions,
                labels=[
                    0,
                    1,
                ],
                target_names=[
                    "DOWN",
                    "UP",
                ],
                zero_division=0,
            )
        )

        print(
            "Confusion matrix:"
        )

        print(
            pd.DataFrame(
                confusion_matrix(
                    y_test,
                    predictions,
                    labels=[
                        0,
                        1,
                    ],
                ),
                index=[
                    "Actual DOWN",
                    "Actual UP",
                ],
                columns=[
                    "Pred DOWN",
                    "Pred UP",
                ],
            ).to_string()
        )

        importance = (
            pd.DataFrame(
                {
                    "feature":
                        feature_columns,

                    "importance":
                        model.feature_importances_,
                }
            )
            .sort_values(
                "importance",
                ascending=False,
            )
        )

        print(
            "\nTop features:"
        )

        print(
            importance
            .head(15)
            .to_string(
                index=False
            )
        )

        metrics = {
            "accuracy":
                float(accuracy),

            "balanced_accuracy":
                float(
                    balanced_accuracy
                ),

            "macro_f1":
                float(macro_f1),

            "train_rows":
                int(len(X_train)),

            "test_rows":
                int(len(X_test)),

            "feature_count":
                int(
                    len(feature_columns)
                ),
        }

        self.save_classification_model(
            config=config,
            model=model,
            feature_columns=feature_columns,
            metrics=metrics,
        )

        return {
            "model": model,
            "metrics": metrics,
            "feature_columns":
                feature_columns,
        }

    # ========================================================
    # TRAIN REGIME
    # ========================================================

    def train_regime(
        self,
        df,
        feature_columns,
    ):

        config = (
            TARGET_CONFIG[
                "regime"
            ]
        )

        target = config[
            "target"
        ]

        working = (
            df[
                feature_columns
                + [target]
            ]
            .copy()
        )

        working[target] = pd.to_numeric(
            working[target],
            errors="coerce",
        )

        working = working.dropna(
            subset=[target]
        )

        X = self.sanitize_features(
            working,
            feature_columns,
        )

        y = (
            working[target]
            .astype(int)
        )

        (
            X_train,
            X_test,
            y_train,
            y_test,
        ) = self.chronological_split(
            X,
            y,
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "INDEX REGIME MODEL"
        )

        print(
            "=" * 70
        )

        print(
            f"Train rows: {len(X_train)}"
        )

        print(
            f"Test rows: {len(X_test)}"
        )

        print(
            "\nTraining distribution:"
        )

        print(
            y_train
            .map(config["labels"])
            .value_counts()
            .reindex(
                [
                    "BEAR",
                    "SIDEWAYS",
                    "BULL",
                ],
                fill_value=0,
            )
            .to_string()
        )

        print(
            "\nTesting distribution:"
        )

        print(
            y_test
            .map(config["labels"])
            .value_counts()
            .reindex(
                [
                    "BEAR",
                    "SIDEWAYS",
                    "BULL",
                ],
                fill_value=0,
            )
            .to_string()
        )

        model = (
            RandomForestClassifier(
                n_estimators=500,
                max_depth=12,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )
        )

        print(
            "\n[INDEX-TRAIN] "
            "Training regime model..."
        )

        model.fit(
            X_train,
            y_train,
        )

        predictions = (
            model.predict(
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
            f"\nAccuracy: "
            f"{accuracy:.4f}"
        )

        print(
            f"Balanced accuracy: "
            f"{balanced_accuracy:.4f}"
        )

        print(
            f"Macro F1: "
            f"{macro_f1:.4f}"
        )

        print(
            "\nClassification report:"
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
                    "BEAR",
                    "SIDEWAYS",
                    "BULL",
                ],
                zero_division=0,
            )
        )

        print(
            "Confusion matrix:"
        )

        print(
            pd.DataFrame(
                confusion_matrix(
                    y_test,
                    predictions,
                    labels=[
                        -1,
                        0,
                        1,
                    ],
                ),
                index=[
                    "Actual BEAR",
                    "Actual SIDEWAYS",
                    "Actual BULL",
                ],
                columns=[
                    "Pred BEAR",
                    "Pred SIDEWAYS",
                    "Pred BULL",
                ],
            ).to_string()
        )

        importance = (
            pd.DataFrame(
                {
                    "feature":
                        feature_columns,

                    "importance":
                        model.feature_importances_,
                }
            )
            .sort_values(
                "importance",
                ascending=False,
            )
        )

        print(
            "\nTop features:"
        )

        print(
            importance
            .head(15)
            .to_string(
                index=False
            )
        )

        metrics = {
            "accuracy":
                float(accuracy),

            "balanced_accuracy":
                float(
                    balanced_accuracy
                ),

            "macro_f1":
                float(macro_f1),

            "train_rows":
                int(len(X_train)),

            "test_rows":
                int(len(X_test)),

            "feature_count":
                int(
                    len(feature_columns)
                ),
        }

        self.save_classification_model(
            config=config,
            model=model,
            feature_columns=feature_columns,
            metrics=metrics,
        )

        return {
            "model": model,
            "metrics": metrics,
            "feature_columns":
                feature_columns,
        }

    # ========================================================
    # TRAIN VOLATILITY
    # ========================================================

    def train_volatility(
        self,
        df,
        feature_columns,
    ):

        config = (
            TARGET_CONFIG[
                "volatility"
            ]
        )

        target = config[
            "target"
        ]

        working = (
            df[
                feature_columns
                + [target]
            ]
            .copy()
        )

        working[target] = pd.to_numeric(
            working[target],
            errors="coerce",
        )

        working = working.dropna(
            subset=[target]
        )

        X = self.sanitize_features(
            working,
            feature_columns,
        )

        y = (
            working[target]
            .astype(float)
        )

        (
            X_train,
            X_test,
            y_train,
            y_test,
        ) = self.chronological_split(
            X,
            y,
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "INDEX VOLATILITY MODEL"
        )

        print(
            "=" * 70
        )

        print(
            f"Train rows: {len(X_train)}"
        )

        print(
            f"Test rows: {len(X_test)}"
        )

        print(
            f"\nTraining target mean: "
            f"{y_train.mean():.6f}"
        )

        print(
            f"Testing target mean: "
            f"{y_test.mean():.6f}"
        )

        model = (
            RandomForestRegressor(
                n_estimators=500,
                max_depth=12,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1,
            )
        )

        print(
            "\n[INDEX-TRAIN] "
            "Training volatility model..."
        )

        model.fit(
            X_train,
            y_train,
        )

        predictions = (
            model.predict(
                X_test
            )
        )

        mae = (
            mean_absolute_error(
                y_test,
                predictions,
            )
        )

        rmse = (
            float(
                np.sqrt(
                    mean_squared_error(
                        y_test,
                        predictions,
                    )
                )
            )
        )

        r2 = (
            r2_score(
                y_test,
                predictions,
            )
        )

        mean_error = (
            float(
                np.mean(
                    predictions
                    - y_test
                )
            )
        )

        print(
            f"\nMAE: "
            f"{mae:.6f}"
        )

        print(
            f"RMSE: "
            f"{rmse:.6f}"
        )

        print(
            f"R²: "
            f"{r2:.6f}"
        )

        print(
            f"Mean error: "
            f"{mean_error:.6f}"
        )

        importance = (
            pd.DataFrame(
                {
                    "feature":
                        feature_columns,

                    "importance":
                        model.feature_importances_,
                }
            )
            .sort_values(
                "importance",
                ascending=False,
            )
        )

        print(
            "\nTop features:"
        )

        print(
            importance
            .head(15)
            .to_string(
                index=False
            )
        )

        metrics = {
            "mae":
                float(mae),

            "rmse":
                float(rmse),

            "r2":
                float(r2),

            "mean_error":
                float(mean_error),

            "train_rows":
                int(len(X_train)),

            "test_rows":
                int(len(X_test)),

            "feature_count":
                int(
                    len(feature_columns)
                ),
        }

        self.save_regression_model(
            config=config,
            model=model,
            feature_columns=feature_columns,
            metrics=metrics,
        )

        return {
            "model": model,
            "metrics": metrics,
            "feature_columns":
                feature_columns,
        }

    # ========================================================
    # TRAIN ALL
    # ========================================================

    def train_all(self):

        print(
            "=" * 70
        )

        print(
            "TradingAI - NIFTY INDEX MODEL TRAINING"
        )

        print(
            "=" * 70
        )

        df = (
            self.load_dataset()
        )

        feature_columns = (
            self.select_features(
                df
            )
        )

        print(
            f"\n[INDEX-TRAIN] "
            f"Final feature count: "
            f"{len(feature_columns)}"
        )

        print(
            "\n[INDEX-TRAIN] Features:"
        )

        for feature in feature_columns:

            print(
                f"  - {feature}"
            )

        # ----------------------------------------------------
        # All three models
        # ----------------------------------------------------

        direction_result = (
            self.train_direction(
                df,
                feature_columns,
            )
        )

        regime_result = (
            self.train_regime(
                df,
                feature_columns,
            )
        )

        volatility_result = (
            self.train_volatility(
                df,
                feature_columns,
            )
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "INDEX MODEL TRAINING COMPLETE"
        )

        print(
            "=" * 70
        )

        print(
            "\nDIRECTION:"
        )

        print(
            direction_result[
                "metrics"
            ]
        )

        print(
            "\nREGIME:"
        )

        print(
            regime_result[
                "metrics"
            ]
        )

        print(
            "\nVOLATILITY:"
        )

        print(
            volatility_result[
                "metrics"
            ]
        )

        return {
            "direction":
                direction_result,

            "regime":
                regime_result,

            "volatility":
                volatility_result,
        }


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def train_index_models():

    trainer = (
        IndexModelTrainer()
    )

    return trainer.train_all()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    train_index_models()