# ============================================================
# TradingAI - INSTRUMENT REGISTRY
# ============================================================

from dataclasses import dataclass
from typing import Dict


# ============================================================
# INSTRUMENT CONFIG
# ============================================================

@dataclass(frozen=True)
class InstrumentConfig:

    symbol: str

    display_name: str

    # Market / OHLC source symbol
    market_symbol: str

    # Data source used to load market history
    market_source: str

    # Derivative mappings
    option_underlying: str
    futures_underlying: str

    # Classification
    segment: str
    asset_type: str


# ============================================================
# REGISTRY
# ============================================================

class InstrumentRegistry:

    def __init__(self):

        self._instruments: Dict[
            str,
            InstrumentConfig
        ] = {

            # ------------------------------------------------
            # INDEX
            # ------------------------------------------------

            "NIFTY": InstrumentConfig(
                symbol="NIFTY",
                display_name="NIFTY 50",
                market_symbol="NIFTY",
                market_source="nse",
                option_underlying="NIFTY",
                futures_underlying="NIFTY",
                segment="INDEX",
                asset_type="INDEX",
            ),

            "BANKNIFTY": InstrumentConfig(
                symbol="BANKNIFTY",
                display_name="NIFTY BANK",
                market_symbol="BANKNIFTY",
                market_source="nse",
                option_underlying="BANKNIFTY",
                futures_underlying="BANKNIFTY",
                segment="INDEX",
                asset_type="INDEX",
            ),

            # ------------------------------------------------
            # EQUITIES
            # ------------------------------------------------

            "RELIANCE": InstrumentConfig(
                symbol="RELIANCE",
                display_name="RELIANCE",
                market_symbol="RELIANCE",
                market_source="eod2",
                option_underlying="RELIANCE",
                futures_underlying="RELIANCE",
                segment="EQUITY",
                asset_type="STOCK",
            ),

            "TCS": InstrumentConfig(
                symbol="TCS",
                display_name="TCS",
                market_symbol="TCS",
                market_source="eod2",
                option_underlying="TCS",
                futures_underlying="TCS",
                segment="EQUITY",
                asset_type="STOCK",
            ),

            "INFY": InstrumentConfig(
                symbol="INFY",
                display_name="INFOSYS",
                market_symbol="INFY",
                market_source="eod2",
                option_underlying="INFY",
                futures_underlying="INFY",
                segment="EQUITY",
                asset_type="STOCK",
            ),

            "HDFCBANK": InstrumentConfig(
                symbol="HDFCBANK",
                display_name="HDFC BANK",
                market_symbol="HDFCBANK",
                market_source="eod2",
                option_underlying="HDFCBANK",
                futures_underlying="HDFCBANK",
                segment="EQUITY",
                asset_type="STOCK",
            ),
        }

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        symbol: str,
    ) -> InstrumentConfig:

        if not symbol:

            raise ValueError(
                "Instrument symbol is required."
            )

        normalized = (
            str(symbol)
            .strip()
            .upper()
        )

        if normalized not in self._instruments:

            raise KeyError(
                f"Unsupported instrument: "
                f"{normalized}"
            )

        return self._instruments[
            normalized
        ]

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        symbol: str,
    ) -> bool:

        if not symbol:

            return False

        normalized = (
            str(symbol)
            .strip()
            .upper()
        )

        return normalized in (
            self._instruments
        )

    # ========================================================
    # ALL
    # ========================================================

    def all(
        self,
    ):

        return dict(
            self._instruments
        )

    # ========================================================
    # SYMBOLS
    # ========================================================

    def symbols(
        self,
    ):

        return list(
            self._instruments.keys()
        )

    # ========================================================
    # REGISTER
    # ========================================================

    def register(
        self,
        config: InstrumentConfig,
    ):

        if not isinstance(
            config,
            InstrumentConfig,
        ):

            raise TypeError(
                "config must be an InstrumentConfig."
            )

        symbol = (
            config.symbol
            .strip()
            .upper()
        )

        if not symbol:

            raise ValueError(
                "Instrument symbol cannot be empty."
            )

        if symbol in self._instruments:

            raise ValueError(
                f"Instrument already registered: "
                f"{symbol}"
            )

        self._instruments[
            symbol
        ] = config

    # ========================================================
    # REMOVE
    # ========================================================

    def remove(
        self,
        symbol: str,
    ):

        normalized = (
            str(symbol)
            .strip()
            .upper()
        )

        if normalized not in self._instruments:

            raise KeyError(
                f"Instrument not registered: "
                f"{normalized}"
            )

        del self._instruments[
            normalized
        ]

    # ========================================================
    # MARKET SOURCE
    # ========================================================

    def get_market_source(
        self,
        symbol: str,
    ) -> str:

        config = self.get(
            symbol
        )

        return config.market_source

    # ========================================================
    # MARKET SYMBOL
    # ========================================================

    def get_market_symbol(
        self,
        symbol: str,
    ) -> str:

        config = self.get(
            symbol
        )

        return config.market_symbol

    # ========================================================
    # OPTION UNDERLYING
    # ========================================================

    def get_option_underlying(
        self,
        symbol: str,
    ) -> str:

        config = self.get(
            symbol
        )

        return config.option_underlying

    # ========================================================
    # FUTURES UNDERLYING
    # ========================================================

    def get_futures_underlying(
        self,
        symbol: str,
    ) -> str:

        config = self.get(
            symbol
        )

        return config.futures_underlying

    # ========================================================
    # RELATIONSHIP VALIDATION
    # ========================================================

    def validate_relationship(
        self,
        market_symbol: str,
        option_underlying: str,
        futures_underlying: str,
    ) -> bool:

        config = self.get(
            market_symbol
        )

        expected_option = (
            config.option_underlying
            .strip()
            .upper()
        )

        expected_futures = (
            config.futures_underlying
            .strip()
            .upper()
        )

        actual_option = (
            str(option_underlying)
            .strip()
            .upper()
        )

        actual_futures = (
            str(futures_underlying)
            .strip()
            .upper()
        )

        if (
            expected_option
            != actual_option
        ):

            raise ValueError(
                f"Option underlying mismatch "
                f"for {config.symbol}: "
                f"expected {expected_option}, "
                f"got {actual_option}"
            )

        if (
            expected_futures
            != actual_futures
        ):

            raise ValueError(
                f"Futures underlying mismatch "
                f"for {config.symbol}: "
                f"expected {expected_futures}, "
                f"got {actual_futures}"
            )

        return True