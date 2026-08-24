# ============================================================
# TradingAI - DIRECTION MODEL DATASET
# STEP 2.1 - QUANT ML
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.feature_engineering import FeatureEngineering


class DirectionDataset:

    def __init__(self, base_dir="market_data"):

        self.base_dir = Path(base_dir)

        self.processed_dir = (
            self.base_dir / "processed"
        )

        self.processed_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.market = UnifiedMarketData()

        self.features = FeatureEngineering()

    # ========================================================
    # BUILD DATASET
    # ========================================================

    def build(
        self,
        symbol="RELIANCE",
        from_date=None,
        to_date=None,
        source="eod2"
    ):

        symbol = symbol.upper()

        print()
        print("=" * 70)
        print(
            f"[DIRECTION] Building dataset: {symbol}"
        )
        print("=" * 70)

        # ----------------------------------------------------
        # LOAD HISTORICAL DATA
        # ----------------------------------------------------

        df = self.market.get_stock_history(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            source=source
        )

        if df is None or df.empty:
            raise RuntimeError(
                f"No historical data available for {symbol}"
            )

        print(
            f"[DIRECTION] Historical rows: {len(df)}"
        )

        # ----------------------------------------------------
        # BUILD TECHNICAL FEATURES
        # ----------------------------------------------------

        df = self.features.build_features(df)

        if df.empty:
            raise RuntimeError(
                "Feature engineering returned no data"
            )

        print(
            f"[DIRECTION] Feature rows: {len(df)}"
        )

        # ----------------------------------------------------
        # SORT CHRONOLOGICALLY
        # ----------------------------------------------------

        df = (
            df.sort_values("timestamp")
              .reset_index(drop=True)
        )

        # ----------------------------------------------------
        # NEXT-DAY CLOSE
        #
        # TODAY'S FEATURES
        #          ↓
        # TOMORROW'S CLOSE
        # ----------------------------------------------------

        df["next_close"] = (
            df["close"].shift(-1)
        )

        # ----------------------------------------------------
        # TARGET
        #
        # 1 = UP
        # 0 = DOWN / FLAT
        # ----------------------------------------------------

        df["target"] = (
            df["next_close"] > df["close"]
        ).astype(int)

        # ----------------------------------------------------
        # LAST ROW HAS NO FUTURE TARGET
        # ----------------------------------------------------

        df = df[
            df["next_close"].notna()
        ].copy()

        # ----------------------------------------------------
        # MODEL FEATURES
        # ----------------------------------------------------

        feature_columns = [

            "open",
            "high",
            "low",
            "close",
            "volume",

            "return",
            "log_return",
            "price_change",
            "range",
            "body",
            "body_pct",
            "upper_wick",
            "lower_wick",
            "candle_direction",

            "sma_5",
            "sma_10",
            "sma_20",
            "sma_50",
            "sma_200",

            "ema_9",
            "ema_21",

            "rsi_14",

            "macd",
            "macd_signal",
            "macd_histogram",

            "true_range",
            "atr_14",

            "bb_middle",
            "bb_upper",
            "bb_lower",
            "bb_width",
            "bb_position",

            "volume_sma_5",
            "volume_sma_20",
            "volume_ratio",

            "volatility_10",
            "volatility_20",

            "close_vs_sma_20",
            "close_vs_sma_50",
            "close_vs_ema_21",

            "momentum_5",
            "momentum_10",
            "momentum_20",
        ]

        # ----------------------------------------------------
        # VERIFY FEATURES
        # ----------------------------------------------------

        missing = [
            column
            for column in feature_columns
            if column not in df.columns
        ]

        if missing:
            raise RuntimeError(
                "Missing direction features: "
                f"{missing}"
            )

        # ----------------------------------------------------
        # BUILD FINAL DATASET
        # ----------------------------------------------------

        dataset = df[
            [
                "timestamp",
                "symbol",
                *feature_columns,
                "next_close",
                "target",
            ]
        ].copy()

        # ----------------------------------------------------
        # REMOVE NaN FROM INDICATOR WARMUP
        # ----------------------------------------------------

        dataset = dataset.dropna(
            subset=feature_columns
        )

        # ----------------------------------------------------
        # SORT AGAIN
        # ----------------------------------------------------

        dataset = (
            dataset
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        output_path = (
            self.processed_dir
            / f"direction_{symbol.lower()}.parquet"
        )

        dataset.to_parquet(
            output_path,
            index=False
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        up_count = int(
            (dataset["target"] == 1).sum()
        )

        down_count = int(
            (dataset["target"] == 0).sum()
        )

        print(
            f"[DIRECTION] Final rows: "
            f"{len(dataset)}"
        )

        print(
            f"[DIRECTION] Features: "
            f"{len(feature_columns)}"
        )

        print(
            f"[DIRECTION] UP: "
            f"{up_count}"
        )

        print(
            f"[DIRECTION] DOWN: "
            f"{down_count}"
        )

        print(
            f"[DIRECTION] Saved: "
            f"{output_path}"
        )

        return dataset