# ============================================================
# TradingAI - HISTORICAL DATA MANAGER
# ============================================================

from pathlib import Path
from datetime import date, datetime

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.parquet_store import ParquetStore


class HistoricalDataManager:

    def __init__(
        self,
        base_dir="market_data"
    ):

        self.base_dir = Path(base_dir)

        self.unified = UnifiedMarketData(
            base_dir=self.base_dir
        )

        self.store = ParquetStore(
            self.base_dir / "processed"
        )

    # ========================================================
    # STOCK
    # ========================================================

    def get_stock(
        self,
        symbol,
        from_date=None,
        to_date=None,
        source="eod2"
    ):

        symbol = symbol.upper()

        from_date = self._normalize_date(
            from_date
        )

        to_date = self._normalize_date(
            to_date
        )

        print(
            f"\n[HISTORY] Stock: {symbol}"
        )

        # ----------------------------------------------------
        # PARQUET DATASET NAME
        # ----------------------------------------------------

        dataset = (
            f"stock_{symbol.lower()}"
        )

        # ----------------------------------------------------
        # EXISTING DATA
        # ----------------------------------------------------

        if self.store.exists(dataset):

            print(
                f"[HISTORY] Loading cached data: "
                f"{dataset}"
            )

            df = self.store.load(dataset)

            # Apply requested date range
            df = self._filter_dates(
                df,
                from_date,
                to_date
            )

            if not df.empty:

                print(
                    f"[HISTORY] Returned "
                    f"{len(df)} cached rows"
                )

                return df

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        print(
            "[HISTORY] Cached data unavailable"
        )

        df = self.unified.get_stock_history(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            source=source
        )

        if df.empty:
            return df

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        self.store.save(
            df,
            dataset
        )

        return df

    # ========================================================
    # INDEX
    # ========================================================

    def get_index(
        self,
        symbol="NIFTY 50",
        from_date=None,
        to_date=None,
        source="nse"
    ):

        symbol = symbol.upper()

        from_date = self._normalize_date(
            from_date
        )

        to_date = self._normalize_date(
            to_date
        )

        print(
            f"\n[HISTORY] Index: {symbol}"
        )

        safe_symbol = (
            symbol.lower()
            .replace(" ", "_")
        )

        dataset = (
            f"index_{safe_symbol}"
        )

        # ----------------------------------------------------
        # CACHE
        # ----------------------------------------------------

        if self.store.exists(dataset):

            print(
                f"[HISTORY] Loading cached data: "
                f"{dataset}"
            )

            df = self.store.load(dataset)

            df = self._filter_dates(
                df,
                from_date,
                to_date
            )

            if not df.empty:

                print(
                    f"[HISTORY] Returned "
                    f"{len(df)} cached rows"
                )

                return df

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        if source == "nse":

            df = self.unified.get_index_history_nse(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date
            )

        elif source == "jugaad":

            df = self.unified.get_index_history_jugaad(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date
            )

        else:

            raise ValueError(
                f"Unknown index source: {source}"
            )

        if df.empty:
            return df

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        self.store.save(
            df,
            dataset
        )

        return df

    # ========================================================
    # OPTION CHAIN
    # ========================================================

    def get_option_chain(
        self,
        symbol="NIFTY",
        expiry=None
    ):

        symbol = symbol.upper()

        print(
            f"\n[HISTORY] Option chain: {symbol}"
        )

        # ----------------------------------------------------
        # OPTION CHAINS ARE SNAPSHOTS
        # ----------------------------------------------------
        #
        # We deliberately do not treat the live option chain
        # like ordinary historical OHLC data.
        #
        # Every retrieval gets a fresh NSE snapshot.
        #

        df = self.unified.get_option_chain(
            symbol=symbol,
            expiry=expiry
        )

        return df

    # ========================================================
    # NORMALIZE DATE
    # ========================================================

    @staticmethod
    def _normalize_date(value):

        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, date):
            return value

        return pd.Timestamp(value).date()

    # ========================================================
    # FILTER DATES
    # ========================================================

    @staticmethod
    def _filter_dates(
        df,
        from_date=None,
        to_date=None
    ):

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()

        if "timestamp" not in df.columns:
            return df

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        if from_date is not None:

            from_date = pd.Timestamp(
                from_date
            )

            df = df[
                df["timestamp"] >= from_date
            ]

        if to_date is not None:

            to_date = pd.Timestamp(
                to_date
            )

            df = df[
                df["timestamp"] <= to_date
            ]

        return (
            df.sort_values("timestamp")
              .reset_index(drop=True)
        )