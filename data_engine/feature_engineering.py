# ============================================================
# TradingAI - FEATURE ENGINEERING
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd


class FeatureEngineering:

    def __init__(self):
        pass

    # ========================================================
    # MAIN FEATURE BUILDER
    # ========================================================

    def build_features(self, df):
        """
        Build technical and price/volume features from OHLCV data.

        Required columns:
            open
            high
            low
            close
            volume

        Returns:
            pandas.DataFrame
        """

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()

        # ----------------------------------------------------
        # NORMALIZE COLUMN NAMES
        # ----------------------------------------------------

        df.columns = [
            str(column).lower()
            for column in df.columns
        ]

        required = [
            "open",
            "high",
            "low",
            "close",
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required OHLC columns: {missing}"
            )

        # Volume is optional
        if "volume" not in df.columns:
            df["volume"] = 0

        # ----------------------------------------------------
        # NUMERIC CONVERSION
        # ----------------------------------------------------

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        for column in numeric_columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

            df = df.sort_values(
                "timestamp"
            )

        df = df.reset_index(
            drop=True
        )

        # ====================================================
        # PRICE FEATURES
        # ====================================================

        # Daily percentage return
        df["return"] = (
            df["close"]
            .pct_change()
        )

        # Log return
        df["log_return"] = np.log(
            df["close"]
            / df["close"].shift(1)
        )

        # Price change
        df["price_change"] = (
            df["close"]
            - df["open"]
        )

        # ----------------------------------------------------
        # CANDLE FEATURES
        # ----------------------------------------------------

        df["range"] = (
            df["high"]
            - df["low"]
        )

        df["body"] = (
            df["close"]
            - df["open"]
        ).abs()

        df["body_pct"] = (
            df["body"]
            / df["open"]
        )
        # ========================================================
        # SCALE-INDEPENDENT PRICE FEATURES
        # ========================================================

        df["range_pct"] = (
            df["range"] /
            df["close"].replace(0, np.nan)
        )

        # Create wick features BEFORE calculating wick percentages.
        df["upper_wick"] = (
            df["high"] -
            df[["open", "close"]].max(axis=1)
        )

        df["lower_wick"] = (
            df[["open", "close"]].min(axis=1) -
            df["low"]
        )

        df["upper_wick_pct"] = (
            df["upper_wick"] /
            df["close"].replace(0, np.nan)
        )

        df["lower_wick_pct"] = (
            df["lower_wick"] /
            df["close"].replace(0, np.nan)
        )

        df["candle_direction"] = np.where(
            df["close"] > df["open"],
            1,
            np.where(
                df["close"] < df["open"],
                -1,
                0
            )
        )

        # ====================================================
        # MOVING AVERAGES
        # ====================================================

        df["sma_5"] = (
            df["close"]
            .rolling(5)
            .mean()
        )

        df["sma_10"] = (
            df["close"]
            .rolling(10)
            .mean()
        )

        df["sma_20"] = (
            df["close"]
            .rolling(20)
            .mean()
        )

        df["sma_50"] = (
            df["close"]
            .rolling(50)
            .mean()
        )

        df["sma_200"] = (
            df["close"]
            .rolling(200)
            .mean()
        )

        # ====================================================
        # EXPONENTIAL MOVING AVERAGES
        # ====================================================

        df["ema_9"] = (
            df["close"]
            .ewm(
                span=9,
                adjust=False
            )
            .mean()
        )

        df["ema_21"] = (
            df["close"]
            .ewm(
                span=21,
                adjust=False
            )
            .mean()
        )

        # ====================================================
        # RSI
        # ====================================================

        delta = df["close"].diff()

        gain = delta.clip(
            lower=0
        )

        loss = -delta.clip(
            upper=0
        )

        avg_gain = (
            gain
            .rolling(14)
            .mean()
        )

        avg_loss = (
            loss
            .rolling(14)
            .mean()
        )

        rs = (
            avg_gain
            / avg_loss.replace(0, np.nan)
        )

        df["rsi_14"] = (
            100
            - (
                100
                / (1 + rs)
            )
        )

        # ====================================================
        # MACD
        # ====================================================

        ema_12 = (
            df["close"]
            .ewm(
                span=12,
                adjust=False
            )
            .mean()
        )

        ema_26 = (
            df["close"]
            .ewm(
                span=26,
                adjust=False
            )
            .mean()
        )

        df["macd"] = (
            ema_12
            - ema_26
        )

        df["macd_signal"] = (
            df["macd"]
            .ewm(
                span=9,
                adjust=False
            )
            .mean()
        )

        df["macd_histogram"] = (
            df["macd"]
            - df["macd_signal"]
        )

        # ====================================================
        # ATR
        # ====================================================

        previous_close = (
            df["close"]
            .shift(1)
        )

        true_range = pd.concat(
            [
                df["high"] - df["low"],
                (
                    df["high"]
                    - previous_close
                ).abs(),
                (
                    df["low"]
                    - previous_close
                ).abs(),
            ],
            axis=1
        ).max(axis=1)

        df["true_range"] = true_range

        df["atr_14"] = (
            true_range
            .rolling(14)
            .mean()
        )
        # ATR relative to price
        df["atr_pct"] = (
            df["atr_14"]
            / df["close"].replace(0, np.nan)
        )

        # ====================================================
        # BOLLINGER BANDS
        # ====================================================

        bb_middle = (
            df["close"]
            .rolling(20)
            .mean()
        )

        bb_std = (
            df["close"]
            .rolling(20)
            .std()
        )

        df["bb_middle"] = bb_middle

        df["bb_upper"] = (
            bb_middle
            + (2 * bb_std)
        )

        df["bb_lower"] = (
            bb_middle
            - (2 * bb_std)
        )

        # Bollinger width
        df["bb_width"] = (
            (
                df["bb_upper"]
                - df["bb_lower"]
            )
            / df["bb_middle"]
        )

        # Position inside Bollinger Bands
        band_width = (
            df["bb_upper"]
            - df["bb_lower"]
        )

        df["bb_position"] = (
            (
                df["close"]
                - df["bb_lower"]
            )
            / band_width.replace(
                0,
                np.nan
            )
        )

        # ====================================================
        # VOLUME FEATURES
        # ====================================================

        df["volume_sma_5"] = (
            df["volume"]
            .rolling(5)
            .mean()
        )

        df["volume_sma_20"] = (
            df["volume"]
            .rolling(20)
            .mean()
        )

        df["volume_ratio"] = (
            df["volume"]
            / df["volume_sma_20"].replace(
                0,
                np.nan
            )
        )

        # ====================================================
        # VOLATILITY
        # ====================================================

        df["volatility_10"] = (
            df["return"]
            .rolling(10)
            .std()
        )

        df["volatility_20"] = (
            df["return"]
            .rolling(20)
            .std()
        )

        # ====================================================
        # PRICE DISTANCE FEATURES
        # ====================================================

        df["close_vs_sma_20"] = (
            df["close"]
            / df["sma_20"]
            - 1
        )

        df["close_vs_sma_50"] = (
            df["close"]
            / df["sma_50"]
            - 1
        )

        df["close_vs_ema_21"] = (
            df["close"]
            / df["ema_21"]
            - 1
        )
        # ========================================================
        # ADDITIONAL RELATIVE TREND FEATURES
        # ========================================================

        for period in [5, 10, 200]:

            column = f"sma_{period}"

            df[f"close_vs_sma_{period}_pct"] = (
                df["close"]
                / df[column].replace(0, np.nan)
            ) - 1


        for period in [9]:

            column = f"ema_{period}"

            df[f"close_vs_ema_{period}_pct"] = (
                df["close"]
                / df[column].replace(0, np.nan)
            ) - 1

        # ====================================================
        # MOMENTUM
        # ====================================================

        df["momentum_5"] = (
            df["close"]
            / df["close"].shift(5)
            - 1
        )

        df["momentum_10"] = (
            df["close"]
            / df["close"].shift(10)
            - 1
        )

        df["momentum_20"] = (
            df["close"]
            / df["close"].shift(20)
            - 1
        )

        # ====================================================
        # CLEAN INF VALUES
        # ====================================================

        df = df.replace(
            [np.inf, -np.inf],
            np.nan
        )

        return df.reset_index(
            drop=True
        )

    # ========================================================
    # REMOVE WARM-UP ROWS
    # ========================================================

    @staticmethod
    def remove_warmup_rows(
        df,
        minimum_period=200
    ):
        """
        Remove rows where long-period indicators
        have not become valid yet.
        """

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()

        if len(df) <= minimum_period:
            return df.reset_index(
                drop=True
            )

        return (
            df.iloc[minimum_period:]
              .reset_index(drop=True)
        )

    # ========================================================
    # SAVE FEATURES
    # ========================================================

    @staticmethod
    def save_features(
        df,
        path
    ):

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_parquet(
            path,
            index=False
        )

        print(
            f"[FEATURES] Saved: {path}"
        )

        print(
            f"[FEATURES] Rows: {len(df)}"
        )

        print(
            f"[FEATURES] Columns: {len(df.columns)}"
        )

        return path