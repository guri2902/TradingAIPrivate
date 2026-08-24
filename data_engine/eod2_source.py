# ============================================================
# TradingAI - EOD2 DATA SOURCE
# ============================================================

from pathlib import Path
import pandas as pd


class EOD2Source:

    def __init__(self, data_dir):

        self.data_dir = Path(data_dir)

        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"EOD2 data directory not found: {self.data_dir}"
            )

        self.daily_dir = self.data_dir / "daily"

        if not self.daily_dir.exists():
            raise FileNotFoundError(
                f"EOD2 daily directory not found: {self.daily_dir}"
            )


    # ========================================================
    # STOCK
    # ========================================================

    def get_stock(
        self,
        symbol,
        from_date=None,
        to_date=None
    ):

        symbol = symbol.lower()

        file_path = self.daily_dir / f"{symbol}.csv"

        if not file_path.exists():

            raise FileNotFoundError(
                f"EOD2 stock not found: {file_path}"
            )

        print(
            f"\n[EOD2] Loading stock: {symbol.upper()}"
        )

        df = pd.read_csv(file_path)

        print(
            f"[EOD2] {symbol.upper()}: {len(df)} rows"
        )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        date_column = self._find_column(
            df,
            [
                "date",
                "Date",
                "DATE"
            ]
        )

        if date_column is None:
            raise ValueError(
                f"Could not find date column in {file_path}"
            )

        df["timestamp"] = pd.to_datetime(
            df[date_column],
            errors="coerce"
        )

        # ----------------------------------------------------
        # FILTER DATE RANGE
        # ----------------------------------------------------

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

        df = (
            df.sort_values("timestamp")
              .reset_index(drop=True)
        )

        return df


    # ========================================================
    # FIND COLUMN
    # ========================================================

    @staticmethod
    def _find_column(
        df,
        candidates
    ):

        for column in candidates:

            if column in df.columns:
                return column

        return None


    # ========================================================
    # LIST SYMBOLS
    # ========================================================

    def list_symbols(self):

        files = sorted(
            self.daily_dir.glob("*.csv")
        )

        symbols = [
            file.stem.upper()
            for file in files
        ]

        print(
            f"[EOD2] Available symbols: {len(symbols)}"
        )

        return symbols