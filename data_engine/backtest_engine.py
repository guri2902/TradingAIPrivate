# ============================================================
# TradingAI - AI BACKTEST ENGINE
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd

from data_engine.feature_engineering import FeatureEngineering
from data_engine.combined_ai_score import CombinedAIScore


class BacktestEngine:

    def __init__(
        self,
        initial_capital=100000.0,
        position_size=10000.0,
        min_score=0.20,
    ):

        self.initial_capital = float(
            initial_capital
        )

        self.position_size = float(
            position_size
        )

        self.min_score = float(
            min_score
        )

        self.features = FeatureEngineering()

        self.combined = CombinedAIScore()
        self.combined.load()

    # ========================================================
    # PREPARE DATA
    # ========================================================

    def prepare(
        self,
        df,
    ):

        if df is None or df.empty:
            raise ValueError(
                "Historical dataframe is empty."
            )

        data = df.copy()

        data.columns = [
            str(c).strip().lower()
            for c in data.columns
        ]

        if "timestamp" not in data.columns:

            if "date" in data.columns:

                data["timestamp"] = (
                    pd.to_datetime(
                        data["date"],
                        errors="coerce",
                    )
                )

            else:

                raise ValueError(
                    "Missing timestamp/date column."
                )

        data["timestamp"] = pd.to_datetime(
            data["timestamp"],
            errors="coerce",
        )

        data = (
            data
            .dropna(subset=["timestamp"])
            .sort_values("timestamp")
            .drop_duplicates(
                subset=["timestamp"],
                keep="last",
            )
            .reset_index(drop=True)
        )

        print(
            f"[BACKTEST] Building features for "
            f"{len(data)} rows..."
        )

        data = self.features.build_features(
            data
        )

        if data.empty:

            raise RuntimeError(
                "Feature dataset is empty."
            )

        return data

    # ========================================================
    # GENERATE SIGNALS - BATCH MODE
    # ========================================================

    def generate_predictions(
        self,
        feature_df,
    ):

        if feature_df is None or feature_df.empty:

            return pd.DataFrame()

        if len(feature_df) < 2:

            return pd.DataFrame()

        print(
            f"[BACKTEST] Running combined model "
            f"prediction on {len(feature_df) - 1:,} rows..."
        )

        # ----------------------------------------------------
        # Predict ALL rows at once
        # ----------------------------------------------------

        prediction_input = (
            feature_df.iloc[:-1]
            .copy()
            .reset_index(drop=True)
        )

        next_rows = (
            feature_df.iloc[1:]
            .copy()
            .reset_index(drop=True)
        )

        predictions = (
            self.combined.predict(
                prediction_input
            )
        )

        if predictions is None or predictions.empty:

            raise RuntimeError(
                "Combined AI model returned no predictions."
            )

        predictions = (
            predictions
            .reset_index(drop=True)
        )

        # ----------------------------------------------------
        # Safety: align lengths
        # ----------------------------------------------------

        usable = min(
            len(predictions),
            len(prediction_input),
            len(next_rows),
        )

        predictions = predictions.iloc[
            :usable
        ].copy()

        current_rows = prediction_input.iloc[
            :usable
        ].copy()

        future_rows = next_rows.iloc[
            :usable
        ].copy()

        print(
            f"[BACKTEST] Predictions generated: "
            f"{len(predictions):,}"
        )

        # ----------------------------------------------------
        # Build result
        # ----------------------------------------------------

        rows = []

        for i in range(
            usable
        ):

            p = predictions.iloc[i]

            score = float(
                p.get(
                    "combined_score",
                    0.0,
                )
                or 0.0
            )

            signal = str(
                p.get(
                    "signal",
                    "NEUTRAL",
                )
            )

            # ------------------------------------------------
            # Skip weak signals
            # ------------------------------------------------

            if abs(score) < self.min_score:
                continue

            if signal not in (
                "BULLISH",
                "BEARISH",
            ):
                continue

            entry_price = float(
                current_rows[
                    "close"
                ].iloc[i]
            )

            exit_price = float(
                future_rows[
                    "close"
                ].iloc[i]
            )

            if entry_price <= 0:
                continue

            actual_return = (
                exit_price
                - entry_price
            ) / entry_price

            # ------------------------------------------------
            # Strategy return
            # ------------------------------------------------

            if signal == "BULLISH":

                strategy_return = (
                    actual_return
                )

            else:

                strategy_return = (
                    -actual_return
                )

            pnl = (
                strategy_return
                * self.position_size
            )

            # ------------------------------------------------
            # Actual direction
            # ------------------------------------------------

            if actual_return > 0:

                actual_direction = "UP"

            elif actual_return < 0:

                actual_direction = "DOWN"

            else:

                actual_direction = "FLAT"

            prediction_correct = (
                (
                    signal == "BULLISH"
                    and actual_direction == "UP"
                )
                or
                (
                    signal == "BEARISH"
                    and actual_direction == "DOWN"
                )
            )

            rows.append(
                {
                    "timestamp":
                        current_rows[
                            "timestamp"
                        ].iloc[i],

                    "entry":
                        entry_price,

                    "exit":
                        exit_price,

                    "signal":
                        signal,

                    "score":
                        score,

                    "confidence":
                        float(
                            p.get(
                                "confidence",
                                0.0,
                            )
                            or 0.0
                        ),

                    "regime":
                        p.get(
                            "regime_prediction"
                        ),

                    "volatility_regime":
                        p.get(
                            "volatility_regime"
                        ),

                    "actual_return":
                        actual_return,

                    "strategy_return":
                        strategy_return,

                    "pnl":
                        pnl,

                    "actual_direction":
                        actual_direction,

                    "prediction_correct":
                        prediction_correct,
                }
            )

        result = pd.DataFrame(
            rows
        )

        print(
            f"[BACKTEST] Tradable signals: "
            f"{len(result):,}"
        )

        return result

    # ========================================================
    # METRICS
    # ========================================================

    def calculate_metrics(
        self,
        trades,
    ):

        if trades is None or trades.empty:

            return {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "final_capital":
                    self.initial_capital,
                "status":
                    "NO_TRADES",
            }

        trades = trades.copy()

        trades["pnl"] = pd.to_numeric(
            trades["pnl"],
            errors="coerce",
        ).fillna(0.0)

        wins = trades[
            trades["pnl"] > 0
        ]

        losses = trades[
            trades["pnl"] < 0
        ]

        win_rate = (
            len(wins)
            / len(trades)
            * 100.0
        )

        gross_profit = float(
            wins["pnl"].sum()
        )

        gross_loss = abs(
            float(
                losses["pnl"].sum()
            )
        )

        if gross_loss > 0:

            profit_factor = (
                gross_profit
                / gross_loss
            )

        elif gross_profit > 0:

            profit_factor = float(
                "inf"
            )

        else:

            profit_factor = 0.0

        equity = (
            self.initial_capital
            + trades["pnl"].cumsum()
        )

        peak = (
            equity.cummax()
        )

        drawdown = (
            equity - peak
        )

        max_drawdown = float(
            drawdown.min()
        )

        total_pnl = float(
            trades["pnl"].sum()
        )

        return {
            "trades":
                int(len(trades)),

            "wins":
                int(len(wins)),

            "losses":
                int(len(losses)),

            "win_rate":
                float(win_rate),

            "total_pnl":
                total_pnl,

            "avg_pnl":
                float(
                    trades["pnl"].mean()
                ),

            "profit_factor":
                float(
                    profit_factor
                ),

            "max_drawdown":
                max_drawdown,

            "final_capital":
                float(
                    self.initial_capital
                    + total_pnl
                ),

            "status":
                "OK",
        }

    # ========================================================
    # RUN
    # ========================================================

    def run(
        self,
        df,
    ):

        features = self.prepare(
            df
        )

        print(
            "[BACKTEST] Starting batch prediction..."
        )

        trades = (
            self.generate_predictions(
                features
            )
        )

        metrics = (
            self.calculate_metrics(
                trades
            )
        )

        return {
            "trades":
                trades,

            "metrics":
                metrics,
        }

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        trades,
        path=(
            "market_data/predictions/"
            "ai_backtest_results.parquet"
        ),
    ):

        output = Path(
            path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        trades.to_parquet(
            output,
            index=False,
        )

        return output

    # ========================================================
    # REPORT
    # ========================================================

    @staticmethod
    def print_report(
        metrics,
    ):

        print("=" * 70)
        print(
            "TradingAI - AI BACKTEST REPORT"
        )
        print("=" * 70)

        print(
            f"\nTrades: "
            f"{metrics['trades']}"
        )

        print(
            f"Wins: "
            f"{metrics['wins']}"
        )

        print(
            f"Losses: "
            f"{metrics['losses']}"
        )

        print(
            f"Win rate: "
            f"{metrics['win_rate']:.2f}%"
        )

        print(
            f"Total P&L: "
            f"₹{metrics['total_pnl']:,.2f}"
        )

        print(
            f"Average trade: "
            f"₹{metrics['avg_pnl']:,.2f}"
        )

        pf = metrics[
            "profit_factor"
        ]

        if np.isinf(pf):

            pf_text = "∞"

        else:

            pf_text = f"{pf:.2f}"

        print(
            f"Profit factor: "
            f"{pf_text}"
        )

        print(
            f"Max drawdown: "
            f"₹{metrics['max_drawdown']:,.2f}"
        )

        print(
            f"Final capital: "
            f"₹{metrics['final_capital']:,.2f}"
        )

        print(
            f"Status: "
            f"{metrics['status']}"
        )