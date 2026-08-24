# ============================================================
# TradingAI - NSE FUTURES HISTORY
# ============================================================

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from jugaad_data.nse import derivatives_df


class NseFuturesHistory:

    DEFAULT_EXPIRIES = {
        "NIFTY": "2026-08-25",
        "BANKNIFTY": "2026-08-25",
    }

    def __init__(
        self,
        output_dir="market_data/raw/nse_futures",
    ):

        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ========================================================
    # SYMBOL
    # ========================================================

    @staticmethod
    def resolve_symbol(
        symbol: str,
    ) -> str:

        return (
            str(symbol)
            .strip()
            .upper()
        )

    # ========================================================
    # EXPIRY
    # ========================================================

    def get_nearest_expiry(
        self,
        symbol: str = "NIFTY",
    ):

        symbol = (
            self.resolve_symbol(
                symbol
            )
        )

        expiry = (
            self.DEFAULT_EXPIRIES
            .get(symbol)
        )

        if expiry is None:

            raise RuntimeError(
                f"No default futures expiry "
                f"configured for {symbol}."
            )

        return pd.Timestamp(
            expiry
        )

    # ========================================================
    # HISTORY
    # ========================================================

    def get_history(
        self,
        symbol: str = "NIFTY",
        from_date: date | None = None,
        to_date: date | None = None,
        expiry=None,
    ) -> pd.DataFrame:

        symbol = (
            self.resolve_symbol(
                symbol
            )
        )

        if from_date is None:

            from_date = date(
                2026,
                1,
                1,
            )

        if to_date is None:

            to_date = date.today()

        if expiry is None:

            expiry = (
                self.get_nearest_expiry(
                    symbol
                )
            )

        if isinstance(
            expiry,
            pd.Timestamp,
        ):

            expiry_for_api = (
                expiry.date()
            )

        else:

            expiry_for_api = expiry

        print(
            "\n[NSE-FUTURES] "
            f"Loading {symbol}"
        )

        print(
            "[NSE-FUTURES] "
            f"Expiry: {expiry_for_api}"
        )

        # ----------------------------------------------------
        # Direct FUTIDX request.
        #
        # No expiry_dates() call.
        # ----------------------------------------------------

        df = derivatives_df(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            expiry_date=expiry_for_api,
            instrument_type="FUTIDX",
        )

        if df is None:

            raise RuntimeError(
                f"No futures data returned "
                f"for {symbol}."
            )

        df = df.copy()

        if df.empty:

            raise RuntimeError(
                f"Futures history is empty "
                f"for {symbol} "
                f"expiry={expiry_for_api}."
            )

        # ----------------------------------------------------
        # NORMALIZE COLUMN NAMES
        # ----------------------------------------------------

        df.columns = [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            for column in df.columns
        ]

        # Actual Jugaad columns:
        #
        # date
        # expiry
        # open
        # high
        # low
        # close
        # ltp
        # settle_price
        # total_traded_quantity
        # market_lot
        # premium_value
        # open_interest
        # change_in_oi
        # symbol

        aliases = {

            "date":
                "timestamp",

            "ltp":
                "ltp",

            "settle_price":
                "settle_price",

            "total_traded_quantity":
                "volume",

            "open_interest":
                "oi",

            "change_in_oi":
                "oi_change",
        }

        for old, new in aliases.items():

            if old in df.columns:

                if new not in df.columns:

                    df[new] = df[old]

        # ----------------------------------------------------
        # REQUIRED PRICE DATA
        # ----------------------------------------------------

        required = [
            "timestamp",
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

            raise RuntimeError(
                "Futures data missing "
                f"columns: {missing}. "
                f"Available: "
                f"{df.columns.tolist()}"
            )

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

        # ----------------------------------------------------
        # NUMERIC
        # ----------------------------------------------------

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "ltp",
            "settle_price",
            "volume",
            "oi",
            "oi_change",
            "market_lot",
            "premium_value",
        ]

        for column in numeric_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

        # ----------------------------------------------------
        # OPTIONAL FIELDS
        # ----------------------------------------------------

        if "volume" not in df.columns:

            df["volume"] = 0.0

        if "oi" not in df.columns:

            df["oi"] = 0.0

        if "oi_change" not in df.columns:

            df["oi_change"] = 0.0

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        df["symbol"] = symbol

        df["expiry"] = pd.Timestamp(
            expiry_for_api
        )

        df["source"] = (
            "jugaad-data"
        )

        # ----------------------------------------------------
        # CLEAN
        # ----------------------------------------------------

        df = df.dropna(
            subset=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
            ]
        )

        df = (
            df
            .sort_values(
                "timestamp"
            )
            .drop_duplicates(
                subset=[
                    "timestamp",
                ],
                keep="last",
            )
            .reset_index(
                drop=True
            )
        )

        if df.empty:

            raise RuntimeError(
                f"No valid futures rows "
                f"remain for {symbol}."
            )

        # ----------------------------------------------------
        # FINAL COMMON SCHEMA
        # ----------------------------------------------------

        result = df[
            [
                "timestamp",
                "symbol",
                "expiry",
                "open",
                "high",
                "low",
                "close",
                "ltp",
                "settle_price",
                "volume",
                "oi",
                "oi_change",
                "market_lot",
                "premium_value",
                "source",
            ]
        ].copy()

        print(
            f"[NSE-FUTURES] "
            f"Rows: {len(result)}"
        )

        print(
            "[NSE-FUTURES] "
            f"Date range: "
            f"{result['timestamp'].min()} "
            f"-> "
            f"{result['timestamp'].max()}"
        )

        return result

    # ========================================================
    # LATEST
    # ========================================================

    def get_latest(
        self,
        symbol: str = "NIFTY",
    ):

        df = self.get_history(
            symbol=symbol
        )

        if df.empty:

            return None

        return (
            df
            .sort_values(
                "timestamp"
            )
            .iloc[-1]
            .to_dict()
        )