from datetime import date
from pathlib import Path

from data_engine.jugaad_source import JugaadSource


class MarketData:

    """
    Unified market-data interface.

    Currently:
        Jugaad-data

    Later:
        EOD2
        NseIndiaApi
        Other sources

    UI / ML code should use this class instead of directly
    importing individual data providers.
    """

    def __init__(self, output_dir=None):

        if output_dir is None:
            output_dir = (
                Path(__file__).resolve().parent.parent
                / "ml_data"
            )

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Current provider
        self.jugaad = JugaadSource(
            output_dir=self.output_dir
        )

    # ========================================================
    # INDEX HISTORY
    # ========================================================

    def get_index_history(
        self,
        symbol,
        from_date,
        to_date
    ):

        if isinstance(from_date, str):
            from_date = date.fromisoformat(from_date)

        if isinstance(to_date, str):
            to_date = date.fromisoformat(to_date)

        return self.jugaad.get_index(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date
        )

    # ========================================================
    # STOCK HISTORY
    # ========================================================

    def get_stock_history(
        self,
        symbol,
        from_date,
        to_date
    ):

        if isinstance(from_date, str):
            from_date = date.fromisoformat(from_date)

        if isinstance(to_date, str):
            to_date = date.fromisoformat(to_date)

        return self.jugaad.get_stock(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date
        )

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        df,
        filename
    ):

        return self.jugaad.save(
            df=df,
            filename=filename
        )