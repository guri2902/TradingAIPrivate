from datetime import date
from pathlib import Path

from jugaad_data.nse import (
    index_df,
    stock_df,
)


class JugaadSource:

    def __init__(self, output_dir):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )


    # ========================================================
    # INDEX
    # ========================================================

    def get_index(
        self,
        symbol,
        from_date,
        to_date
    ):

        print(
            f"\n[JUGAAD] Downloading index: {symbol}"
        )

        df = index_df(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date
        )

        print(
            f"[JUGAAD] {symbol}: {len(df)} rows"
        )

        return df


    # ========================================================
    # STOCK
    # ========================================================

    def get_stock(
        self,
        symbol,
        from_date,
        to_date
    ):

        print(
            f"\n[JUGAAD] Downloading stock: {symbol}"
        )

        df = stock_df(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date
        )

        print(
            f"[JUGAAD] {symbol}: {len(df)} rows"
        )

        return df


    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        df,
        filename
    ):

        path = self.output_dir / filename

        df.to_csv(
            path,
            index=False
        )

        print(
            f"[JUGAAD] Saved: {path}"
        )

        return path