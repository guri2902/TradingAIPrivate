# ============================================================
# TradingAI - INDEX MODEL DATASET
# ============================================================

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from data_engine.feature_engineering import FeatureEngineering


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

SOURCE_PATH = (
    BASE_DIR
    / "market_data"
    / "raw"
    / "eod2"
    / "daily"
    / "nifty 50.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "nifty_index_ml_dataset.parquet"
)


class IndexModelDataset:

    # ========================================================
    # FEATURE EXCLUSIONS
    # ========================================================

    EXCLUDED_FEATURES = {
        "timestamp",
        "symbol",
        "series",
        "p/e",

        # Stock-delivery specific
        "total_trades",
        "qty_per_trade",
        "dlv_qty",
    }

    # ========================================================
    # LOAD RAW
    # ========================================================

    def load_raw(self):

        if not SOURCE_PATH.exists():

            raise FileNotFoundError(
                f"NIFTY EOD2 file not found: "
                f"{SOURCE_PATH}"
            )

        df = pd.read_csv(
            SOURCE_PATH
        )

        df.columns = [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            for column in df.columns
        ]

        aliases = {
            "date": "timestamp",
        }

        for old, new in aliases.items():

            if (
                old in df.columns
                and new not in df.columns
            ):

                df[new] = df[old]

        required = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:

            raise RuntimeError(
                f"NIFTY dataset missing "
                f"columns: {missing}"
            )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "p/e",
            "total_trades",
            "qty_per_trade",
            "dlv_qty",
        ]:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

        df = (
            df
            .dropna(
                subset=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                ]
            )
            .sort_values(
                "timestamp"
            )
            .drop_duplicates(
                subset=["timestamp"],
                keep="last",
            )
            .reset_index(drop=True)
        )

        return df

    # ========================================================
    # BUILD FEATURES
    # ========================================================

    def build_features(
        self,
        raw_df,
    ):

        engineer = (
            FeatureEngineering()
        )

        feature_df = (
            engineer.build_features(
                raw_df.copy()
            )
        )

        if feature_df.empty:

            raise RuntimeError(
                "Feature engineering "
                "returned no rows."
            )

        return feature_df

    # ========================================================
    # SELECT FEATURES
    # ========================================================

    def select_features(
        self,
        df,
    ):

        candidates = []

        for column in df.columns:

            if column in self.EXCLUDED_FEATURES:

                continue

            if not pd.api.types.is_numeric_dtype(
                df[column]
            ):

                continue

            candidates.append(
                column
            )

        if not candidates:

            raise RuntimeError(
                "No numeric index ML features "
                "were found."
            )

        return candidates

    # ========================================================
    # BUILD TARGETS
    # ========================================================

    def build_targets(
        self,
        df,
    ):

        result = df.copy()

        # ----------------------------------------------------
        # Next-period return
        # ----------------------------------------------------

        result[
            "future_close"
        ] = result[
            "close"
        ].shift(-1)

        result[
            "future_return"
        ] = (
            (
                result["future_close"]
                - result["close"]
            )
            / result["close"]
        )

        # ----------------------------------------------------
        # Direction
        #
        # 0 = DOWN
        # 1 = UP
        # ----------------------------------------------------

        result[
            "direction_target"
        ] = np.where(
            result[
                "future_return"
            ] >= 0,
            1,
            0,
        )

        # ----------------------------------------------------
        # Regime
        #
        # Based on 5-period forward return.
        #
        # -1 = BEAR
        #  0 = SIDEWAYS
        #  1 = BULL
        # ----------------------------------------------------

        future_close_5 = (
            result[
                "close"
            ].shift(-5)
        )

        result[
            "future_return_5"
        ] = (
            (
                future_close_5
                - result["close"]
            )
            / result["close"]
        )

        regime_threshold = 0.003

        result[
            "regime_target"
        ] = np.select(
            [
                result[
                    "future_return_5"
                ] > regime_threshold,

                result[
                    "future_return_5"
                ] < -regime_threshold,
            ],
            [
                1,
                -1,
            ],
            default=0,
        )

        # ----------------------------------------------------
        # Future realized volatility
        #
        # Standard deviation of the next 5 daily returns.
        # ----------------------------------------------------

        next_returns = (
            result[
                "close"
            ]
            .pct_change()
            .shift(-1)
        )

        future_volatility = []

        values = (
            next_returns
            .to_numpy()
        )

        horizon = 5

        for index in range(
            len(values)
        ):

            window = values[
                index:
                index + horizon
            ]

            if len(window) < horizon:

                future_volatility.append(
                    np.nan
                )

            elif np.isnan(
                window
            ).any():

                future_volatility.append(
                    np.nan
                )

            else:

                future_volatility.append(
                    float(
                        np.std(
                            window,
                            ddof=0,
                        )
                    )
                )

        result[
            "volatility_target"
        ] = future_volatility

        return result

    # ========================================================
    # BUILD
    # ========================================================

    def build(self):

        print(
            "=" * 70
        )

        print(
            "TradingAI - INDEX MODEL DATASET"
        )

        print(
            "=" * 70
        )

        raw = (
            self.load_raw()
        )

        print(
            f"Raw rows: {len(raw)}"
        )

        features = (
            self.build_features(
                raw
            )
        )

        print(
            f"Feature rows: "
            f"{len(features)}"
        )

        feature_columns = (
            self.select_features(
                features
            )
        )

        print(
            f"Numeric index features: "
            f"{len(feature_columns)}"
        )

        print(
            "\nExcluded:"
        )

        print(
            sorted(
                self.EXCLUDED_FEATURES
                & set(features.columns)
            )
        )

        dataset = (
            self.build_targets(
                features
            )
        )

        # ----------------------------------------------------
        # Keep only rows with future targets.
        # ----------------------------------------------------

        dataset = dataset.dropna(
            subset=[
                "future_close",
                "future_return",
                "future_return_5",
                "volatility_target",
            ]
        )

        # ----------------------------------------------------
        # Build final dataset
        # ----------------------------------------------------

        output_columns = [
            "timestamp",
        ]

        output_columns += (
            feature_columns
        )

        output_columns += [
            "future_close",
            "future_return",
            "future_return_5",
            "direction_target",
            "regime_target",
            "volatility_target",
        ]

        output_columns = [
            column
            for column in output_columns
            if column in dataset.columns
        ]

        dataset = (
            dataset[
                output_columns
            ]
            .replace(
                [
                    np.inf,
                    -np.inf,
                ],
                np.nan,
            )
            .dropna()
            .reset_index(
                drop=True
            )
        )

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        dataset.to_parquet(
            OUTPUT_PATH,
            index=False,
        )

        print(
            f"\nFinal rows: "
            f"{len(dataset)}"
        )

        print(
            f"Final columns: "
            f"{len(dataset.columns)}"
        )

        print(
            "\nDirection distribution:"
        )

        print(
            dataset[
                "direction_target"
            ]
            .value_counts()
            .sort_index()
        )

        print(
            "\nRegime distribution:"
        )

        print(
            dataset[
                "regime_target"
            ]
            .value_counts()
            .sort_index()
        )

        print(
            "\nVolatility statistics:"
        )

        print(
            dataset[
                "volatility_target"
            ].describe()
        )

        print(
            f"\nSaved: {OUTPUT_PATH}"
        )

        return dataset


def build_index_model_dataset():

    builder = (
        IndexModelDataset()
    )

    return builder.build()


if __name__ == "__main__":

    build_index_model_dataset()