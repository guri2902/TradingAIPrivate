# ============================================================
# TradingAI - MARKET REGIME DATASET
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd

from data_engine.feature_engineering import FeatureEngineering


class RegimeDataset:

    def __init__(
        self,
        output_dir="market_data/processed"
    ):
        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.features = FeatureEngineering()

    # ========================================================
    # BUILD
    # ========================================================

    def build(
        self,
        df,
        symbol=None
    ):

        if df is None or df.empty:
            raise ValueError(
                "Historical market data is empty."
            )

        df = df.copy()

        # ----------------------------------------------------
        # Normalize columns
        # ----------------------------------------------------

        df.columns = [
            str(c).lower().strip()
            for c in df.columns
        ]

        required = [
            "open",
            "high",
            "low",
            "close",
        ]

        missing = [
            c for c in required
            if c not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required columns: {missing}"
            )

        if "volume" not in df.columns:
            df["volume"] = 0.0

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        if "timestamp" not in df.columns:

            if "date" in df.columns:
                df["timestamp"] = pd.to_datetime(
                    df["date"],
                    errors="coerce"
                )

            else:
                raise ValueError(
                    "Missing timestamp/date column."
                )

        else:
            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

        df = (
            df
            .dropna(subset=["timestamp"])
            .sort_values("timestamp")
            .drop_duplicates(
                subset=["timestamp"],
                keep="last"
            )
            .reset_index(drop=True)
        )

        print(
            "[REGIME] Building technical features..."
        )

        # ----------------------------------------------------
        # Technical features
        # ----------------------------------------------------

        df = self.features.build_features(df)

        print(
            f"[REGIME] Feature rows: {len(df)}"
        )

        # ----------------------------------------------------
        # FUTURE REGIME LABEL
        #
        # IMPORTANT:
        # This is the TRAINING TARGET only.
        #
        # The model never receives these future columns.
        #
        # 20 trading day forward return:
        #
        # >= +5%  -> BULL
        # <= -5%  -> BEAR
        # otherwise SIDEWAYS
        # ----------------------------------------------------

        horizon = 20

        df["future_close"] = (
            df["close"].shift(-horizon)
        )

        df["future_return_20"] = (
            df["future_close"]
            / df["close"]
        ) - 1.0

        df["regime"] = np.select(
            [
                df["future_return_20"] >= 0.05,
                df["future_return_20"] <= -0.05,
            ],
            [
                "BULL",
                "BEAR",
            ],
            default="SIDEWAYS"
        )

        # ----------------------------------------------------
        # Numeric target
        # ----------------------------------------------------

        regime_map = {
            "BEAR": 0,
            "SIDEWAYS": 1,
            "BULL": 2,
        }

        df["regime_target"] = (
            df["regime"]
            .map(regime_map)
        )

        # ----------------------------------------------------
        # Remove rows without future information
        # ----------------------------------------------------

        before = len(df)

        df = df[
            df["future_close"].notna()
            & df["future_return_20"].notna()
            & df["regime_target"].notna()
        ].copy()

        df["regime_target"] = (
            df["regime_target"]
            .astype(int)
        )

        print(
            f"[REGIME] Final rows: {len(df)}"
        )

        print(
            f"[REGIME] Removed rows: "
            f"{before - len(df)}"
        )

        # ----------------------------------------------------
        # Remove future information
        # ----------------------------------------------------

        df = df.drop(
            columns=[
                "future_close",
                "future_return_20",
            ],
            errors="ignore"
        )

        # ----------------------------------------------------
        # Determine symbol
        # ----------------------------------------------------

        if symbol is None:

            if "symbol" in df.columns:

                valid_symbols = (
                    df["symbol"]
                    .dropna()
                )

                if not valid_symbols.empty:
                    symbol = str(
                        valid_symbols.iloc[0]
                    )

            if symbol is None:
                symbol = "market"

        symbol = str(symbol).lower()

        # ----------------------------------------------------
        # Feature statistics
        # ----------------------------------------------------

        feature_columns = (
            self._feature_columns(df)
        )

        print(
            f"[REGIME] Features: "
            f"{len(feature_columns)}"
        )

        # ----------------------------------------------------
        # Distribution
        # ----------------------------------------------------

        print(
            "\n[REGIME] Distribution:"
        )

        print(
            df["regime"]
            .value_counts()
            .reindex(
                ["BEAR", "SIDEWAYS", "BULL"],
                fill_value=0
            )
            .to_string()
        )

        print(
            "\n[REGIME] Target distribution:"
        )

        print(
            df["regime_target"]
            .value_counts()
            .sort_index()
            .to_string()
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        output_path = (
            self.output_dir
            / f"regime_{symbol}.parquet"
        )

        df.to_parquet(
            output_path,
            index=False
        )

        print(
            f"\n[REGIME] Saved: "
            f"{output_path}"
        )

        return df

    # ========================================================
    # FEATURE COLUMNS
    # ========================================================

    @staticmethod
    def _feature_columns(df):

        excluded = {
            "timestamp",
            "date",
            "symbol",
            "source",
            "series",
            "regime",
            "regime_target",

            # Never allow future fields
            "future_close",
            "future_return_20",
        }

        return [
            c
            for c in df.columns
            if c not in excluded
            and pd.api.types.is_numeric_dtype(df[c])
        ]