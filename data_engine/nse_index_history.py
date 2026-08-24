# ============================================================
# TradingAI - NSE INDEX HISTORY ADAPTER
# ============================================================

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from nse import NSE


class NseIndexHistory:

    INDEX_NAMES = {
        "NIFTY": "NIFTY 50",
        "BANKNIFTY": "NIFTY BANK",
    }

    def __init__(
        self,
        download_folder="market_data/raw/nse",
    ):

        self.download_folder = Path(
            download_folder
        )

        self.download_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.nse = NSE(
            download_folder=self.download_folder
        )

    # ========================================================
    # SYMBOL
    # ========================================================

    def resolve_index_name(
        self,
        symbol: str,
    ) -> str:

        key = (
            str(symbol)
            .strip()
            .upper()
        )

        return self.INDEX_NAMES.get(
            key,
            key,
        )

    # ========================================================
    # FETCH
    # ========================================================

    def get_history(
        self,
        symbol: str,
        from_date: date | datetime,
        to_date: date | datetime,
    ) -> pd.DataFrame:

        index_name = (
            self.resolve_index_name(
                symbol
            )
        )

        print(
            f"\n[NSE-INDEX] "
            f"Loading {index_name}"
        )

        # NseIndiaApi exposes historical index
        # functionality through the NSE client.
        raw = self.nse.fetch_historical_index_data(
            index_name,
            from_date,
            to_date,
        )

        if raw is None:

            raise RuntimeError(
                f"No NSE index data returned "
                f"for {index_name}."
            )

        # ----------------------------------------------------
        # Convert to DataFrame
        # ----------------------------------------------------

        if isinstance(
            raw,
            pd.DataFrame,
        ):

            df = raw.copy()

        elif isinstance(
            raw,
            list,
        ):

            df = pd.DataFrame(
                raw
            )

        elif isinstance(
            raw,
            dict,
        ):

            # Try common payload keys.
            records = (
                raw.get(
                    "data"
                )
                or raw.get(
                    "records"
                )
                or raw.get(
                    "dataRecords"
                )
                or []
            )

            df = pd.DataFrame(
                records
            )

        else:

            raise RuntimeError(
                "Unexpected NSE index "
                f"response type: "
                f"{type(raw).__name__}"
            )

        if df.empty:

            raise RuntimeError(
                f"NSE index history is empty "
                f"for {index_name}."
            )

        # ----------------------------------------------------
        # Normalize columns
        # ----------------------------------------------------

        df.columns = [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            for column in df.columns
        ]

        aliases = {
            "eod_index_name": "symbol",
            "eod_open_index_val": "open",
            "eod_high_index_val": "high",
            "eod_low_index_val": "low",
            "eod_close_index_val": "close",
            "eod_timestamp": "timestamp",

            "index_date": "timestamp",
            "date": "timestamp",
            "datetime": "timestamp",
        }

        for old, new in aliases.items():

            if (
                old in df.columns
                and new not in df.columns
            ):

                df[new] = df[old]

        # ----------------------------------------------------
        # Symbol
        # ----------------------------------------------------

        if "symbol" not in df.columns:

            df["symbol"] = index_name

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        if "timestamp" not in df.columns:

            raise RuntimeError(
                f"Could not identify timestamp "
                f"column in NSE response: "
                f"{df.columns.tolist()}"
            )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
            dayfirst=True,
        )

        # ----------------------------------------------------
        # OHLC
        # ----------------------------------------------------

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

            raise RuntimeError(
                "NSE index response is missing "
                f"OHLC columns: {missing}. "
                f"Available: "
                f"{df.columns.tolist()}"
            )

        # ----------------------------------------------------
        # Numeric conversion
        # ----------------------------------------------------

        for column in required:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        # ----------------------------------------------------
        # Volume
        # ----------------------------------------------------

        if "volume" not in df.columns:

            if "hit_traded_qty" in df.columns:

                df["volume"] = pd.to_numeric(
                    df["hit_traded_qty"],
                    errors="coerce",
                )

            elif "traded_quantity" in df.columns:

                df["volume"] = pd.to_numeric(
                    df["traded_quantity"],
                    errors="coerce",
                )

            else:

                df["volume"] = 0.0

        # ----------------------------------------------------
        # Clean
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
            .sort_values("timestamp")
            .drop_duplicates(
                subset=["timestamp"],
                keep="last",
            )
            .reset_index(drop=True)
        )

        # ----------------------------------------------------
        # Common TradingAI schema
        # ----------------------------------------------------

        result = df[
            [
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ].copy()

        result["symbol"] = symbol.upper()

        # Put symbol first-ish in predictable order.
        result = result[
            [
                "timestamp",
                "symbol",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ]

        print(
            f"[NSE-INDEX] "
            f"{symbol.upper()}: "
            f"{len(result)} rows"
        )

        return result