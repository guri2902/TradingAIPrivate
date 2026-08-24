# ============================================================
# TradingAI - PROCESSED DATA STORAGE
# ============================================================

from pathlib import Path
import pandas as pd


class MarketDataStorage:

    def __init__(self, base_dir="market_data"):

        self.base_dir = Path(base_dir)

        self.processed_dir = (
            self.base_dir / "processed"
        )

        self.stocks_dir = (
            self.processed_dir / "stocks"
        )

        self.indices_dir = (
            self.processed_dir / "indices"
        )

        self.options_dir = (
            self.processed_dir / "options"
        )

        # ----------------------------------------------------
        # CREATE DIRECTORIES
        # ----------------------------------------------------

        for directory in [
            self.stocks_dir,
            self.indices_dir,
            self.options_dir,
        ]:
            directory.mkdir(
                parents=True,
                exist_ok=True
            )

    # ========================================================
    # STOCK
    # ========================================================

    def save_stock(
        self,
        df,
        symbol
    ):

        symbol = str(symbol).upper()

        path = (
            self.stocks_dir
            / f"{symbol}.parquet"
        )

        df.to_parquet(
            path,
            index=False
        )

        print(
            f"[STORAGE] Stock saved: {path}"
        )

        return path

    def load_stock(
        self,
        symbol
    ):

        symbol = str(symbol).upper()

        path = (
            self.stocks_dir
            / f"{symbol}.parquet"
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Processed stock not found: {path}"
            )

        return pd.read_parquet(path)

    # ========================================================
    # INDEX
    # ========================================================

    def save_index(
        self,
        df,
        symbol
    ):

        safe_symbol = (
            str(symbol)
            .upper()
            .replace(" ", "_")
        )

        path = (
            self.indices_dir
            / f"{safe_symbol}.parquet"
        )

        df.to_parquet(
            path,
            index=False
        )

        print(
            f"[STORAGE] Index saved: {path}"
        )

        return path

    def load_index(
        self,
        symbol
    ):

        safe_symbol = (
            str(symbol)
            .upper()
            .replace(" ", "_")
        )

        path = (
            self.indices_dir
            / f"{safe_symbol}.parquet"
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Processed index not found: {path}"
            )

        return pd.read_parquet(path)

    # ========================================================
    # OPTION CHAIN
    # ========================================================

    def save_option_chain(
        self,
        df,
        symbol="NIFTY"
    ):

        symbol = str(symbol).upper()

        path = (
            self.options_dir
            / f"{symbol}_option_chain.parquet"
        )

        df.to_parquet(
            path,
            index=False
        )

        print(
            f"[STORAGE] Option chain saved: {path}"
        )

        return path

    def load_option_chain(
        self,
        symbol="NIFTY"
    ):

        symbol = str(symbol).upper()

        path = (
            self.options_dir
            / f"{symbol}_option_chain.parquet"
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Processed option chain not found: {path}"
            )

        return pd.read_parquet(path)