# ============================================================
# TradingAI - WEAKNESS DETECTOR
# ============================================================

import json
from pathlib import Path


class WeaknessDetector:

    def __init__(
        self,
        minimum_sample_size=20,
        severe_accuracy_threshold=0.45,
        weak_accuracy_threshold=0.55,
        overconfidence_gap=0.10,
        volatility_mae_threshold=0.05,
    ):

        self.minimum_sample_size = int(
            minimum_sample_size
        )

        self.severe_accuracy_threshold = float(
            severe_accuracy_threshold
        )

        self.weak_accuracy_threshold = float(
            weak_accuracy_threshold
        )

        self.overconfidence_gap = float(
            overconfidence_gap
        )

        self.volatility_mae_threshold = float(
            volatility_mae_threshold
        )

    # ========================================================
    # SAMPLE CHECK
    # ========================================================

    def _valid(
        self,
        metric,
    ):

        if not isinstance(
            metric,
            dict
        ):
            return False

        sample_size = metric.get(
            "sample_size",
            0
        )

        status = metric.get(
            "status"
        )

        return (
            sample_size
            >= self.minimum_sample_size
            and status
            == "VALID_SAMPLE"
        )

    # ========================================================
    # DIRECTION WEAKNESSES
    # ========================================================

    def detect_direction_weaknesses(
        self,
        direction,
    ):

        weaknesses = []

        if not self._valid(
            direction
        ):

            return weaknesses

        accuracy = direction.get(
            "accuracy"
        )

        up_accuracy = direction.get(
            "up_accuracy"
        )

        down_accuracy = direction.get(
            "down_accuracy"
        )

        if (
            accuracy is not None
            and accuracy
            < self.severe_accuracy_threshold
        ):

            weaknesses.append({
                "type":
                    "DIRECTION_LOW_ACCURACY",

                "severity":
                    "HIGH",

                "message":
                    f"Direction accuracy is "
                    f"{accuracy:.2%}.",

                "metric":
                    accuracy,
            })

        elif (
            accuracy is not None
            and accuracy
            < self.weak_accuracy_threshold
        ):

            weaknesses.append({
                "type":
                    "DIRECTION_WEAK_ACCURACY",

                "severity":
                    "MEDIUM",

                "message":
                    f"Direction accuracy is "
                    f"{accuracy:.2%}.",

                "metric":
                    accuracy,
            })

        if (
            up_accuracy is not None
            and down_accuracy is not None
        ):

            difference = abs(
                up_accuracy
                - down_accuracy
            )

            if difference >= 0.15:

                weaker_side = (
                    "UP"
                    if up_accuracy
                    < down_accuracy
                    else "DOWN"
                )

                weaker_accuracy = (
                    up_accuracy
                    if weaker_side == "UP"
                    else down_accuracy
                )

                weaknesses.append({
                    "type":
                        "DIRECTION_ASYMMETRY",

                    "severity":
                        "MEDIUM",

                    "message":
                        f"{weaker_side} direction "
                        f"accuracy is weaker at "
                        f"{weaker_accuracy:.2%}.",

                    "metric":
                        weaker_accuracy,
                })

        return weaknesses

    # ========================================================
    # CONFIDENCE WEAKNESSES
    # ========================================================

    def detect_confidence_weaknesses(
        self,
        confidence,
    ):

        weaknesses = []

        if not self._valid(
            confidence
        ):

            return weaknesses

        average_confidence = confidence.get(
            "average_confidence"
        )

        actual_accuracy = confidence.get(
            "actual_accuracy"
        )

        confidence_gap = confidence.get(
            "confidence_gap"
        )

        if (
            confidence_gap is not None
            and confidence_gap
            >= self.overconfidence_gap
        ):

            weaknesses.append({
                "type":
                    "MODEL_OVERCONFIDENCE",

                "severity":
                    "HIGH",

                "message":
                    f"Average confidence exceeds "
                    f"actual accuracy by "
                    f"{confidence_gap:.2%}.",

                "metric":
                    confidence_gap,
            })

        if (
            average_confidence is not None
            and actual_accuracy is not None
            and average_confidence
            < actual_accuracy - 0.10
        ):

            weaknesses.append({
                "type":
                    "MODEL_UNDERCONFIDENCE",

                "severity":
                    "MEDIUM",

                "message":
                    f"Average confidence "
                    f"({average_confidence:.2%}) "
                    f"is materially below actual "
                    f"accuracy "
                    f"({actual_accuracy:.2%}).",

                "metric":
                    average_confidence,
            })

        return weaknesses

    # ========================================================
    # VOLATILITY WEAKNESSES
    # ========================================================

    def detect_volatility_weaknesses(
        self,
        volatility,
    ):

        weaknesses = []

        if not self._valid(
            volatility
        ):

            return weaknesses

        mae = volatility.get(
            "mae"
        )

        rmse = volatility.get(
            "rmse"
        )

        average_error = volatility.get(
            "average_error"
        )

        if (
            mae is not None
            and mae
            > self.volatility_mae_threshold
        ):

            weaknesses.append({
                "type":
                    "VOLATILITY_HIGH_ERROR",

                "severity":
                    "MEDIUM",

                "message":
                    f"Volatility MAE is "
                    f"{mae:.4f}.",

                "metric":
                    mae,
            })

        if (
            average_error is not None
            and abs(average_error)
            > self.volatility_mae_threshold
        ):

            direction = (
                "overpredicting"
                if average_error > 0
                else "underpredicting"
            )

            weaknesses.append({
                "type":
                    "VOLATILITY_BIAS",

                "severity":
                    "MEDIUM",

                "message":
                    f"Volatility model is "
                    f"{direction} on average "
                    f"by {abs(average_error):.4f}.",

                "metric":
                    average_error,
            })

        return weaknesses

    # ========================================================
    # SIGNAL WEAKNESSES
    # ========================================================

    def detect_signal_weaknesses(
        self,
        signal_performance,
    ):

        weaknesses = []

        if not isinstance(
            signal_performance,
            dict
        ):

            return weaknesses

        for signal, metrics in (
            signal_performance.items()
        ):

            if not self._valid(
                metrics
            ):

                continue

            accuracy = metrics.get(
                "accuracy"
            )

            if (
                accuracy is not None
                and accuracy
                < self.severe_accuracy_threshold
            ):

                weaknesses.append({
                    "type":
                        "SIGNAL_LOW_ACCURACY",

                    "severity":
                        "HIGH",

                    "message":
                        f"{signal} signal accuracy "
                        f"is {accuracy:.2%}.",

                    "signal":
                        signal,

                    "metric":
                        accuracy,
                })

            elif (
                accuracy is not None
                and accuracy
                < self.weak_accuracy_threshold
            ):

                weaknesses.append({
                    "type":
                        "SIGNAL_WEAK_ACCURACY",

                    "severity":
                        "MEDIUM",

                    "message":
                        f"{signal} signal accuracy "
                        f"is {accuracy:.2%}.",

                    "signal":
                        signal,

                    "metric":
                        accuracy,
                })

        return weaknesses

    # ========================================================
    # SCORE BUCKET WEAKNESSES
    # ========================================================

    def detect_score_weaknesses(
        self,
        score_buckets,
    ):

        weaknesses = []

        if not isinstance(
            score_buckets,
            dict
        ):

            return weaknesses

        for bucket, metrics in (
            score_buckets.items()
        ):

            if not self._valid(
                metrics
            ):

                continue

            accuracy = metrics.get(
                "accuracy"
            )

            if (
                accuracy is not None
                and accuracy
                < self.weak_accuracy_threshold
            ):

                weaknesses.append({
                    "type":
                        "SCORE_BUCKET_WEAKNESS",

                    "severity":
                        "MEDIUM",

                    "message":
                        f"{bucket} score bucket "
                        f"has accuracy "
                        f"{accuracy:.2%}.",

                    "bucket":
                        bucket,

                    "metric":
                        accuracy,
                })

        return weaknesses

    # ========================================================
    # FULL ANALYSIS
    # ========================================================

    def analyze(
        self,
        evaluation_report,
    ):

        if not isinstance(
            evaluation_report,
            dict
        ):

            raise TypeError(
                "evaluation_report must be a dictionary."
            )

        weaknesses = []

        weaknesses.extend(
            self.detect_direction_weaknesses(
                evaluation_report.get(
                    "direction",
                    {}
                )
            )
        )

        weaknesses.extend(
            self.detect_confidence_weaknesses(
                evaluation_report.get(
                    "confidence",
                    {}
                )
            )
        )

        weaknesses.extend(
            self.detect_volatility_weaknesses(
                evaluation_report.get(
                    "volatility",
                    {}
                )
            )
        )

        weaknesses.extend(
            self.detect_signal_weaknesses(
                evaluation_report.get(
                    "signal_performance",
                    {}
                )
            )
        )

        weaknesses.extend(
            self.detect_score_weaknesses(
                evaluation_report.get(
                    "score_buckets",
                    {}
                )
            )
        )

        # ----------------------------------------------------
        # Severity ordering
        # ----------------------------------------------------

        severity_rank = {
            "HIGH": 0,
            "MEDIUM": 1,
            "LOW": 2,
        }

        weaknesses.sort(
            key=lambda item:
            severity_rank.get(
                item.get(
                    "severity",
                    "LOW"
                ),
                3,
            )
        )

        high_count = sum(
            1
            for item in weaknesses
            if item.get(
                "severity"
            ) == "HIGH"
        )

        medium_count = sum(
            1
            for item in weaknesses
            if item.get(
                "severity"
            ) == "MEDIUM"
        )

        valid_evidence = (
            evaluation_report.get(
                "direction",
                {}
            ).get(
                "status"
            ) == "VALID_SAMPLE"
            or
            evaluation_report.get(
                "confidence",
                {}
            ).get(
                "status"
            ) == "VALID_SAMPLE"
            or
            evaluation_report.get(
                "volatility",
                {}
            ).get(
                "status"
            ) == "VALID_SAMPLE"
        )

        if not valid_evidence:

            overall_status = (
                "INSUFFICIENT_EVIDENCE"
            )

        elif high_count > 0:

            overall_status = "HIGH_RISK"

        elif medium_count > 0:

            overall_status = "WEAKNESSES_DETECTED"

        else:

            overall_status = "NO_MAJOR_WEAKNESSES"

        return {
            "status":
                overall_status,

            "high_count":
                high_count,

            "medium_count":
                medium_count,

            "total_weaknesses":
                len(weaknesses),

            "weaknesses":
                weaknesses,
        }

    # ========================================================
    # SAVE REPORT
    # ========================================================

    def save_report(
        self,
        analysis,
        path=(
            "market_data/predictions/"
            "weakness_report.json"
        ),
    ):

        output_path = Path(
            path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                analysis,
                file,
                indent=4,
            )

        return output_path

    # ========================================================
    # PRINT REPORT
    # ========================================================

    @staticmethod
    def print_report(
        analysis,
    ):

        print("=" * 70)
        print("TradingAI - WEAKNESS DETECTION")
        print("=" * 70)

        print(
            f"\nStatus: "
            f"{analysis['status']}"
        )

        print(
            f"High severity: "
            f"{analysis['high_count']}"
        )

        print(
            f"Medium severity: "
            f"{analysis['medium_count']}"
        )

        print(
            f"Total weaknesses: "
            f"{analysis['total_weaknesses']}"
        )

        if not analysis[
            "weaknesses"
        ]:

            print(
                "\nNo weaknesses detected "
                "from sufficient evidence."
            )

            return

        print(
            "\nDETECTED WEAKNESSES:"
        )

        for index, item in enumerate(
            analysis[
                "weaknesses"
            ],
            start=1,
        ):

            print(
                f"\n{index}. "
                f"[{item['severity']}] "
                f"{item['type']}"
            )

            print(
                f"   {item['message']}"
            )

            if "signal" in item:

                print(
                    f"   Signal: "
                    f"{item['signal']}"
                )

            if "bucket" in item:

                print(
                    f"   Bucket: "
                    f"{item['bucket']}"
                )