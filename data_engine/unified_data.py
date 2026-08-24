# ============================================================
# TradingAI - UNIFIED MARKET DATA LAYER
# ============================================================

from pathlib import Path
from datetime import date, datetime

import pandas as pd

from data_engine.jugaad_source import JugaadSource
from data_engine.eod2_source import EOD2Source
from data_engine.nse_source import NseSource


class UnifiedMarketData:

    def __init__(self, base_dir="market_data"):

        self.base_dir = Path(base_dir)

        # ----------------------------------------------------
        # DATA SOURCES
        # ----------------------------------------------------

        self.jugaad = JugaadSource(
            self.base_dir / "raw" / "jugaad"
        )

        self.eod2 = EOD2Source(
            self.base_dir / "raw" / "eod2_data"
        )

        self.nse = NseSource(
            self.base_dir / "raw" / "nse"
        )

    # ========================================================
    # STOCK HISTORY
    # ========================================================

    def get_stock_history(
        self,
        symbol,
        from_date=None,
        to_date=None,
        source="eod2"
    ):

        symbol = symbol.upper()
        source = source.lower()

        print(
            f"\n[UNIFIED] Stock history: "
            f"{symbol} | source={source}"
        )

        # ----------------------------------------------------
        # EOD2
        # ----------------------------------------------------

        if source == "eod2":

            df = self.eod2.get_stock(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date
            )

            df = self._normalize_stock(
                df,
                symbol=symbol,
                source="eod2"
            )

            return df

        # ----------------------------------------------------
        # JUGAAD
        # ----------------------------------------------------

        if source == "jugaad":

            if from_date is None:
                from_date = date.today()

            if to_date is None:
                to_date = date.today()

            df = self.jugaad.get_stock(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date
            )

            df = self._normalize_stock(
                df,
                symbol=symbol,
                source="jugaad"
            )

            return df

        raise ValueError(
            f"Unknown stock data source: {source}"
        )

    # ========================================================
    # INDEX HISTORY - JUGAAD
    # ========================================================

    def get_index_history_jugaad(
        self,
        symbol,
        from_date,
        to_date
    ):

        print(
            f"\n[UNIFIED] Index history: "
            f"{symbol} | source=jugaad"
        )

        df = self.jugaad.get_index(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date
        )

        return self._normalize_index(
            df,
            symbol=symbol,
            source="jugaad"
        )

    # ========================================================
    # INDEX HISTORY - NSE
    # ========================================================

    def get_index_history_nse(
        self,
        symbol="NIFTY 50",
        from_date=None,
        to_date=None
    ):

        if from_date is None:
            from_date = date.today()

        if to_date is None:
            to_date = date.today()

        print(
            f"\n[UNIFIED] Index history: "
            f"{symbol} | source=nse"
        )

        records = self.nse.get_index_history(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date
        )

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)

        rename_map = {
            "EOD_TIMESTAMP": "timestamp",
            "EOD_INDEX_NAME": "symbol",
            "EOD_OPEN_INDEX_VAL": "open",
            "EOD_HIGH_INDEX_VAL": "high",
            "EOD_LOW_INDEX_VAL": "low",
            "EOD_CLOSE_INDEX_VAL": "close",
            "HIT_TRADED_QTY": "volume",
            "HIT_TURN_OVER": "turnover",
        }

        df = df.rename(
            columns=rename_map
        )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            format="%d-%b-%Y",
            errors="coerce"
        )

        df["symbol"] = symbol.upper()

        df["source"] = "nse"

        return (
            df.sort_values("timestamp")
              .reset_index(drop=True)
        )

    # ========================================================
    # OPTION CHAIN
    # ========================================================

    def get_option_chain(
        self,
        symbol="NIFTY",
        expiry=None
    ):

        print(
            f"\n[UNIFIED] Option chain: "
            f"{symbol}"
        )

        df = self.nse.get_option_chain(
            symbol=symbol,
            expiry=expiry
        )

        if df is None:
            return pd.DataFrame()

        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        return df.reset_index(
            drop=True
        )

    # ========================================================
    # FUTURES
    # ========================================================

    def get_futures(
        self,
        symbol="NIFTY"
    ):

        symbol = str(symbol).upper()

        print(
            f"\n[UNIFIED] Futures: "
            f"{symbol}"
        )

        df = self.nse.get_futures(
            symbol=symbol
        )

        if df is None:
            return pd.DataFrame()

        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        return (
            df.sort_values(
                "expiry"
            )
            .reset_index(
                drop=True
            )
        )
    # ========================================================
    # NORMALIZE STOCK
    # ========================================================

    @staticmethod
    def _normalize_stock(
        df,
        symbol,
        source
    ):

        if df is None:
            return pd.DataFrame()

        df = df.copy()

        # ----------------------------------------------------
        # COLUMN MATCHING
        # ----------------------------------------------------

        rename_map = {}

        columns_lower = {
            str(column).lower(): column
            for column in df.columns
        }

        standard_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        for column in standard_columns:

            if column in columns_lower:

                actual = columns_lower[column]

                if actual != column:
                    rename_map[actual] = column

        if rename_map:
            df = df.rename(
                columns=rename_map
            )

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        if "timestamp" not in df.columns:

            date_candidates = [
                "date",
                "Date",
                "DATE",
            ]

            found = None

            for column in date_candidates:

                if column in df.columns:
                    found = column
                    break

            if found is not None:

                df["timestamp"] = pd.to_datetime(
                    df[found],
                    errors="coerce"
                )

        else:

            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

        # ----------------------------------------------------
        # SYMBOL
        # ----------------------------------------------------

        df["symbol"] = symbol.upper()

        # ----------------------------------------------------
        # SOURCE
        # ----------------------------------------------------

        df["source"] = source

        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            df = df.sort_values(
                "timestamp"
            )

        return df.reset_index(
            drop=True
        )

    # ========================================================
    # NORMALIZE INDEX
    # ========================================================

    @staticmethod
    def _normalize_index(
        df,
        symbol,
        source
    ):

        if df is None:
            return pd.DataFrame()

        df = df.copy()

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        df["symbol"] = symbol.upper()

        df["source"] = source

        return (
            df.sort_values("timestamp")
              .reset_index(drop=True)
        )

    # ========================================================
    # MARKET SNAPSHOT
    # ========================================================

    def get_market_snapshot(
        self,
        symbol="NIFTY"
    ):

        print(
            f"\n[UNIFIED] Creating market snapshot: "
            f"{symbol}"
        )

        option_chain = self.get_option_chain(
            symbol=symbol
        )

        return {
            "timestamp": datetime.now(),
            "symbol": symbol.upper(),
            "option_chain": option_chain,
        }

    # ========================================================
    # LIVE MARKET DATA
    # ========================================================

    def get_live_market_data(
        self,
        symbol="NIFTY"
    ):
        """
        Return a unified live market snapshot.

        Currently combines:
            - Option chain
            - Futures
            - Underlying value

        This is intentionally kept inside Step 1:
        Data Foundation.
        """

        symbol = symbol.upper()

        print(
            f"\n[UNIFIED] Live market data: "
            f"{symbol}"
        )

        # ----------------------------------------------------
        # OPTION CHAIN
        # ----------------------------------------------------

        option_chain = self.get_option_chain(
            symbol=symbol
        )

        # ----------------------------------------------------
        # FUTURES
        # ----------------------------------------------------

        futures = self.get_futures(
            symbol=symbol
        )

        # ----------------------------------------------------
        # UNDERLYING VALUE
        # ----------------------------------------------------

        underlying_value = None

        if (
            option_chain is not None
            and not option_chain.empty
            and "underlying_value" in option_chain.columns
        ):

            values = (
                pd.to_numeric(
                    option_chain["underlying_value"],
                    errors="coerce"
                )
                .dropna()
            )

            if not values.empty:
                underlying_value = float(
                    values.iloc[0]
                )

        elif (
            futures is not None
            and not futures.empty
            and "underlying_value" in futures.columns
        ):

            values = (
                pd.to_numeric(
                    futures["underlying_value"],
                    errors="coerce"
                )
                .dropna()
            )

            if not values.empty:
                underlying_value = float(
                    values.iloc[0]
                )

        return {
            "timestamp": datetime.now(),
            "symbol": symbol,
            "underlying_value": underlying_value,
            "option_chain": option_chain,
            "futures": futures,
        }