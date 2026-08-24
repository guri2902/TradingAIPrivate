# ============================================================
# TradingAI - OPTION FEATURES
# Persistent historical option-chain snapshot storage
# ============================================================

from pathlib import Path
from datetime import datetime

import pandas as pd


class OptionFeatures:

    def __init__(
        self,
        output_dir="market_data/processed"
    ):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.output_file = (
            self.output_dir
            / "features_nifty_options.parquet"
        )

    # ========================================================
    # BUILD FEATURES
    # ========================================================

    def build(
        self,
        df,
        timestamp=None
    ):

        if df is None or df.empty:
            raise ValueError(
                "Option chain dataframe is empty."
            )

        df = df.copy()

        # ----------------------------------------------------
        # Normalize columns
        # ----------------------------------------------------

        df.columns = [
            str(c).lower().strip()
            for c in df.columns
        ]

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        if timestamp is None:
            timestamp = datetime.now()

        timestamp = pd.to_datetime(timestamp)

        df["timestamp"] = timestamp

        # ----------------------------------------------------
        # Normalize option type
        # ----------------------------------------------------

        if "option_type" in df.columns:

            df["option_type"] = (
                df["option_type"]
                .astype(str)
                .str.upper()
                .str.strip()
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
            "atm_strike",
        ]

        for column in numeric_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # ----------------------------------------------------
        # Basic option features
        # ----------------------------------------------------

        if (
            "strike" in df.columns
            and "atm_strike" in df.columns
        ):

            df["strike_distance"] = (
                df["strike"]
                - df["atm_strike"]
            )

            if "underlying_value" in df.columns:

                underlying = pd.to_numeric(
                    df["underlying_value"],
                    errors="coerce"
                )

                df["strike_distance_pct"] = (
                    df["strike_distance"]
                    / underlying.replace(0, pd.NA)
                )

            df["distance_from_atm"] = (
                df["strike_distance"].abs()
            )

        # ----------------------------------------------------
        # Moneyness
        # ----------------------------------------------------

        if (
            "strike" in df.columns
            and "underlying_value" in df.columns
        ):

            underlying = pd.to_numeric(
                df["underlying_value"],
                errors="coerce"
            )

            df["moneyness"] = (
                df["strike"]
                / underlying.replace(0, pd.NA)
            )

        # ----------------------------------------------------
        # Bid / Ask
        # ----------------------------------------------------

        if (
            "bid_price" in df.columns
            and "ask_price" in df.columns
        ):

            df["bid_ask_spread"] = (
                df["ask_price"]
                - df["bid_price"]
            )

            df["bid_ask_spread_pct"] = (
                df["bid_ask_spread"]
                / df["ask_price"].replace(
                    0,
                    pd.NA
                )
            )

        # ----------------------------------------------------
        # Bid / Ask imbalance
        # ----------------------------------------------------

        if (
            "bid_quantity" in df.columns
            and "ask_quantity" in df.columns
        ):

            total = (
                df["bid_quantity"]
                + df["ask_quantity"]
            )

            df["bid_ask_imbalance"] = (
                (
                    df["bid_quantity"]
                    - df["ask_quantity"]
                )
                / total.replace(
                    0,
                    pd.NA
                )
            )

        # ----------------------------------------------------
        # Buy / Sell imbalance
        # ----------------------------------------------------

        if (
            "total_buy_quantity" in df.columns
            and "total_sell_quantity" in df.columns
        ):

            total = (
                df["total_buy_quantity"]
                + df["total_sell_quantity"]
            )

            df["buy_sell_imbalance"] = (
                (
                    df["total_buy_quantity"]
                    - df["total_sell_quantity"]
                )
                / total.replace(
                    0,
                    pd.NA
                )
            )

            df["buy_sell_ratio"] = (
                df["total_buy_quantity"]
                / df["total_sell_quantity"].replace(
                    0,
                    pd.NA
                )
            )

        # ----------------------------------------------------
        # OI features
        # ----------------------------------------------------

        if (
            "oi_change" in df.columns
            and "oi" in df.columns
        ):

            df["oi_change_pct"] = (
                df["oi_change"]
                / df["oi"].replace(
                    0,
                    pd.NA
                )
            )

        if (
            "oi" in df.columns
            and "volume" in df.columns
        ):

            df["oi_volume_ratio"] = (
                df["oi"]
                / df["volume"].replace(
                    0,
                    pd.NA
                )
            )

        # ----------------------------------------------------
        # IV
        # ----------------------------------------------------

        if "iv" in df.columns:

            df["iv_decimal"] = (
                df["iv"] / 100.0
            )

        # ----------------------------------------------------
        # Moneyness type
        # ----------------------------------------------------

        if (
            "option_type" in df.columns
            and "strike" in df.columns
            and "underlying_value" in df.columns
        ):

            def classify(row):

                option_type = row["option_type"]
                strike = row["strike"]
                underlying = row["underlying_value"]

                if (
                    pd.isna(strike)
                    or pd.isna(underlying)
                ):
                    return "UNKNOWN"

                if option_type == "CE":

                    if strike < underlying:
                        return "ITM"

                    if strike > underlying:
                        return "OTM"

                    return "ATM"

                if option_type == "PE":

                    if strike > underlying:
                        return "ITM"

                    if strike < underlying:
                        return "OTM"

                    return "ATM"

                return "UNKNOWN"

            df["moneyness_type"] = (
                df.apply(
                    classify,
                    axis=1
                )
            )

        # ----------------------------------------------------
        # IMPORTANT
        #
        # Every call represents ONE historical snapshot.
        # Append it to persistent storage.
        # ----------------------------------------------------

        self._append_snapshot(df)

        return df

    # ========================================================
    # APPEND SNAPSHOT
    # ========================================================

    def _append_snapshot(
        self,
        snapshot
    ):

        if (
            snapshot is None
            or snapshot.empty
        ):
            return

        snapshot = snapshot.copy()

        # ----------------------------------------------------
        # Normalize timestamp
        # ----------------------------------------------------

        snapshot["timestamp"] = pd.to_datetime(
            snapshot["timestamp"]
        )

        snapshot_timestamp = (
            snapshot["timestamp"].iloc[0]
        )

        # ----------------------------------------------------
        # Load existing history
        # ----------------------------------------------------

        if self.output_file.exists():

            try:

                history = pd.read_parquet(
                    self.output_file
                )

            except Exception as exc:

                print(
                    "[OPTIONS] Existing history "
                    f"could not be read: {exc}"
                )

                history = pd.DataFrame()

        else:

            history = pd.DataFrame()

        # ----------------------------------------------------
        # If this exact timestamp already exists,
        # replace that snapshot instead of duplicating it.
        # ----------------------------------------------------

        if not history.empty:

            history["timestamp"] = pd.to_datetime(
                history["timestamp"]
            )

            history = history[
                history["timestamp"]
                != snapshot_timestamp
            ].copy()

        # ----------------------------------------------------
        # Align columns
        # ----------------------------------------------------

        if history.empty:

            combined = snapshot

        else:

            all_columns = list(
                dict.fromkeys(
                    list(history.columns)
                    + list(snapshot.columns)
                )
            )

            history = history.reindex(
                columns=all_columns
            )

            snapshot = snapshot.reindex(
                columns=all_columns
            )

            combined = pd.concat(
                [
                    history,
                    snapshot
                ],
                ignore_index=True
            )

        # ----------------------------------------------------
        # Remove duplicate contracts
        #
        # Same timestamp + expiry + strike + option type
        # = same contract snapshot.
        # ----------------------------------------------------

        duplicate_columns = [
            c
            for c in [
                "timestamp",
                "symbol",
                "expiry",
                "strike",
                "option_type",
            ]
            if c in combined.columns
        ]

        if duplicate_columns:

            combined = (
                combined
                .drop_duplicates(
                    subset=duplicate_columns,
                    keep="last"
                )
            )

        # ----------------------------------------------------
        # Sort chronologically
        # ----------------------------------------------------

        sort_columns = [
            c
            for c in [
                "timestamp",
                "expiry",
                "strike",
                "option_type",
            ]
            if c in combined.columns
        ]

        if sort_columns:

            combined = (
                combined
                .sort_values(sort_columns)
                .reset_index(drop=True)
            )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        combined.to_parquet(
            self.output_file,
            index=False
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        print(
            "\n[OPTIONS] Historical snapshot saved"
        )

        print(
            f"[OPTIONS] Snapshot timestamp: "
            f"{snapshot_timestamp}"
        )

        print(
            f"[OPTIONS] Snapshot rows: "
            f"{len(snapshot)}"
        )

        print(
            f"[OPTIONS] Total rows: "
            f"{len(combined)}"
        )

        print(
            f"[OPTIONS] Total timestamps: "
            f"{combined['timestamp'].nunique()}"
        )

        print(
            f"[OPTIONS] File: "
            f"{self.output_file}"
        )

    # ========================================================
    # LOAD HISTORY
    # ========================================================

    def load_history(self):

        if not self.output_file.exists():

            return pd.DataFrame()

        try:

            df = pd.read_parquet(
                self.output_file
            )

            if "timestamp" in df.columns:

                df["timestamp"] = pd.to_datetime(
                    df["timestamp"]
                )

            return df

        except Exception as exc:

            print(
                "[OPTIONS] Failed to load history: "
                f"{exc}"
            )

            return pd.DataFrame()

    # ========================================================
    # HISTORY STATUS
    # ========================================================

    def history_status(self):

        df = self.load_history()

        if df.empty:

            return {
                "rows": 0,
                "timestamps": 0,
                "start": None,
                "end": None,
            }

        return {
            "rows": len(df),
            "timestamps": df["timestamp"].nunique(),
            "start": df["timestamp"].min(),
            "end": df["timestamp"].max(),
        }