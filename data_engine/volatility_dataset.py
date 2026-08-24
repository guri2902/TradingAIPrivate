# ============================================================
# TradingAI - VOLATILITY MODEL DATASET
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd

from data_engine.feature_engineering import FeatureEngineering


class VolatilityDataset:

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
        symbol=None,
        horizon=10
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
            str(c).lower()
            for c in df.columns
        ]

        required = [
            "open",
            "high",
            "low",
            "close",
        ]

        missing = [
            c
            for c in required
            if c not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required columns: {missing}"
            )

        if "volume" not in df.columns:
            df["volume"] = 0

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        if "timestamp" not in df.columns:

            if "date" in df.columns:

                df["timestamp"] = pd.to_datetime(
                    df["date"]
                )

            else:

                raise ValueError(
                    "Missing timestamp/date column."
                )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"]
        )

        df = (
            df
            .sort_values("timestamp")
            .drop_duplicates(
                subset=["timestamp"],
                keep="last"
            )
            .reset_index(drop=True)
        )

        print(
            "[VOLATILITY] Building technical features..."
        )

        # ----------------------------------------------------
        # Technical features
        # ----------------------------------------------------

        df = self.features.build_features(df)

        feature_rows = len(df)

        print(
            f"[VOLATILITY] Feature rows: "
            f"{feature_rows}"
        )

        # ----------------------------------------------------
        # CURRENT LOG RETURN
        #
        # Used only as source data for the future target.
        # ----------------------------------------------------

        if "log_return" not in df.columns:

            df["log_return"] = np.log(
                df["close"]
                / df["close"].shift(1)
            )

        # ----------------------------------------------------
        # FUTURE REALIZED VOLATILITY
        #
        # Uses the NEXT `horizon` trading sessions.
        #
        # Annualized:
        #
        # std(log returns) * sqrt(252)
        #
        # This column is TARGET ONLY.
        # It must NEVER be used as an input feature.
        # ----------------------------------------------------

        future_returns = (
            df["log_return"]
            .shift(-1)
        )

        df[
            "future_volatility"
        ] = (
            future_returns
            .iloc[::-1]
            .rolling(
                window=horizon,
                min_periods=horizon
            )
            .std()
            .iloc[::-1]
            * np.sqrt(252)
        )

        # ----------------------------------------------------
        # Remove rows without future information
        # ----------------------------------------------------

        before = len(df)

        df = df[
            df["future_volatility"].notna()
        ].copy()

        removed = before - len(df)

        # ----------------------------------------------------
        # Volatility target
        #
        # Numeric regression target.
        # Classification thresholds are calculated later
        # using TRAINING data only.
        # ----------------------------------------------------

        df["volatility_target"] = (
            df["future_volatility"]
        )

        # ----------------------------------------------------
        # Volatility bucket
        #
        # Informational only.
        #
        # Do NOT use this as a model feature.
        # ----------------------------------------------------

        q33 = df[
            "future_volatility"
        ].quantile(0.3333)

        q66 = df[
            "future_volatility"
        ].quantile(0.6667)

        df["volatility_regime"] = np.select(
            [
                df["future_volatility"] <= q33,
                df["future_volatility"] >= q66,
            ],
            [
                "LOW",
                "HIGH",
            ],
            default="NORMAL"
        )

        # ----------------------------------------------------
        # Symbol
        # ----------------------------------------------------

        if symbol is None:

            if "symbol" in df.columns:

                symbol = str(
                    df["symbol"].iloc[0]
                ).lower()

            else:

                symbol = "market"

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        output_path = (
            self.output_dir
            / f"volatility_{symbol.lower()}.parquet"
        )

        df.to_parquet(
            output_path,
            index=False
        )

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        print(
            f"[VOLATILITY] Final rows: "
            f"{len(df)}"
        )

        print(
            f"[VOLATILITY] Removed rows: "
            f"{removed}"
        )

        print(
            f"[VOLATILITY] Features: "
            f"{len(self._feature_columns(df))}"
        )

        print(
            "\n[VOLATILITY] Target statistics:"
        )

        print(
            df["volatility_target"]
            .describe()
            .to_string()
        )

        print(
            "\n[VOLATILITY] Distribution:"
        )

        print(
            df["volatility_regime"]
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
            f"\n[VOLATILITY] Saved: "
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

            # Targets
            "future_volatility",
            "volatility_target",
            "volatility_regime",
        }

        return [
            c
            for c in df.columns
            if c not in excluded
            and pd.api.types.is_numeric_dtype(
                df[c]
            )
        ]