# ============================================================
# TradingAI - PREDICTION TRACKER
# ============================================================

import json
import os
from datetime import datetime
from uuid import uuid4
from pathlib import Path
from typing import Any, Optional

import pandas as pd


class PredictionTracker:

    def __init__(
        self,
        output_dir="market_data/predictions",
    ):

        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.prediction_file = (
            self.output_dir
            / "prediction_log.parquet"
        )

        self.pending_file = (
            self.output_dir
            / "pending_predictions.parquet"
        )

        # --------------------------------------------------------
        # STEP 8 - OPTION TRADE PREDICTION LEDGER
        #
        # Kept separate from the existing ML prediction ledger so
        # the original Direction/Regime/Volatility tracking remains
        # unchanged.
        # --------------------------------------------------------

        self.trade_prediction_file = (
            self.output_dir
            / "trade_prediction_log.parquet"
        )

        self.trade_pending_file = (
            self.output_dir
            / "pending_trade_predictions.parquet"
        )

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _safe_float(
        value,
    ):

        try:

            if value is None:
                return None

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def _safe_int(
        value,
    ):

        try:

            if value is None:
                return None

            return int(value)

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ========================================================
    # CREATE PREDICTION RECORD
    # ========================================================

    def create_record(
        self,
        symbol: str,
        prediction: dict[str, Any],
        horizon=1,
    ):

        if not symbol:

            raise ValueError(
                "symbol is required."
            )

        if not isinstance(
            prediction,
            dict,
        ):

            raise TypeError(
                "prediction must be a dictionary."
            )

        timestamp = datetime.now().isoformat()

        record = {

            "prediction_id":
                f"{symbol.upper()}_"
                f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}",

            "timestamp":
                timestamp,

            "symbol":
                str(symbol).upper(),

            "horizon":
                int(horizon),

            # ------------------------------------------------
            # Direction
            # ------------------------------------------------

            "direction_prediction":
                prediction.get(
                    "direction_prediction"
                ),

            "up_probability":
                self._safe_float(
                    prediction.get(
                        "up_probability"
                    )
                ),

            "down_probability":
                self._safe_float(
                    prediction.get(
                        "down_probability"
                    )
                ),

            # ------------------------------------------------
            # Regime
            # ------------------------------------------------

            "regime_prediction":
                prediction.get(
                    "regime_prediction"
                ),

            "bear_probability":
                self._safe_float(
                    prediction.get(
                        "bear_probability"
                    )
                ),

            "sideways_probability":
                self._safe_float(
                    prediction.get(
                        "sideways_probability"
                    )
                ),

            "bull_probability":
                self._safe_float(
                    prediction.get(
                        "bull_probability"
                    )
                ),

            # ------------------------------------------------
            # Volatility
            # ------------------------------------------------

            "predicted_volatility":
                self._safe_float(
                    prediction.get(
                        "predicted_volatility"
                    )
                ),

            "volatility_regime":
                prediction.get(
                    "volatility_regime"
                ),

            # ------------------------------------------------
            # Combined AI
            # ------------------------------------------------

            "direction_score":
                self._safe_float(
                    prediction.get(
                        "direction_score"
                    )
                ),

            "regime_score":
                self._safe_float(
                    prediction.get(
                        "regime_score"
                    )
                ),

            "volatility_modifier":
                self._safe_float(
                    prediction.get(
                        "volatility_modifier"
                    )
                ),

            "combined_score":
                self._safe_float(
                    prediction.get(
                        "combined_score"
                    )
                ),

            "confidence":
                self._safe_float(
                    prediction.get(
                        "confidence"
                    )
                ),

            "signal":
                prediction.get(
                    "signal"
                ),

            "strength":
                prediction.get(
                    "strength"
                ),

            "trade_suitability":
                prediction.get(
                    "trade_suitability"
                ),

            # ------------------------------------------------
            # Outcome fields
            # ------------------------------------------------

            "actual_price":
                None,

            "actual_return":
                None,

            "actual_direction":
                None,

            "direction_correct":
                None,

            "actual_volatility":
                None,

            "volatility_error":
                None,

            "outcome_recorded":
                False,

            "outcome_timestamp":
                None,
        }

        return record

    # ========================================================
    # SAVE PREDICTION
    # ========================================================

    def save_prediction(
        self,
        record: dict[str, Any],
    ):

        if not isinstance(
            record,
            dict,
        ):

            raise TypeError(
                "record must be a dictionary."
            )

        new_df = pd.DataFrame(
            [record]
        )

        # ----------------------------------------------------
        # Main prediction log
        # ----------------------------------------------------

        if self.prediction_file.exists():

            existing = pd.read_parquet(
                self.prediction_file
            )

            combined = pd.concat(
                [
                    existing,
                    new_df,
                ],
                ignore_index=True,
            )

        else:

            combined = new_df

        combined = (
            combined
            .drop_duplicates(
                subset=[
                    "prediction_id"
                ],
                keep="last",
            )
            .reset_index(drop=True)
        )

        combined.to_parquet(
            self.prediction_file,
            index=False,
        )

        # ----------------------------------------------------
        # Pending predictions
        # ----------------------------------------------------

        pending = combined[
            combined["outcome_recorded"]
            != True
        ].copy()

        pending.to_parquet(
            self.pending_file,
            index=False,
        )

        return record

    # ========================================================
    # RECORD FROM COMBINED SCORE
    # ========================================================

    def track(
        self,
        symbol: str,
        combined_result,
        horizon=1,
    ):

        if hasattr(
            combined_result,
            "to_dict",
        ):

            prediction = (
                combined_result.to_dict()
            )

        else:

            prediction = dict(
                combined_result
            )

        record = self.create_record(
            symbol=symbol,
            prediction=prediction,
            horizon=horizon,
        )

        return self.save_prediction(
            record
        )


    # ========================================================
    # STEP 8 - OPTION TRADE PREDICTION TRACKING
    # ========================================================

    def _load_trade_predictions(self):
        if not self.trade_prediction_file.exists():
            return pd.DataFrame()

        return pd.read_parquet(
            self.trade_prediction_file
        )

    def _save_trade_predictions(
        self,
        df: pd.DataFrame,
    ):
        df.to_parquet(
            self.trade_prediction_file,
            index=False,
        )

        pending = df[
            df["outcome_recorded"] != True
        ].copy()

        pending.to_parquet(
            self.trade_pending_file,
            index=False,
        )

    def record_generation(
        self,
        result: dict[str, Any],
    ):
        """
        Record every option trade generated by TradeEngine.

        This is separate from the existing `track()` method, which is
        preserved for the original ML prediction workflow.
        """
        if not isinstance(result, dict):
            raise TypeError(
                "result must be a dictionary."
            )

        trades = result.get("trades") or []

        if not trades:
            return []

        existing = self._load_trade_predictions()

        rows = []

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        symbol = str(
            result.get("selected_index")
            or result.get("instrument")
            or "NIFTY 50"
        ).upper()

        expiry = (
            result.get("selected_expiry")
            or result.get("expiry")
        )

        generation_id = (
            datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
            + "_"
            + uuid4().hex[:8]
        )

        for rank, trade in enumerate(
            trades,
            start=1,
        ):
            if not isinstance(
                trade,
                dict,
            ):
                continue

            risk = (
                trade.get("risk")
                or {}
            )

            prediction_id = (
                f"{generation_id}_"
                f"{rank}_"
                f"{trade.get('strike', 'NA')}_"
                f"{trade.get('type', 'NA')}"
            )

            rows.append(
                {
                    "prediction_id":
                        prediction_id,
                    "generation_id":
                        generation_id,
                    "generated_at":
                        now,
                    "rank":
                        rank,

                    # Frozen prediction context
                    "symbol":
                        symbol,
                    "expiry":
                        expiry,
                    "strike":
                        self._safe_float(
                            trade.get("strike")
                        ),
                    "type":
                        trade.get("type"),
                    "entry":
                        self._safe_float(
                            trade.get("premium")
                        ),
                    "stop_loss":
                        self._safe_float(
                            risk.get("sl")
                        ),
                    "target1":
                        self._safe_float(
                            risk.get("target1")
                        ),
                    "target2":
                        self._safe_float(
                            risk.get("target2")
                        ),
                    "target3":
                        self._safe_float(
                            risk.get("target3")
                        ),
                    "risk_reward":
                        self._safe_float(
                            risk.get("rr")
                        ),
                    "position_size":
                        self._safe_int(
                            risk.get(
                                "position_size"
                            )
                        ),
                    "max_loss":
                        self._safe_float(
                            risk.get("max_loss")
                        ),
                    "ai_score":
                        self._safe_float(
                            trade.get("ai_score")
                        ),
                    "probability":
                        self._safe_float(
                            trade.get("probability")
                        ),
                    "recommendation":
                        trade.get(
                            "recommendation"
                        ),
                    "reasons":
                        json.dumps(
                            trade.get("reasons")
                            or [],
                            ensure_ascii=False,
                        ),
                    "warnings":
                        json.dumps(
                            trade.get("warnings")
                            or [],
                            ensure_ascii=False,
                        ),
                    "unified_components":
                        json.dumps(
                            trade.get(
                                "unified_components"
                            )
                            or {},
                            ensure_ascii=False,
                        ),

                    # Mutable live/outcome fields
                    "status":
                        "OPEN",
                    "last_price":
                        self._safe_float(
                            trade.get(
                                "live_premium",
                                trade.get(
                                    "premium"
                                )
                            )
                        ),
                    "observed_at":
                        now,
                    "outcome":
                        None,
                    "outcome_price":
                        None,
                    "outcome_timestamp":
                        None,
                    "outcome_recorded":
                        False,
                }
            )

        if not rows:
            return []

        new_df = pd.DataFrame(
            rows
        )

        if existing.empty:
            combined = new_df
        else:
            combined = pd.concat(
                [
                    existing,
                    new_df,
                ],
                ignore_index=True,
            )

        combined = (
            combined
            .drop_duplicates(
                subset=[
                    "prediction_id"
                ],
                keep="last",
            )
            .reset_index(drop=True)
        )

        self._save_trade_predictions(
            combined
        )

        return [
            row["prediction_id"]
            for row in rows
        ]

    def update_market_snapshot(
        self,
        instrument: str,
        rows,
    ):
        """
        Update live option prices and resolve outcomes.

        Outcome priority intentionally mirrors the existing trade
        tracker: Target 2, then Target 1, then Stop Loss.
        """
        snapshot = list(
            rows or []
        )

        if not snapshot:
            return 0

        df = self._load_trade_predictions()

        if df.empty:
            return 0

        changed = 0

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        instrument = str(
            instrument
            or ""
        ).upper()

        for index in df.index:

            if str(
                df.at[
                    index,
                    "symbol",
                ]
            ).upper() != instrument:
                continue

            if bool(
                df.at[
                    index,
                    "outcome_recorded",
                ]
            ):
                continue

            strike = self._safe_float(
                df.at[
                    index,
                    "strike",
                ]
            )

            option_type = str(
                df.at[
                    index,
                    "type",
                ]
                or "CE"
            ).upper()

            if strike is None:
                continue

            live_price = None

            for row in snapshot:

                if not isinstance(
                    row,
                    dict,
                ):
                    continue

                row_strike = self._safe_float(
                    row.get("strike")
                )

                if (
                    row_strike is None
                    or row_strike != strike
                ):
                    continue

                key = (
                    "pe_ltp"
                    if option_type == "PE"
                    else "ce_ltp"
                )

                live_price = self._safe_float(
                    row.get(key)
                )

                if live_price is not None:
                    break

            if live_price is None:
                continue

            df.at[
                index,
                "last_price",
            ] = live_price

            df.at[
                index,
                "observed_at",
            ] = now

            target2 = self._safe_float(
                df.at[
                    index,
                    "target2",
                ]
            ) or 0.0

            target1 = self._safe_float(
                df.at[
                    index,
                    "target1",
                ]
            ) or 0.0

            stop_loss = self._safe_float(
                df.at[
                    index,
                    "stop_loss",
                ]
            ) or 0.0

            outcome = None

            if (
                target2 > 0
                and live_price >= target2
            ):
                outcome = "TARGET_2"

            elif (
                target1 > 0
                and live_price >= target1
            ):
                outcome = "TARGET_1"

            elif (
                stop_loss > 0
                and live_price <= stop_loss
            ):
                outcome = "STOP_LOSS"

            if outcome is not None:

                df.at[
                    index,
                    "status",
                ] = (
                    "TARGET 2 HIT"
                    if outcome == "TARGET_2"
                    else (
                        "TARGET 1 HIT"
                        if outcome == "TARGET_1"
                        else "STOP LOSS HIT"
                    )
                )

                df.at[
                    index,
                    "outcome",
                ] = outcome

                df.at[
                    index,
                    "outcome_price",
                ] = live_price

                df.at[
                    index,
                    "outcome_timestamp",
                ] = now

                df.at[
                    index,
                    "outcome_recorded",
                ] = True

            changed += 1

        self._save_trade_predictions(
            df
        )

        return changed

    def load_trade_predictions(
        self,
    ):
        return self._load_trade_predictions()

    def load_pending_trade_predictions(
        self,
    ):
        if not self.trade_pending_file.exists():
            return pd.DataFrame()

        return pd.read_parquet(
            self.trade_pending_file
        )

    def trade_statistics(
        self,
    ):
        df = self._load_trade_predictions()

        if df.empty:
            return {
                "total_predictions": 0,
                "resolved_predictions": 0,
                "pending_predictions": 0,
                "target1_hits": 0,
                "target2_hits": 0,
                "stop_loss_hits": 0,
                "win_rate": None,
                "average_probability": None,
            }

        resolved = df[
            df["outcome_recorded"] == True
        ].copy()

        target1_hits = int(
            (
                resolved["outcome"]
                == "TARGET_1"
            ).sum()
        )

        target2_hits = int(
            (
                resolved["outcome"]
                == "TARGET_2"
            ).sum()
        )

        stop_loss_hits = int(
            (
                resolved["outcome"]
                == "STOP_LOSS"
            ).sum()
        )

        closed = (
            target1_hits
            + target2_hits
            + stop_loss_hits
        )

        wins = (
            target1_hits
            + target2_hits
        )

        win_rate = (
            wins / closed * 100.0
            if closed
            else None
        )

        probability = pd.to_numeric(
            df["probability"],
            errors="coerce",
        ).dropna()

        average_probability = (
            float(
                probability.mean()
            )
            if not probability.empty
            else None
        )

        return {
            "total_predictions":
                int(len(df)),
            "resolved_predictions":
                int(len(resolved)),
            "pending_predictions":
                int(
                    len(df)
                    - len(resolved)
                ),
            "target1_hits":
                target1_hits,
            "target2_hits":
                target2_hits,
            "stop_loss_hits":
                stop_loss_hits,
            "win_rate":
                win_rate,
            "average_probability":
                average_probability,
        }

    # ========================================================
    # LOAD ALL
    # ========================================================

    def load_predictions(self):

        if not self.prediction_file.exists():

            return pd.DataFrame()

        return pd.read_parquet(
            self.prediction_file
        )

    # ========================================================
    # LOAD PENDING
    # ========================================================

    def load_pending(self):

        if not self.pending_file.exists():

            return pd.DataFrame()

        return pd.read_parquet(
            self.pending_file
        )

    # ========================================================
    # RECORD OUTCOME
    # ========================================================

    def record_outcome(
        self,
        prediction_id: str,
        actual_price: float,
        reference_price: float,
        actual_volatility: Optional[float] = None,
    ):

        df = self.load_predictions()

        if df.empty:

            raise RuntimeError(
                "Prediction log is empty."
            )

        matches = (
            df["prediction_id"]
            == prediction_id
        )

        if not matches.any():

            raise KeyError(
                f"Prediction not found: "
                f"{prediction_id}"
            )

        row_index = df.index[
            matches
        ][0]

        actual_price = float(
            actual_price
        )

        reference_price = float(
            reference_price
        )

        actual_return = (
            (
                actual_price
                - reference_price
            )
            / reference_price
            if reference_price != 0
            else 0.0
        )

        if actual_return > 0:

            actual_direction = 1

        elif actual_return < 0:

            actual_direction = 0

        else:

            actual_direction = 2

        predicted_direction = (
            df.at[
                row_index,
                "direction_prediction"
            ]
        )

        direction_correct = False

        # UP = 1 / DOWN = 0
        if (
            actual_direction in [0, 1]
            and predicted_direction
            in [0, 1]
        ):

            direction_correct = (
                int(
                    predicted_direction
                )
                == actual_direction
            )

        predicted_volatility = (
            self._safe_float(
                df.at[
                    row_index,
                    "predicted_volatility"
                ]
            )
        )

        volatility_error = None

        if (
            actual_volatility is not None
            and predicted_volatility
            is not None
        ):

            volatility_error = abs(
                float(actual_volatility)
                - predicted_volatility
            )

        df.at[
            row_index,
            "actual_price"
        ] = actual_price

        df.at[
            row_index,
            "actual_return"
        ] = actual_return

        df.at[
            row_index,
            "actual_direction"
        ] = actual_direction

        df.at[
            row_index,
            "direction_correct"
        ] = direction_correct

        df.at[
            row_index,
            "actual_volatility"
        ] = (
            actual_volatility
        )

        df.at[
            row_index,
            "volatility_error"
        ] = volatility_error

        df.at[
            row_index,
            "outcome_recorded"
        ] = True

        df.at[
            row_index,
            "outcome_timestamp"
        ] = datetime.now().isoformat()

        df.to_parquet(
            self.prediction_file,
            index=False,
        )

        pending = df[
            df["outcome_recorded"]
            != True
        ].copy()

        pending.to_parquet(
            self.pending_file,
            index=False,
        )

        return df.loc[
            row_index
        ].to_dict()

    # ========================================================
    # STATS
    # ========================================================

    def statistics(self):

        df = self.load_predictions()

        if df.empty:

            return {
                "total_predictions": 0,
                "resolved_predictions": 0,
                "pending_predictions": 0,
                "direction_accuracy": None,
                "average_actual_return": None,
                "average_volatility_error": None,
            }

        resolved = df[
            df["outcome_recorded"] == True
        ].copy()

        direction_accuracy = None

        if (
            not resolved.empty
            and "direction_correct"
            in resolved.columns
        ):

            direction_accuracy = (
                resolved[
                    "direction_correct"
                ]
                .astype(float)
                .mean()
            )

        average_return = None

        if (
            not resolved.empty
            and "actual_return"
            in resolved.columns
        ):

            average_return = float(
                resolved[
                    "actual_return"
                ]
                .mean()
            )

        average_volatility_error = None

        if (
            not resolved.empty
            and "volatility_error"
            in resolved.columns
        ):

            values = (
                pd.to_numeric(
                    resolved[
                        "volatility_error"
                    ],
                    errors="coerce",
                )
                .dropna()
            )

            if not values.empty:

                average_volatility_error = (
                    float(
                        values.mean()
                    )
                )

        return {
            "total_predictions":
                int(len(df)),

            "resolved_predictions":
                int(len(resolved)),

            "pending_predictions":
                int(
                    len(df)
                    - len(resolved)
                ),

            "direction_accuracy":
                direction_accuracy,

            "average_actual_return":
                average_return,

            "average_volatility_error":
                average_volatility_error,
        }