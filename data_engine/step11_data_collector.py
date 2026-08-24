from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from data_engine.prediction_tracker import PredictionTracker


BASE_DIR = Path(__file__).resolve().parent.parent

WALK_FORWARD_REPORT = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "step10_walk_forward_report.json"
)

HISTORY_FILE = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "step11_trade_performance_history.parquet"
)


class Step11DataCollector:
    """
    Persistent evidence collector for Step 11.

    Sources:
      1. Step 10 walk-forward trade results.
      2. Existing PredictionTracker statistics.

    The collector is append-only at the logical trade level and
    de-duplicates imported walk-forward trades using a stable key.
    It does NOT modify TradeEngine or PredictionTracker records.
    """

    def __init__(
        self,
        walk_forward_report: Path = WALK_FORWARD_REPORT,
        history_file: Path = HISTORY_FILE,
    ):
        self.walk_forward_report = Path(
            walk_forward_report
        )
        self.history_file = Path(
            history_file
        )
        self.history_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.tracker = PredictionTracker()

    def _load_report(self) -> Dict[str, Any]:
        if not self.walk_forward_report.exists():
            raise FileNotFoundError(
                f"Walk-forward report not found: "
                f"{self.walk_forward_report}"
            )

        return json.loads(
            self.walk_forward_report.read_text(
                encoding="utf-8"
            )
        )

    def _load_history(self) -> pd.DataFrame:
        if not self.history_file.exists():
            return pd.DataFrame()

        try:
            return pd.read_parquet(
                self.history_file
            )
        except Exception as exc:
            raise RuntimeError(
                f"Could not read performance history: {exc}"
            ) from exc

    @staticmethod
    def _stable_key(
        row: Dict[str, Any]
    ) -> str:

        return "|".join(
            str(
                row.get(field)
            )
            for field in (
                "window",
                "timestamp",
                "expiry",
                "strike",
                "type",
                "ai_score",
                "probability",
                "outcome",
            )
        )

    def collect_live_tracker_trades(
        self,
    ) -> int:
        """
        Import resolved option-trade predictions from the dedicated
        PredictionTracker trade ledger.

        PredictionTracker intentionally keeps option trades separate from
        the original Direction/Regime/Volatility prediction ledger.
        """

        try:
            if hasattr(
                self.tracker,
                "load_trade_predictions",
            ):
                tracker_df = (
                    self.tracker.load_trade_predictions()
                )
            else:
                return 0

        except Exception as exc:
            print(
                "[STEP11] Trade ledger read failed:",
                exc,
            )
            return 0

        if (
            tracker_df is None
            or tracker_df.empty
        ):
            return 0

        # The dedicated trade ledger already contains the exact fields
        # needed by Step 11:
        # strike, type, ai_score, probability, outcome, etc.
        required_fields = {
            "prediction_id",
            "generated_at",
            "symbol",
            "strike",
            "type",
            "ai_score",
            "probability",
            "outcome",
            "outcome_recorded",
        }

        if not required_fields.issubset(
            set(tracker_df.columns)
        ):
            return 0

        resolved = tracker_df[
            tracker_df[
                "outcome_recorded"
            ] == True
        ].copy()

        if resolved.empty:
            return 0

        existing = self._load_history()

        existing_keys = set()

        if (
            not existing.empty
            and "_stable_key" in existing.columns
        ):
            existing_keys = set(
                existing[
                    "_stable_key"
                ].astype(str).tolist()
            )

        collected_at = datetime.now().isoformat(
            timespec="seconds"
        )

        new_rows = []

        for _, source_row in resolved.iterrows():

            source = source_row.to_dict()

            # Convert the dedicated tracker schema into the existing
            # Step 11 history schema without changing the history format.
            normalized = {
                "collected_at":
                    collected_at,
                "_stable_key":
                    None,

                "window":
                    None,
                "train_snapshot_count":
                    None,
                "test_snapshot_index":
                    None,

                "timestamp":
                    source.get(
                        "generated_at"
                    ),
                "expiry":
                    source.get(
                        "expiry"
                    ),

                "strike":
                    source.get(
                        "strike"
                    ),
                "type":
                    source.get(
                        "type"
                    ),

                "ai_score":
                    source.get(
                        "ai_score"
                    ),
                "probability":
                    source.get(
                        "probability"
                    ),
                "rr":
                    (
                        source.get(
                            "risk_reward"
                        )
                        if source.get(
                            "risk_reward"
                        ) is not None
                        else source.get(
                            "rr"
                        )
                    ),

                "entry":
                    source.get(
                        "entry"
                    ),
                "stop_loss":
                    source.get(
                        "stop_loss"
                    ),
                "target1":
                    source.get(
                        "target1"
                    ),
                "target2":
                    source.get(
                        "target2"
                    ),

                "outcome":
                    source.get(
                        "outcome"
                    ),
                "outcome_price":
                    source.get(
                        "outcome_price"
                    ),
                "closed_at":
                    source.get(
                        "outcome_timestamp"
                    ),

                # Existing trade tracker currently stores the resolved
                # outcome but not an R-multiple. Calculate it from the
                # frozen entry/stop/outcome where possible.
                "r_multiple":
                    None,
            }

            entry = source.get(
                "entry"
            )
            stop_loss = source.get(
                "stop_loss"
            )
            outcome_price = source.get(
                "outcome_price"
            )

            try:
                entry = float(entry)
                stop_loss = float(stop_loss)
                outcome_price = float(
                    outcome_price
                )

                risk_per_unit = (
                    entry - stop_loss
                )

                if risk_per_unit > 0:
                    normalized[
                        "r_multiple"
                    ] = (
                        outcome_price - entry
                    ) / risk_per_unit

            except (
                TypeError,
                ValueError,
            ):
                pass

            # Use the PredictionTracker prediction_id in the stable key so
            # two otherwise identical live trades remain distinct.
            key = (
                f"live|"
                f"{source.get('prediction_id')}|"
                f"{source.get('outcome')}"
            )

            if key in existing_keys:
                continue

            normalized[
                "_stable_key"
            ] = key

            new_rows.append(
                normalized
            )

        if not new_rows:
            return 0

        incoming = pd.DataFrame(
            new_rows
        )

        if existing.empty:
            combined = incoming
        else:
            combined = pd.concat(
                [
                    existing,
                    incoming,
                ],
                ignore_index=True,
            )

        combined = (
            combined
            .drop_duplicates(
                subset=[
                    "_stable_key"
                ],
                keep="last",
            )
            .reset_index(
                drop=True
            )
        )

        combined.to_parquet(
            self.history_file,
            index=False,
        )

        return len(new_rows)

    def collect(
        self
    ) -> Dict[str, Any]:

        # Collect any newly resolved live option trades first.
        live_tracker_rows = (
            self.collect_live_tracker_trades()
        )

        report = self._load_report()

        trades = (
            report.get(
                "trades"
            )
            or []
        )

        if not isinstance(
            trades,
            list,
        ):
            trades = []

        existing = self._load_history()

        existing_keys = set()

        if not existing.empty:
            if "_stable_key" in existing.columns:
                existing_keys = set(
                    existing[
                        "_stable_key"
                    ]
                    .astype(str)
                    .tolist()
                )

        new_rows: List[Dict[str, Any]] = []

        collected_at = datetime.now().isoformat(
            timespec="seconds"
        )

        for trade in trades:

            if not isinstance(
                trade,
                dict,
            ):
                continue

            key = self._stable_key(
                trade
            )

            if key in existing_keys:
                continue

            new_rows.append(
                {
                    "collected_at":
                        collected_at,
                    "_stable_key":
                        key,

                    "window":
                        trade.get("window"),
                    "train_snapshot_count":
                        trade.get(
                            "train_snapshot_count"
                        ),
                    "test_snapshot_index":
                        trade.get(
                            "test_snapshot_index"
                        ),

                    "timestamp":
                        trade.get("timestamp"),
                    "expiry":
                        trade.get("expiry"),

                    "strike":
                        trade.get("strike"),
                    "type":
                        trade.get("type"),

                    "ai_score":
                        trade.get("ai_score"),
                    "probability":
                        trade.get("probability"),
                    "rr":
                        trade.get("rr"),

                    "entry":
                        trade.get("entry"),
                    "stop_loss":
                        trade.get("stop_loss"),
                    "target1":
                        trade.get("target1"),
                    "target2":
                        trade.get("target2"),

                    "outcome":
                        trade.get("outcome"),
                    "outcome_price":
                        trade.get(
                            "outcome_price"
                        ),
                    "closed_at":
                        trade.get("closed_at"),
                    "r_multiple":
                        trade.get(
                            "r_multiple"
                        ),
                }
            )

        if new_rows:
            incoming = pd.DataFrame(
                new_rows
            )

            combined = pd.concat(
                [
                    existing,
                    incoming,
                ],
                ignore_index=True,
            )

            combined = combined.drop_duplicates(
                subset=[
                    "_stable_key"
                ],
                keep="last",
            )

        else:
            combined = existing

        if not combined.empty:
            combined.to_parquet(
                self.history_file,
                index=False,
            )

        # ----------------------------------------------------------
        # Existing PredictionTracker evidence is read-only.
        # ----------------------------------------------------------

        tracker_df = (
            self.tracker.load_predictions()
        )

        pending_df = (
            self.tracker.load_pending()
        )

        tracker_resolved = 0

        if (
            not tracker_df.empty
            and "outcome_recorded"
            in tracker_df.columns
        ):
            tracker_resolved = int(
                (
                    tracker_df[
                        "outcome_recorded"
                    ]
                    == True
                ).sum()
            )

        return {
            "history_file":
                str(self.history_file),
            "history_rows":
                int(
                    len(combined)
                ),
            "new_rows":
                len(new_rows),
            "live_tracker_new_rows":
                int(live_tracker_rows),
            "total_walk_forward_rows":
                len(trades),
            "tracker_predictions":
                int(
                    len(tracker_df)
                ),
            "tracker_pending":
                int(
                    len(pending_df)
                ),
            "tracker_resolved":
                tracker_resolved,
        }


def main():

    collector = Step11DataCollector()

    result = collector.collect()

    print("=" * 70)
    print(
        "TradingAI - STEP 11 DATA COLLECTION"
    )
    print("=" * 70)
    print(
        f"Walk-forward rows: "
        f"{result['total_walk_forward_rows']}"
    )
    print(
        f"New performance rows: "
        f"{result['new_rows']}"
    )
    print(
        f"New live tracker rows: "
        f"{result['live_tracker_new_rows']}"
    )
    print(
        f"Stored performance rows: "
        f"{result['history_rows']}"
    )
    print(
        f"Tracker predictions: "
        f"{result['tracker_predictions']}"
    )
    print(
        f"Tracker pending: "
        f"{result['tracker_pending']}"
    )
    print(
        f"Tracker resolved: "
        f"{result['tracker_resolved']}"
    )
    print(
        f"Saved: {result['history_file']}"
    )


if __name__ == "__main__":
    main()