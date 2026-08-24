# ============================================================
# TradingAI - MODEL EVALUATOR
# ============================================================

from pathlib import Path

import pandas as pd


class ModelEvaluator:

    def __init__(
        self,
        prediction_file=(
            "market_data/predictions/"
            "prediction_log.parquet"
        ),
        minimum_sample_size=20,
    ):

        self.prediction_file = Path(
            prediction_file
        )

        self.minimum_sample_size = int(
            minimum_sample_size
        )

    # ========================================================
    # LOAD
    # ========================================================

    def load_predictions(self):

        if not self.prediction_file.exists():

            return pd.DataFrame()

        df = pd.read_parquet(
            self.prediction_file
        )

        if df.empty:

            return df

        if "outcome_recorded" in df.columns:

            df = df[
                df["outcome_recorded"] == True
            ].copy()

        return df.reset_index(
            drop=True
        )

    # ========================================================
    # SAMPLE STATUS
    # ========================================================

    def sample_status(
        self,
        sample_size,
    ):

        if sample_size < self.minimum_sample_size:

            return "INSUFFICIENT_SAMPLE"

        return "VALID_SAMPLE"

    # ========================================================
    # DIRECTION EVALUATION
    # ========================================================

    def evaluate_direction(
        self,
        df,
    ):

        if df.empty:

            return {
                "sample_size": 0,
                "accuracy": None,
                "up_accuracy": None,
                "down_accuracy": None,
                "status": "NO_DATA",
            }

        required = [
            "direction_prediction",
            "actual_direction",
        ]

        data = df.dropna(
            subset=required
        ).copy()

        if data.empty:

            return {
                "sample_size": 0,
                "accuracy": None,
                "up_accuracy": None,
                "down_accuracy": None,
                "status": "NO_DATA",
            }

        # Ignore FLAT actual outcomes for binary direction accuracy.
        binary = data[
            data["actual_direction"].isin(
                [0, 1]
            )
            & data["direction_prediction"].isin(
                [0, 1]
            )
        ].copy()

        if binary.empty:

            return {
                "sample_size": 0,
                "accuracy": None,
                "up_accuracy": None,
                "down_accuracy": None,
                "status": "NO_DATA",
            }

        binary["correct"] = (
            binary["direction_prediction"]
            == binary["actual_direction"]
        )

        accuracy = float(
            binary["correct"].mean()
        )

        up = binary[
            binary["actual_direction"] == 1
        ]

        down = binary[
            binary["actual_direction"] == 0
        ]

        up_accuracy = (
            float(up["correct"].mean())
            if not up.empty
            else None
        )

        down_accuracy = (
            float(down["correct"].mean())
            if not down.empty
            else None
        )

        return {
            "sample_size": int(
                len(binary)
            ),
            "accuracy": accuracy,
            "up_accuracy": up_accuracy,
            "down_accuracy": down_accuracy,
            "status": self.sample_status(
                len(binary)
            ),
        }

    # ========================================================
    # CONFIDENCE CALIBRATION
    # ========================================================

    def evaluate_confidence(
        self,
        df,
    ):

        required = [
            "confidence",
            "direction_correct",
        ]

        if df.empty or any(
            column not in df.columns
            for column in required
        ):

            return {
                "sample_size": 0,
                "average_confidence": None,
                "actual_accuracy": None,
                "confidence_gap": None,
                "status": "NO_DATA",
            }

        data = df.dropna(
            subset=required
        ).copy()

        if data.empty:

            return {
                "sample_size": 0,
                "average_confidence": None,
                "actual_accuracy": None,
                "confidence_gap": None,
                "status": "NO_DATA",
            }

        data["confidence"] = pd.to_numeric(
            data["confidence"],
            errors="coerce",
        )

        data["direction_correct"] = (
            data["direction_correct"]
            .astype(bool)
        )

        data = data.dropna(
            subset=["confidence"]
        )

        if data.empty:

            return {
                "sample_size": 0,
                "average_confidence": None,
                "actual_accuracy": None,
                "confidence_gap": None,
                "status": "NO_DATA",
            }

        average_confidence = float(
            data["confidence"].mean()
        )

        actual_accuracy = float(
            data["direction_correct"].mean()
        )

        confidence_gap = (
            average_confidence
            - actual_accuracy
        )

        return {
            "sample_size": int(
                len(data)
            ),
            "average_confidence":
                average_confidence,
            "actual_accuracy":
                actual_accuracy,
            "confidence_gap":
                confidence_gap,
            "status":
                self.sample_status(
                    len(data)
                ),
        }

    # ========================================================
    # VOLATILITY EVALUATION
    # ========================================================

    def evaluate_volatility(
        self,
        df,
    ):

        required = [
            "predicted_volatility",
            "actual_volatility",
        ]

        if df.empty or any(
            column not in df.columns
            for column in required
        ):

            return {
                "sample_size": 0,
                "mae": None,
                "rmse": None,
                "average_error": None,
                "status": "NO_DATA",
            }

        data = df.dropna(
            subset=required
        ).copy()

        if data.empty:

            return {
                "sample_size": 0,
                "mae": None,
                "rmse": None,
                "average_error": None,
                "status": "NO_DATA",
            }

        predicted = pd.to_numeric(
            data["predicted_volatility"],
            errors="coerce",
        )

        actual = pd.to_numeric(
            data["actual_volatility"],
            errors="coerce",
        )

        valid = (
            predicted.notna()
            & actual.notna()
        )

        predicted = predicted[
            valid
        ]

        actual = actual[
            valid
        ]

        if predicted.empty:

            return {
                "sample_size": 0,
                "mae": None,
                "rmse": None,
                "average_error": None,
                "status": "NO_DATA",
            }

        errors = (
            predicted
            - actual
        )

        mae = float(
            errors.abs().mean()
        )

        rmse = float(
            (
                errors ** 2
            )
            .mean()
            ** 0.5
        )

        average_error = float(
            errors.mean()
        )

        return {
            "sample_size": int(
                len(errors)
            ),
            "mae": mae,
            "rmse": rmse,
            "average_error":
                average_error,
            "status":
                self.sample_status(
                    len(errors)
                ),
        }

    # ========================================================
    # SIGNAL PERFORMANCE
    # ========================================================

    def evaluate_signal(
        self,
        df,
    ):

        if df.empty:

            return {}

        data = df.copy()

        if "signal" not in data.columns:

            return {}

        groups = {}

        for signal, group in data.groupby(
            "signal"
        ):

            sample_size = len(
                group
            )

            accuracy = None

            if (
                "direction_correct"
                in group.columns
            ):

                values = group[
                    "direction_correct"
                ].dropna()

                if not values.empty:

                    accuracy = float(
                        values
                        .astype(bool)
                        .mean()
                    )

            average_return = None

            if (
                "actual_return"
                in group.columns
            ):

                values = pd.to_numeric(
                    group[
                        "actual_return"
                    ],
                    errors="coerce",
                ).dropna()

                if not values.empty:

                    average_return = float(
                        values.mean()
                    )

            groups[str(signal)] = {
                "sample_size":
                    sample_size,
                "accuracy":
                    accuracy,
                "average_actual_return":
                    average_return,
                "status":
                    self.sample_status(
                        sample_size
                    ),
            }

        return groups

    # ========================================================
    # SCORE BUCKET PERFORMANCE
    # ========================================================

    def evaluate_score_buckets(
        self,
        df,
    ):

        if (
            df.empty
            or "combined_score"
            not in df.columns
        ):

            return {}

        data = df.copy()

        data[
            "combined_score"
        ] = pd.to_numeric(
            data[
                "combined_score"
            ],
            errors="coerce",
        )

        data = data.dropna(
            subset=[
                "combined_score"
            ]
        )

        if data.empty:

            return {}

        bins = [
            -1.0,
            -0.60,
            -0.35,
            -0.20,
            0.20,
            0.35,
            0.60,
            1.0,
        ]

        labels = [
            "STRONG_BEARISH",
            "MODERATE_BEARISH",
            "WEAK_BEARISH",
            "NEUTRAL",
            "WEAK_BULLISH",
            "MODERATE_BULLISH",
            "STRONG_BULLISH",
        ]

        data["score_bucket"] = pd.cut(
            data["combined_score"],
            bins=bins,
            labels=labels,
            include_lowest=True,
        )

        results = {}

        for bucket, group in data.groupby(
            "score_bucket",
            observed=True,
        ):

            sample_size = len(
                group
            )

            accuracy = None

            if (
                "direction_correct"
                in group.columns
            ):

                values = group[
                    "direction_correct"
                ].dropna()

                if not values.empty:

                    accuracy = float(
                        values.astype(bool)
                        .mean()
                    )

            actual_return = None

            if (
                "actual_return"
                in group.columns
            ):

                values = pd.to_numeric(
                    group[
                        "actual_return"
                    ],
                    errors="coerce",
                ).dropna()

                if not values.empty:

                    actual_return = float(
                        values.mean()
                    )

            results[str(bucket)] = {
                "sample_size":
                    sample_size,
                "accuracy":
                    accuracy,
                "average_actual_return":
                    actual_return,
                "status":
                    self.sample_status(
                        sample_size
                    ),
            }

        return results

    # ========================================================
    # FULL EVALUATION
    # ========================================================

    def evaluate(
        self,
    ):

        df = self.load_predictions()

        total_predictions = 0

        if self.prediction_file.exists():

            total_df = pd.read_parquet(
                self.prediction_file
            )

            total_predictions = len(
                total_df
            )

        resolved_predictions = len(
            df
        )

        return {
            "total_predictions":
                total_predictions,

            "resolved_predictions":
                resolved_predictions,

            "pending_predictions":
                max(
                    0,
                    total_predictions
                    - resolved_predictions
                ),

            "direction":
                self.evaluate_direction(
                    df
                ),

            "confidence":
                self.evaluate_confidence(
                    df
                ),

            "volatility":
                self.evaluate_volatility(
                    df
                ),

            "signal_performance":
                self.evaluate_signal(
                    df
                ),

            "score_buckets":
                self.evaluate_score_buckets(
                    df
                ),
        }

    # ========================================================
    # PRINT REPORT
    # ========================================================

    def print_report(
        self,
        report,
    ):

        print("=" * 70)
        print("TradingAI - MODEL EVALUATION")
        print("=" * 70)

        print(
            f"\nTotal predictions: "
            f"{report['total_predictions']}"
        )

        print(
            f"Resolved predictions: "
            f"{report['resolved_predictions']}"
        )

        print(
            f"Pending predictions: "
            f"{report['pending_predictions']}"
        )

        direction = report[
            "direction"
        ]

        print("\nDIRECTION")

        print(
            f"Sample size: "
            f"{direction['sample_size']}"
        )

        print(
            f"Accuracy: "
            f"{direction['accuracy']}"
        )

        print(
            f"UP accuracy: "
            f"{direction['up_accuracy']}"
        )

        print(
            f"DOWN accuracy: "
            f"{direction['down_accuracy']}"
        )

        print(
            f"Status: "
            f"{direction['status']}"
        )

        confidence = report[
            "confidence"
        ]

        print("\nCONFIDENCE")

        print(
            f"Average confidence: "
            f"{confidence['average_confidence']}"
        )

        print(
            f"Actual accuracy: "
            f"{confidence['actual_accuracy']}"
        )

        print(
            f"Confidence gap: "
            f"{confidence['confidence_gap']}"
        )

        print(
            f"Status: "
            f"{confidence['status']}"
        )

        volatility = report[
            "volatility"
        ]

        print("\nVOLATILITY")

        print(
            f"Sample size: "
            f"{volatility['sample_size']}"
        )

        print(
            f"MAE: "
            f"{volatility['mae']}"
        )

        print(
            f"RMSE: "
            f"{volatility['rmse']}"
        )

        print(
            f"Average error: "
            f"{volatility['average_error']}"
        )

        print(
            f"Status: "
            f"{volatility['status']}"
        )

        print("\nSIGNAL PERFORMANCE")

        for signal, values in report[
            "signal_performance"
        ].items():

            print(
                f"{signal}: "
                f"{values}"
            )

        print("\nSCORE BUCKETS")

        for bucket, values in report[
            "score_buckets"
        ].items():

            print(
                f"{bucket}: "
                f"{values}"
            )