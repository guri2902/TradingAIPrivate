# ============================================================
# TradingAI - OPTION MOVEMENT DATASET
# ============================================================

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

HISTORY_PATH = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "nifty_option_history.parquet"
)

OUTPUT_PATH = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "option_movement_nifty.parquet"
)


# ============================================================
# DATASET BUILDER
# ============================================================

class OptionMovementDataset:

    KEY_COLUMNS = [
        "symbol",
        "expiry",
        "strike",
        "option_type",
    ]

    # --------------------------------------------------------
    # Raw/current snapshot features
    # --------------------------------------------------------

    FEATURE_COLUMNS = [
        "last_price",
        "change",
        "percent_change",

        "volume",

        "oi",
        "oi_change",

        "iv",

        "bid_price",
        "ask_price",

        "bid_quantity",
        "ask_quantity",

        "total_buy_quantity",
        "total_sell_quantity",

        "underlying_value",

        # Current snapshot derived features
        "premium_return_current",
        "premium_change_current",
        "oi_change_pct_current",
        "iv_change_current",
        "volume_change_current",
        "underlying_return_current",

        "moneyness",
        "distance_from_atm_pct",
        "intrinsic_value",
        "time_value",
        "oi_volume_ratio",
        "bid_ask_spread",
        "bid_ask_mid",
        "premium_vs_mid",
    ]

    # --------------------------------------------------------
    # Model labels
    #
    # IMPORTANT:
    # Must match OptionMovementModel.LABELS
    #
    # -1 = DOWN
    #  0 = SIDEWAYS
    #  1 = UP
    # --------------------------------------------------------

    LABELS = {
        -1: "DOWN",
        0: "SIDEWAYS",
        1: "UP",
    }

    # ========================================================
    # LOAD HISTORY
    # ========================================================

    def load_history(self):

        if not HISTORY_PATH.exists():

            raise RuntimeError(
                f"Option history not found: "
                f"{HISTORY_PATH}"
            )

        df = pd.read_parquet(
            HISTORY_PATH
        )

        if df.empty:

            raise RuntimeError(
                "Option history is empty."
            )

        # ----------------------------------------------------
        # Normalize column names
        # ----------------------------------------------------

        df.columns = [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            for column in df.columns
        ]

        # ----------------------------------------------------
        # Common aliases
        # ----------------------------------------------------

        aliases = {

            "date":
                "timestamp",

            "datetime":
                "timestamp",

            "strikeprice":
                "strike",

            "strike_price":
                "strike",

            "optiontype":
                "option_type",

            "type":
                "option_type",

            "expirydate":
                "expiry",

            "expiry_date":
                "expiry",

            "lastprice":
                "last_price",

            "ltp":
                "last_price",

            "openinterest":
                "oi",

            "changeinoi":
                "oi_change",

            "change_in_oi":
                "oi_change",

            "impliedvolatility":
                "iv",

            "implied_volatility":
                "iv",

            # ------------------------------------------------
            # Important:
            # Actual NSE option history uses underlying_value
            # ------------------------------------------------

            "underlyingvalue":
                "underlying_value",

            "underlying_price":
                "underlying_value",

            "underlying_close":
                "underlying_value",
        }

        for old, new in aliases.items():

            if (
                old in df.columns
                and new not in df.columns
            ):

                df[new] = df[old]

        # ----------------------------------------------------
        # Required columns
        # ----------------------------------------------------

        required = [
            "timestamp",
            "symbol",
            "expiry",
            "strike",
            "option_type",
            "last_price",
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:

            raise RuntimeError(
                "Missing required option-history "
                f"columns: {missing}"
            )

        # ----------------------------------------------------
        # Timestamps
        # ----------------------------------------------------

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

        df["expiry"] = pd.to_datetime(
            df["expiry"],
            errors="coerce",
        )

        # ----------------------------------------------------
        # Numeric columns
        # ----------------------------------------------------

        numeric_columns = [
            "strike",
            "last_price",
            "change",
            "percent_change",
            "volume",
            "oi",
            "oi_change",
            "iv",
            "bid_price",
            "ask_price",
            "bid_quantity",
            "ask_quantity",
            "total_buy_quantity",
            "total_sell_quantity",
            "underlying_value",
        ]

        for column in numeric_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

        # ----------------------------------------------------
        # Option type
        # ----------------------------------------------------

        df["option_type"] = (
            df["option_type"]
            .astype(str)
            .str.upper()
            .str.strip()
            .replace(
                {
                    "CALL": "CE",
                    "PUT": "PE",
                }
            )
        )

        # ----------------------------------------------------
        # Drop invalid rows
        # ----------------------------------------------------

        df = df.dropna(
            subset=[
                "timestamp",
                "expiry",
                "strike",
                "option_type",
                "last_price",
            ]
        )

        # ----------------------------------------------------
        # Keep valid option contracts only
        # ----------------------------------------------------

        df = df[
            df["option_type"].isin(
                [
                    "CE",
                    "PE",
                ]
            )
        ].copy()

        # ----------------------------------------------------
        # Optional columns
        # ----------------------------------------------------

        defaults = {

            "change":
                0.0,

            "percent_change":
                0.0,

            "volume":
                0.0,

            "oi":
                0.0,

            "oi_change":
                0.0,

            "iv":
                0.0,

            "bid_price":
                0.0,

            "ask_price":
                0.0,

            "bid_quantity":
                0.0,

            "ask_quantity":
                0.0,

            "total_buy_quantity":
                0.0,

            "total_sell_quantity":
                0.0,

            "underlying_value":
                np.nan,
        }

        for column, default in defaults.items():

            if column not in df.columns:

                df[column] = default

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            if (
                default is not None
                and not pd.isna(default)
            ):

                df[column] = (
                    df[column]
                    .fillna(default)
                )

        # ----------------------------------------------------
        # Underlying is mandatory for useful movement data
        # ----------------------------------------------------

        if df[
            "underlying_value"
        ].notna().sum() == 0:

            raise RuntimeError(
                "No valid underlying_value data "
                "is available."
            )

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        df = (
            df
            .sort_values(
                [
                    "timestamp",
                    "symbol",
                    "expiry",
                    "strike",
                    "option_type",
                ]
            )
            .reset_index(drop=True)
        )

        return df

    # ========================================================
    # BUILD CURRENT-SNAPSHOT FEATURES
    # ========================================================

    def _build_current_features(
        self,
        df,
    ):

        df = df.copy()

        # ----------------------------------------------------
        # Contract grouping
        # ----------------------------------------------------

        contract_group = (
            df.groupby(
                self.KEY_COLUMNS,
                sort=False,
                observed=True,
            )
        )

        # ----------------------------------------------------
        # Historical premium movement
        #
        # These are FEATURES, not targets.
        # They only use information from prior/current
        # snapshots.
        # ----------------------------------------------------

        df[
            "premium_return_current"
        ] = (
            contract_group[
                "last_price"
            ].pct_change()
        )

        df[
            "premium_change_current"
        ] = (
            contract_group[
                "last_price"
            ].diff()
        )

        # ----------------------------------------------------
        # OI movement
        # ----------------------------------------------------

        df[
            "oi_change_pct_current"
        ] = (
            contract_group[
                "oi"
            ].pct_change()
        )

        # ----------------------------------------------------
        # IV movement
        # ----------------------------------------------------

        df[
            "iv_change_current"
        ] = (
            contract_group[
                "iv"
            ].diff()
        )

        # ----------------------------------------------------
        # Volume movement
        # ----------------------------------------------------

        df[
            "volume_change_current"
        ] = (
            contract_group[
                "volume"
            ].pct_change()
        )

        # ----------------------------------------------------
        # Underlying return
        #
        # Group by snapshot and derive underlying movement
        # between snapshots.
        # ----------------------------------------------------

        underlying_by_timestamp = (
            df.groupby(
                "timestamp",
                sort=True,
            )[
                "underlying_value"
            ]
            .first()
        )

        underlying_return = (
            underlying_by_timestamp
            .pct_change()
            .rename(
                "underlying_return_current"
            )
        )

        df = df.merge(
            underlying_return,
            left_on="timestamp",
            right_index=True,
            how="left",
        )

        # ----------------------------------------------------
        # Basic option geometry
        # ----------------------------------------------------

        safe_underlying = (
            df[
                "underlying_value"
            ].replace(
                0,
                np.nan,
            )
        )

        df[
            "moneyness"
        ] = (
            df["strike"]
            / safe_underlying
        )

        df[
            "distance_from_atm_pct"
        ] = (
            (
                df["strike"]
                - df["underlying_value"]
            )
            / safe_underlying
            * 100.0
        )

        # ----------------------------------------------------
        # Intrinsic value
        # ----------------------------------------------------

        df[
            "intrinsic_value"
        ] = np.where(
            df["option_type"] == "CE",

            np.maximum(
                df["underlying_value"]
                - df["strike"],
                0,
            ),

            np.maximum(
                df["strike"]
                - df["underlying_value"],
                0,
            ),
        )

        # ----------------------------------------------------
        # Time value
        # ----------------------------------------------------

        df[
            "time_value"
        ] = np.maximum(
            df["last_price"]
            - df["intrinsic_value"],
            0,
        )

        # ----------------------------------------------------
        # OI / volume ratio
        # ----------------------------------------------------

        df[
            "oi_volume_ratio"
        ] = (
            df["oi"]
            / df["volume"].replace(
                0,
                np.nan,
            )
        )

        # ----------------------------------------------------
        # Bid / ask information
        # ----------------------------------------------------

        df[
            "bid_ask_spread"
        ] = (
            df["ask_price"]
            - df["bid_price"]
        )

        df[
            "bid_ask_mid"
        ] = (
            df["bid_price"]
            + df["ask_price"]
        ) / 2.0

        df[
            "premium_vs_mid"
        ] = (
            df["last_price"]
            - df["bid_ask_mid"]
        )

        return df

    # ========================================================
    # BUILD TARGET DATASET
    # ========================================================

    def build(
        self,
        df,
        horizon=1,
        sideways_threshold=0.50,
        minimum_snapshots=10,
    ):

        if df is None or df.empty:

            raise ValueError(
                "Option history is empty."
            )

        df = df.copy()

        # ----------------------------------------------------
        # Snapshot count
        # ----------------------------------------------------

        timestamps = (
            df["timestamp"]
            .drop_duplicates()
            .sort_values()
            .tolist()
        )

        snapshot_count = (
            len(timestamps)
        )

        print(
            f"[OPTION-MOVEMENT] "
            f"Snapshots: {snapshot_count}"
        )

        if snapshot_count < 2:

            raise RuntimeError(
                "At least 2 option snapshots "
                "are required."
            )

        if snapshot_count < minimum_snapshots:

            print(
                "[OPTION-MOVEMENT] WARNING: "
                f"Only {snapshot_count} snapshots available. "
                f"Recommended minimum: "
                f"{minimum_snapshots}."
            )

        # ----------------------------------------------------
        # Build historical/current features BEFORE target
        # ----------------------------------------------------

        df = (
            self._build_current_features(
                df
            )
        )

        # ----------------------------------------------------
        # Create one future snapshot mapping
        #
        # This is deliberately limited to the NEXT snapshot,
        # not arbitrary future rows.
        # ----------------------------------------------------

        next_timestamp_map = {
            timestamps[i]:
                timestamps[i + horizon]
            for i in range(
                len(timestamps) - horizon
            )
        }

        frames = []

        # ----------------------------------------------------
        # Pair current snapshot with future snapshot
        # ----------------------------------------------------

        for current_ts, future_ts in (
            next_timestamp_map.items()
        ):

            current = (
                df[
                    df["timestamp"]
                    == current_ts
                ]
                .copy()
            )

            future = (
                df[
                    df["timestamp"]
                    == future_ts
                ]
                .copy()
            )

            if (
                current.empty
                or future.empty
            ):

                continue

            # ------------------------------------------------
            # Only future premium is taken from future data.
            # ------------------------------------------------

            future = future[
                self.KEY_COLUMNS
                + [
                    "last_price"
                ]
            ].copy()

            future = future.rename(
                columns={
                    "last_price":
                        "future_last_price",
                }
            )

            # ------------------------------------------------
            # Same-contract matching
            # ------------------------------------------------

            try:

                merged = (
                    current.merge(
                        future,
                        on=self.KEY_COLUMNS,
                        how="inner",
                        validate="one_to_one",
                    )
                )

            except Exception as exc:

                raise RuntimeError(
                    "Option contract matching "
                    f"failed: {exc}"
                ) from exc

            if merged.empty:

                continue

            merged[
                "future_timestamp"
            ] = future_ts

            # ------------------------------------------------
            # Premium return
            #
            # Percentage, not decimal.
            # Example:
            # 100 -> 110 = +10%
            # ------------------------------------------------

            safe_last = (
                merged[
                    "last_price"
                ].replace(
                    0,
                    np.nan,
                )
            )

            merged[
                "premium_return"
            ] = (
                (
                    merged[
                        "future_last_price"
                    ]
                    - merged[
                        "last_price"
                    ]
                )
                / safe_last
                * 100.0
            )

            # ------------------------------------------------
            # Absolute premium movement
            # ------------------------------------------------

            merged[
                "premium_change"
            ] = (
                merged[
                    "future_last_price"
                ]
                - merged[
                    "last_price"
                ]
            )

            # ------------------------------------------------
            # Target
            #
            # -1 = DOWN
            #  0 = SIDEWAYS
            #  1 = UP
            #
            # Compatible with OptionMovementModel.
            # ------------------------------------------------

            merged[
                "target"
            ] = np.select(
                [
                    merged[
                        "premium_return"
                    ]
                    > sideways_threshold,

                    merged[
                        "premium_return"
                    ]
                    < -sideways_threshold,
                ],
                [
                    1,
                    -1,
                ],
                default=0,
            )

            # Compatibility field retained for existing code.
            merged[
                "movement_target"
            ] = merged[
                "target"
            ]

            merged[
                "movement"
            ] = (
                merged[
                    "target"
                ]
                .map(
                    self.LABELS
                )
            )

            frames.append(
                merged
            )

        if not frames:

            raise RuntimeError(
                "Could not match option contracts "
                "between snapshots."
            )

        result = pd.concat(
            frames,
            ignore_index=True,
        )

        # ----------------------------------------------------
        # Remove invalid numeric values
        # ----------------------------------------------------

        result = result.replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )

        # ----------------------------------------------------
        # We require:
        #
        # current premium
        # future premium
        # premium return
        # target
        # ----------------------------------------------------

        result = result.dropna(
            subset=[
                "last_price",
                "future_last_price",
                "premium_return",
                "target",
            ]
        )

        # ----------------------------------------------------
        # Numeric target
        # ----------------------------------------------------

        result[
            "target"
        ] = (
            result["target"]
            .astype(int)
        )

        result[
            "movement_target"
        ] = (
            result["movement_target"]
            .astype(int)
        )

        # ----------------------------------------------------
        # Ensure movement labels are valid
        # ----------------------------------------------------

        result = result[
            result["target"].isin(
                [
                    -1,
                    0,
                    1,
                ]
            )
        ].copy()

        # ----------------------------------------------------
        # Useful output columns
        # ----------------------------------------------------

        existing_features = [
            column
            for column in self.FEATURE_COLUMNS
            if column in result.columns
        ]

        output_columns = [

            "timestamp",
            "future_timestamp",

            *self.KEY_COLUMNS,

            *existing_features,

            "future_last_price",
            "premium_change",
            "premium_return",

            "target",
            "movement_target",
            "movement",
        ]

        # Remove duplicate names while preserving order.
        output_columns = list(
            dict.fromkeys(
                output_columns
            )
        )

        output_columns = [
            column
            for column in output_columns
            if column in result.columns
        ]

        result = (
            result[
                output_columns
            ]
            .sort_values(
                [
                    "timestamp",
                    "symbol",
                    "expiry",
                    "strike",
                    "option_type",
                ]
            )
            .reset_index(
                drop=True
            )
        )

        return result

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
        result,
    ):

        if (
            result is None
            or result.empty
        ):

            raise RuntimeError(
                "Option movement dataset "
                "contains no rows."
            )

        # ----------------------------------------------------
        # Required columns
        # ----------------------------------------------------

        required = [
            "timestamp",
            "future_timestamp",
            "symbol",
            "expiry",
            "strike",
            "option_type",
            "last_price",
            "future_last_price",
            "premium_change",
            "premium_return",
            "target",
            "movement_target",
            "movement",
        ]

        missing = [
            column
            for column in required
            if column not in result.columns
        ]

        if missing:

            raise RuntimeError(
                "Option movement dataset "
                f"is missing columns: {missing}"
            )

        # ----------------------------------------------------
        # Label validation
        # ----------------------------------------------------

        labels = sorted(
            result[
                "target"
            ]
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        )

        invalid_labels = [
            label
            for label in labels
            if label not in (
                -1,
                0,
                1,
            )
        ]

        if invalid_labels:

            raise RuntimeError(
                f"Invalid target labels: "
                f"{invalid_labels}"
            )

        # ----------------------------------------------------
        # Same target fields
        # ----------------------------------------------------

        if not (
            result[
                "target"
            ]
            == result[
                "movement_target"
            ]
        ).all():

            raise RuntimeError(
                "target and movement_target "
                "are inconsistent."
            )

        # ----------------------------------------------------
        # No leakage
        #
        # Future columns must not be in model feature list.
        # ----------------------------------------------------

        leakage_columns = {
            "future_last_price",
            "future_premium",
            "future_premium_return",
            "premium_change",
            "premium_return",
            "target",
            "movement_target",
            "movement",
        }

        feature_leakage = (
            set(
                self.FEATURE_COLUMNS
            )
            & leakage_columns
        )

        if feature_leakage:

            raise RuntimeError(
                "Target leakage detected in "
                f"feature columns: "
                f"{sorted(feature_leakage)}"
            )

        # ----------------------------------------------------
        # Snapshot statistics
        # ----------------------------------------------------

        snapshot_count = (
            result[
                "timestamp"
            ]
            .nunique()
        )

        changed_contracts = 0

        grouped = (
            result
            .sort_values(
                "timestamp"
            )
            .groupby(
                self.KEY_COLUMNS,
                observed=True,
            )
        )

        if not result.empty:

            changed_contracts = int(
                (
                    grouped[
                        "last_price"
                    ]
                    .nunique()
                    > 1
                ).sum()
            )

        print(
            f"[OPTION-MOVEMENT] "
            f"Dataset snapshots: "
            f"{snapshot_count}"
        )

        print(
            f"[OPTION-MOVEMENT] "
            f"Contracts with observed "
            f"price movement: "
            f"{changed_contracts}"
        )

        # ----------------------------------------------------
        # Target distribution
        # ----------------------------------------------------

        distribution = (
            result[
                "target"
            ]
            .value_counts()
            .reindex(
                [
                    -1,
                    0,
                    1,
                ],
                fill_value=0,
            )
        )

        total = (
            distribution.sum()
        )

        if total > 0:

            print(
                "\n[OPTION-MOVEMENT] "
                "TARGET DISTRIBUTION:"
            )

            for label, count in (
                distribution.items()
            ):

                name = (
                    self.LABELS[
                        int(label)
                    ]
                )

                percentage = (
                    float(count)
                    / float(total)
                    * 100.0
                )

                print(
                    f"  {name:<10}: "
                    f"{int(count):>8} "
                    f"({percentage:>6.2f}%)"
                )

        # ----------------------------------------------------
        # Premium statistics
        # ----------------------------------------------------

        print(
            "\n[OPTION-MOVEMENT] "
            "PREMIUM RETURN STATISTICS:"
        )

        print(
            result[
                "premium_return"
            ]
            .describe()
            .to_string()
        )

        # ----------------------------------------------------
        # Movement sanity
        # ----------------------------------------------------

        non_zero_returns = (
            result[
                "premium_return"
            ]
            .abs()
            .gt(1e-12)
            .sum()
        )

        print(
            "\n[OPTION-MOVEMENT] "
            f"Non-zero future premium returns: "
            f"{int(non_zero_returns)}"
        )

        if non_zero_returns == 0:

            raise RuntimeError(
                "All future premium returns are zero. "
                "Real intraday movement is required "
                "before training the model."
            )

        # ----------------------------------------------------
        # Validate that at least two classes exist
        # ----------------------------------------------------

        unique_targets = (
            result[
                "target"
            ]
            .nunique()
        )

        if unique_targets < 2:

            raise RuntimeError(
                "Only one target class is present. "
                "More varied option movement is "
                "required before model training."
            )

        return True

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        df,
    ):

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        df.to_parquet(
            OUTPUT_PATH,
            index=False,
        )

        print(
            f"[OPTION-MOVEMENT] "
            f"Saved: {OUTPUT_PATH}"
        )

    # ========================================================
    # RUN
    # ========================================================

    def run(
        self,
    ):

        df = (
            self.load_history()
        )

        result = (
            self.build(
                df
            )
        )

        self.validate(
            result
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "TradingAI - OPTION MOVEMENT DATASET"
        )

        print(
            "=" * 70
        )

        print(
            f"\n[OPTION-MOVEMENT] "
            f"Final rows: {len(result)}"
        )

        print(
            f"[OPTION-MOVEMENT] "
            f"Columns: {len(result.columns)}"
        )

        print(
            "\n[OPTION-MOVEMENT] "
            "TARGET DISTRIBUTION:"
        )

        print(
            result[
                "target"
            ]
            .value_counts()
            .reindex(
                [
                    -1,
                    0,
                    1,
                ],
                fill_value=0,
            )
            .rename(
                index={
                    -1: "DOWN",
                    0: "SIDEWAYS",
                    1: "UP",
                }
            )
            .to_string()
        )

        print(
            "\n[OPTION-MOVEMENT] "
            "PREMIUM RETURN STATISTICS:"
        )

        print(
            result[
                "premium_return"
            ]
            .describe()
        )

        self.save(
            result
        )

        return result


# ============================================================
# PUBLIC HELPER
# ============================================================

def build_option_movement_dataset():

    builder = (
        OptionMovementDataset()
    )

    return builder.run()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    build_option_movement_dataset()