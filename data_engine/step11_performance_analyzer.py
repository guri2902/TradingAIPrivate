from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from data_engine.prediction_tracker import PredictionTracker


BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_REPORT = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "step10_walk_forward_report.json"
)

DEFAULT_OUTPUT = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "step11_performance_analysis.json"
)

HISTORY_FILE = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "step11_trade_performance_history.parquet"
)


class TradePerformanceAnalyzer:
    """
    Step 11 measurement layer.

    This module ONLY analyzes existing backtest results.
    It does not modify TradeEngine, score weights, probability,
    risk rules, or generated trades.
    """

    TERMINAL_WINS = {
        "TARGET_1",
        "TARGET_2",
    }

    TERMINAL_LOSSES = {
        "STOP_LOSS",
    }

    def __init__(
        self,
        report_path: Path = DEFAULT_REPORT,
        tracker: PredictionTracker | None = None,
        history_path: Path = HISTORY_FILE,
    ):
        self.report_path = Path(report_path)
        self.history_path = Path(history_path)
        self.tracker = (
            tracker
            if tracker is not None
            else PredictionTracker()
        )

    def load(self) -> Dict[str, Any]:
        if not self.report_path.exists():
            raise FileNotFoundError(
                f"Walk-forward report not found: "
                f"{self.report_path}"
            )

        with self.report_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise RuntimeError(
                "Walk-forward report must be a JSON object."
            )

        return data

    @staticmethod
    def _rows(
        report: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        rows = report.get("trades") or []

        if not isinstance(rows, list):
            return []

        return [
            row
            for row in rows
            if isinstance(row, dict)
        ]

    @staticmethod
    def _number(
        value,
    ) -> Optional[float]:

        try:
            number = float(value)

            if pd.isna(number):
                return None

            return number

        except (
            TypeError,
            ValueError,
        ):
            return None

    @classmethod
    def _resolved(
        cls,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        return [
            row
            for row in rows
            if row.get("outcome")
            in (
                *cls.TERMINAL_WINS,
                *cls.TERMINAL_LOSSES,
            )
        ]

    @classmethod
    def _win_rate(
        cls,
        rows: List[Dict[str, Any]],
    ) -> float:

        resolved = cls._resolved(rows)

        if not resolved:
            return 0.0

        wins = sum(
            1
            for row in resolved
            if row.get("outcome")
            in cls.TERMINAL_WINS
        )

        return (
            wins
            / len(resolved)
            * 100.0
        )

    @classmethod
    def _avg_r(
        cls,
        rows: List[Dict[str, Any]],
    ) -> float:

        values = []

        for row in rows:

            value = cls._number(
                row.get("r_multiple")
            )

            if value is not None:
                values.append(value)

        return (
            sum(values)
            / len(values)
            if values
            else 0.0
        )

    @classmethod
    def _bucket_score(
        cls,
        score,
    ) -> str:

        value = cls._number(score)

        if value is None:
            return "UNKNOWN"

        if value < 50:
            return "<50"

        if value < 60:
            return "50-59"

        if value < 70:
            return "60-69"

        if value < 80:
            return "70-79"

        return "80+"

    @classmethod
    def _bucket_probability(
        cls,
        probability,
    ) -> str:

        value = cls._number(
            probability
        )

        if value is None:
            return "UNKNOWN"

        if value < 55:
            return "<55"

        if value < 60:
            return "55-59"

        if value < 65:
            return "60-64"

        if value < 70:
            return "65-69"

        return "70+"

    def analyze(
        self,
    ) -> Dict[str, Any]:

        report = self.load()
        rows = self._rows(report)
        resolved = self._resolved(rows)

        history_summary = self.history_summary()
        tracker_summary = self.tracker_summary()

        outcomes = Counter(
            row.get("outcome")
            for row in rows
        )

        # ----------------------------------------------------------
        # Score / probability buckets
        # ----------------------------------------------------------

        score_groups = defaultdict(list)
        probability_groups = defaultdict(list)
        type_groups = defaultdict(list)
        rr_groups = defaultdict(list)

        for row in rows:

            score_groups[
                self._bucket_score(
                    row.get("ai_score")
                )
            ].append(row)

            probability_groups[
                self._bucket_probability(
                    row.get("probability")
                )
            ].append(row)

            option_type = str(
                row.get("type")
                or "UNKNOWN"
            ).upper()

            type_groups[
                option_type
            ].append(row)

            rr_value = self._number(
                row.get("rr")
            )

            rr_bucket = (
                "UNKNOWN"
                if rr_value is None
                else (
                    "<1.5"
                    if rr_value < 1.5
                    else "1.5-2"
                    if rr_value < 2
                    else "2-2.5"
                    if rr_value < 2.5
                    else "2.5+"
                )
            )

            rr_groups[
                rr_bucket
            ].append(row)

        def summarize_group(
            group_rows,
        ):

            return {
                "count":
                    len(group_rows),
                "resolved":
                    len(
                        self._resolved(
                            group_rows
                        )
                    ),
                "win_rate":
                    round(
                        self._win_rate(
                            group_rows
                        ),
                        2,
                    ),
                "average_r":
                    round(
                        self._avg_r(
                            group_rows
                        ),
                        4,
                    ),
            }

        score_analysis = {
            key:
                summarize_group(value)
            for key, value
            in sorted(
                score_groups.items()
            )
        }

        probability_analysis = {
            key:
                summarize_group(value)
            for key, value
            in sorted(
                probability_groups.items()
            )
        }

        type_analysis = {
            key:
                summarize_group(value)
            for key, value
            in sorted(
                type_groups.items()
            )
        }

        rr_analysis = {
            key:
                summarize_group(value)
            for key, value
            in sorted(
                rr_groups.items()
            )
        }

        # ----------------------------------------------------------
        # Basic data-quality checks
        # ----------------------------------------------------------

        probability_values = [
            self._number(
                row.get("probability")
            )
            for row in rows
        ]

        probability_values = [
            value
            for value in probability_values
            if value is not None
        ]

        probability_range = (
            {
                "min":
                    min(
                        probability_values
                    ),
                "max":
                    max(
                        probability_values
                    ),
                "mean":
                    sum(
                        probability_values
                    )
                    / len(
                        probability_values
                    ),
            }
            if probability_values
            else {}
        )

        # ----------------------------------------------------------
        # Evidence-based findings
        #
        # We do NOT recommend changing weights unless there is enough
        # resolved data. This prevents tuning on tiny samples.
        # ----------------------------------------------------------

        findings = []

        resolved_for_gate = int(
            history_summary.get(
                "resolved",
                len(resolved),
            )
        )

        if resolved_for_gate < 30:

            findings.append(
                {
                    "type":
                        "INSUFFICIENT_RESOLVED_DATA",
                    "message":
                        (
                            "Fewer than 30 resolved trades are "
                            "available. Do not modify score or "
                            "probability rules from this sample."
                        ),
                }
            )

        else:

            findings.append(
                {
                    "type":
                        "READY_FOR_CONTROLLED_REVIEW",
                    "message":
                        (
                            "There is enough resolved data for "
                            "a controlled comparison of buckets."
                        ),
                }
            )

        if (
            probability_values
            and (
                max(probability_values)
                - min(probability_values)
            ) < 10
        ):

            findings.append(
                {
                    "type":
                        "LOW_PROBABILITY_VARIATION",
                    "message":
                        (
                            "Predicted probabilities have a narrow "
                            "range. Calibration quality cannot be "
                            "judged from score alone."
                        ),
                }
            )

        score_rank = sorted(
            (
                (
                    summary["average_r"],
                    bucket,
                    summary["count"],
                    summary["resolved"],
                )
                for bucket, summary
                in score_analysis.items()
                if summary["resolved"] > 0
            ),
            reverse=True,
        )

        if score_rank:

            findings.append(
                {
                    "type":
                        "BEST_RESOLVED_SCORE_BUCKET",
                    "bucket":
                        score_rank[0][1],
                    "average_r":
                        score_rank[0][0],
                    "count":
                        score_rank[0][2],
                    "resolved":
                        score_rank[0][3],
                }
            )

        return {
            "source_report":
                str(self.report_path),
            "persistent_history":
                history_summary,
            "prediction_tracker":
                tracker_summary,
            "total_candidates":
                len(rows),
            "resolved":
                len(resolved),
            "pending_or_unresolved":
                len(rows)
                - len(resolved),
            "overall_win_rate":
                round(
                    self._win_rate(rows),
                    2,
                ),
            "overall_average_r":
                round(
                    self._avg_r(rows),
                    4,
                ),
            "outcomes":
                dict(outcomes),
            "probability_range":
                probability_range,
            "score_analysis":
                score_analysis,
            "probability_analysis":
                probability_analysis,
            "option_type_analysis":
                type_analysis,
            "rr_analysis":
                rr_analysis,
            "findings":
                findings,
            "recommendation":
                (
                    "MEASURE_MORE"
                    if len(resolved) < 30
                    else "CONTROLLED_EXPERIMENTS_ALLOWED"
                ),
        }

    def history_summary(
        self,
    ) -> Dict[str, Any]:
        """
        Read the persistent Step 11 trade-performance history.

        This is read-only and does not change the Parquet file.
        """

        if not self.history_path.exists():
            return {
                "available": False,
                "rows": 0,
                "resolved": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "average_r": 0.0,
            }

        try:
            df = pd.read_parquet(
                self.history_path
            )
        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "rows": 0,
                "resolved": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "average_r": 0.0,
            }

        if df.empty:
            return {
                "available": True,
                "rows": 0,
                "resolved": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "average_r": 0.0,
            }

        if "outcome" in df.columns:
            resolved = df[
                df["outcome"].isin(
                    [
                        "TARGET_1",
                        "TARGET_2",
                        "STOP_LOSS",
                    ]
                )
            ]
        else:
            resolved = df.iloc[0:0]

        wins = (
            resolved[
                resolved["outcome"].isin(
                    [
                        "TARGET_1",
                        "TARGET_2",
                    ]
                )
            ]
            if not resolved.empty
            else resolved
        )

        losses = (
            resolved[
                resolved["outcome"].eq(
                    "STOP_LOSS"
                )
            ]
            if not resolved.empty
            else resolved
        )

        if "r_multiple" in df.columns:
            r_values = pd.to_numeric(
                df["r_multiple"],
                errors="coerce",
            ).dropna()
        else:
            r_values = pd.Series(
                dtype=float
            )

        return {
            "available": True,
            "rows": int(len(df)),
            "resolved": int(len(resolved)),
            "wins": int(len(wins)),
            "losses": int(len(losses)),
            "win_rate": (
                round(
                    len(wins)
                    / len(resolved)
                    * 100.0,
                    2,
                )
                if len(resolved)
                else 0.0
            ),
            "average_r": (
                round(
                    float(r_values.mean()),
                    4,
                )
                if len(r_values)
                else 0.0
            ),
        }

    def tracker_summary(
        self,
    ) -> Dict[str, Any]:
        """
        Read the existing PredictionTracker directly.

        This intentionally uses the same calls that were already
        verified independently in the project.
        """

        try:
            tracker = (
                self.tracker
                if self.tracker is not None
                else PredictionTracker()
            )

            predictions = tracker.load_predictions()
            pending = tracker.load_pending()

        except Exception as exc:
            return {
                "available": False,
                "error": str(exc),
                "prediction_records": 0,
                "pending_records": 0,
                "resolved_records": 0,
                "direction_accuracy": None,
                "average_actual_return": None,
            }

        if predictions is None:
            predictions = pd.DataFrame()

        if pending is None:
            pending = pd.DataFrame()

        resolved_records = 0

        if (
            not predictions.empty
            and "outcome_recorded"
            in predictions.columns
        ):
            resolved_records = int(
                (
                    predictions[
                        "outcome_recorded"
                    ]
                    == True
                ).sum()
            )

        direction_accuracy = None

        if (
            not predictions.empty
            and "direction_correct"
            in predictions.columns
        ):
            values = predictions[
                predictions[
                    "direction_correct"
                ].notna()
            ][
                "direction_correct"
            ]

            if len(values):
                direction_accuracy = float(
                    values.mean()
                )

        average_actual_return = None

        if (
            not predictions.empty
            and "actual_return"
            in predictions.columns
        ):
            values = pd.to_numeric(
                predictions[
                    "actual_return"
                ],
                errors="coerce",
            ).dropna()

            if len(values):
                average_actual_return = float(
                    values.mean()
                )

        return {
            "available": True,
            "prediction_records":
                int(len(predictions)),
            "pending_records":
                int(len(pending)),
            "resolved_records":
                int(resolved_records),
            "direction_accuracy":
                direction_accuracy,
            "average_actual_return":
                average_actual_return,
        }

    def save(
        self,
        output_path: Path = DEFAULT_OUTPUT,
    ) -> Path:

        analysis = self.analyze()

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                analysis,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        return output_path


def main():

    analyzer = TradePerformanceAnalyzer()

    report = analyzer.analyze()

    print("=" * 70)
    print(
        "TradingAI - STEP 11 PERFORMANCE ANALYSIS"
    )
    print("=" * 70)

    print(
        f"Candidates: "
        f"{report['total_candidates']}"
    )

    print(
        f"Resolved: "
        f"{report['resolved']}"
    )

    print(
        f"Win rate: "
        f"{report['overall_win_rate']}%"
    )

    print(
        f"Average R: "
        f"{report['overall_average_r']}"
    )

    print(
        f"Recommendation: "
        f"{report['recommendation']}"
    )

    print("\nOutcomes:")

    for key, value in sorted(
        report["outcomes"].items(),
        key=lambda item: str(item[0]),
    ):
        print(
            f"  {key}: {value}"
        )

    print("\nScore buckets:")

    for key, value in report[
        "score_analysis"
    ].items():
        print(
            f"  {key}: "
            f"count={value['count']} "
            f"resolved={value['resolved']} "
            f"win_rate={value['win_rate']}% "
            f"avg_R={value['average_r']}"
        )

    print("\nProbability buckets:")

    for key, value in report[
        "probability_analysis"
    ].items():
        print(
            f"  {key}: "
            f"count={value['count']} "
            f"resolved={value['resolved']} "
            f"win_rate={value['win_rate']}% "
            f"avg_R={value['average_r']}"
        )

    print("\nOption type:")

    for key, value in report[
        "option_type_analysis"
    ].items():
        print(
            f"  {key}: "
            f"count={value['count']} "
            f"resolved={value['resolved']} "
            f"win_rate={value['win_rate']}% "
            f"avg_R={value['average_r']}"
        )

    print("\nFindings:")

    for finding in report[
        "findings"
    ]:
        print(
            f"  - {finding}"
        )

    output = analyzer.save()

    print(
        f"\nSaved: {output}"
    )


if __name__ == "__main__":
    main()