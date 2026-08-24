# ============================================================
# TradingAI - REAL-TIME DATA ORCHESTRATOR
# ============================================================

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from data_engine.instrument_registry import InstrumentRegistry
from data_engine.nse_index_history import NseIndexHistory
from data_engine.nse_futures_history import NseFuturesHistory
from data_engine.nse_option_chain import NseOptionChain
from data_engine.feature_engineering import FeatureEngineering
from data_engine.unified_data import UnifiedMarketData


class RealtimeDataOrchestrator:

    def __init__(
        self,
        market_data_root="market_data",
    ):

        self.market_data_root = (
            market_data_root
        )

        self.registry = (
            InstrumentRegistry()
        )

        self.index_source = (
            NseIndexHistory()
        )

        self.futures_source = (
            NseFuturesHistory()
        )

        self.options_source = (
            NseOptionChain()
        )

        self.unified = (
            UnifiedMarketData()
        )

        self.features = (
            FeatureEngineering()
        )

    # ========================================================
    # CLEAN VALUE
    # ========================================================

    @staticmethod
    def _clean_value(
        value,
    ):

        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except Exception:
            pass

        if isinstance(
            value,
            (
                pd.Timestamp,
                datetime,
            ),
        ):
            return value.isoformat()

        if hasattr(
            value,
            "item",
        ):

            try:
                return value.item()
            except Exception:
                pass

        return value

    # ========================================================
    # CLEAN DICT
    # ========================================================

    @classmethod
    def _clean_dict(
        cls,
        data: dict,
    ):

        return {
            key: cls._clean_value(value)
            for key, value in data.items()
        }

    # ========================================================
    # CURRENT OPTIONS
    # ========================================================

    def fetch_live_options(
        self,
        symbol: str,
    ) -> dict[str, Any]:

        symbol = symbol.upper()

        data = (
            self.options_source.get_raw(
                symbol=symbol
            )
        )

        normalized = (
            self.options_source.normalize(
                data,
                symbol=symbol,
            )
        )

        if (
            normalized is None
            or normalized.empty
        ):

            raise RuntimeError(
                f"No live option chain "
                f"returned for {symbol}."
            )

        expiry = None

        if "expiry" in normalized.columns:

            expiry_values = (
                normalized["expiry"]
                .dropna()
                .sort_values()
                .unique()
            )

            if len(expiry_values):

                expiry = pd.Timestamp(
                    expiry_values[0]
                )

        # Current underlying
        underlying = None

        if "underlying_value" in (
            normalized.columns
        ):

            values = pd.to_numeric(
                normalized[
                    "underlying_value"
                ],
                errors="coerce",
            ).dropna()

            if not values.empty:

                underlying = float(
                    values.iloc[-1]
                )

        return {
            "available": True,
            "rows": int(
                len(normalized)
            ),
            "timestamp":
                pd.Timestamp.now().isoformat(),
            "symbol":
                symbol,
            "underlying":
                underlying,
            "expiry":
                (
                    expiry.isoformat()
                    if expiry is not None
                    else None
                ),
            "source": "nse",
        }

    # ========================================================
    # FUTURES
    # ========================================================

    def fetch_live_futures(
        self,
        symbol: str,
        expiry=None,
    ) -> dict[str, Any]:

        symbol = symbol.upper()

        if expiry is None:

            raise RuntimeError(
                "A futures expiry is required."
            )

        df = (
            self.futures_source.get_history(
                symbol=symbol,
                from_date=date(
                    2026,
                    1,
                    1,
                ),
                to_date=datetime.now().date(),
                expiry=pd.Timestamp(
                    expiry
                ),
            )
        )

        if df.empty:

            raise RuntimeError(
                f"No futures data for {symbol}."
            )

        latest = (
            df.sort_values(
                "timestamp"
            )
            .iloc[-1]
            .to_dict()
        )

        return {
            "available": True,
            "rows": int(
                len(df)
            ),
            "timestamp":
                self._clean_value(
                    latest.get(
                        "timestamp"
                    )
                ),
            "symbol":
                symbol,
            "expiry":
                self._clean_value(
                    latest.get(
                        "expiry"
                    )
                ),
            "latest":
                self._clean_dict(
                    latest
                ),
            "source":
                "jugaad-data",
        }

    # ========================================================
    # HISTORICAL MARKET
    # ========================================================

    def fetch_market_history(
        self,
        symbol: str,
    ) -> dict[str, Any]:

        symbol = symbol.upper()

        config = (
            self.registry.get(
                symbol
            )
        )

        if (
            config.asset_type.upper()
            == "INDEX"
        ):

            df = (
                self.index_source.get_history(
                    symbol=symbol,
                    from_date=date(
                        2020,
                        1,
                        1,
                    ),
                    to_date=datetime.now().date(),
                )
            )

            source = "nse"

        else:

            df = (
                self.unified.get_stock_history(
                    symbol=config.market_symbol,
                    source=config.market_source,
                )
            )

            source = config.market_source

        if df is None or df.empty:

            raise RuntimeError(
                f"No market history for {symbol}."
            )

        df = df.copy()

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

        df = (
            df
            .dropna(
                subset=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                ]
            )
            .sort_values(
                "timestamp"
            )
            .reset_index(
                drop=True
            )
        )

        latest = (
            df.iloc[-1]
            .to_dict()
        )

        latest_timestamp = pd.Timestamp(
            latest["timestamp"]
        )

        age_hours = (
            (
                pd.Timestamp.now()
                - latest_timestamp
            )
            / pd.Timedelta(
                hours=1
            )
        )

        features = (
            self.features.build_features(
                df
            )
        )
        # --------------------------------------------------------
        # Dashboard-compatible EMA values
        # --------------------------------------------------------

        df["ema_20"] = (
            df["close"]
            .ewm(
                span=20,
                adjust=False,
                min_periods=20,
            )
            .mean()
        )

        df["ema_50"] = (
            df["close"]
            .ewm(
                span=50,
                adjust=False,
                min_periods=50,
            )
            .mean()
        )

        df["ema_200"] = (
            df["close"]
            .ewm(
                span=200,
                adjust=False,
                min_periods=200,
            )
            .mean()
        )

        latest_market = (
            df.iloc[-1]
        )

        latest_features = (
            features.iloc[-1].to_dict()
        )

        latest_features[
            "ema_20"
        ] = latest_market.get(
            "ema_20"
        )

        latest_features[
            "ema_50"
        ] = latest_market.get(
            "ema_50"
        )

        latest_features[
            "ema_200"
        ] = latest_market.get(
            "ema_200"
        )

        latest_features = (
            features.iloc[-1]
            .to_dict()
        )

        return {
            "available": True,
            "rows": int(
                len(df)
            ),
            "source":
                source,
            "latest_timestamp":
                latest_timestamp.isoformat(),
            "age_hours":
                float(age_hours),
            "is_fresh":
                bool(age_hours <= 24),
            "latest":
                self._clean_dict(
                    latest
                ),
            "technical":
                self._clean_dict(
                    latest_features
                ),
            "history":
                df,
        }

    # ========================================================
    # BUILD REAL-TIME STATE
    # ========================================================

    def build_state(
        self,
        symbol="NIFTY",
    ) -> dict[str, Any]:

        generated_at = (
            pd.Timestamp.now()
        )

        symbol = symbol.upper()

        config = (
            self.registry.get(
                symbol
            )
        )

        # ----------------------------------------------------
        # MARKET HISTORY / TECHNICAL
        # ----------------------------------------------------

        market = (
            self.fetch_market_history(
                symbol
            )
        )

        # ----------------------------------------------------
        # OPTIONS
        # ----------------------------------------------------

        options = None

        try:

            options = (
                self.fetch_live_options(
                    config.option_underlying
                )
            )

        except Exception as exc:

            options = {
                "available": False,
                "reason":
                    "LIVE_OPTION_ERROR",
                "error":
                    str(exc),
            }

        # ----------------------------------------------------
        # FUTURES
        # ----------------------------------------------------

        futures = None

        try:

            expiry = (
                options.get(
                    "expiry"
                )
                if options
                else None
            )

            if expiry is not None:

                futures = (
                    self.fetch_live_futures(
                        config.futures_underlying,
                        expiry=expiry,
                    )
                )

            else:

                futures = {
                    "available": False,
                    "reason":
                        "NO_CURRENT_EXPIRY",
                }

        except Exception as exc:

            futures = {
                "available": False,
                "reason":
                    "LIVE_FUTURES_ERROR",
                "error":
                    str(exc),
            }

        # ----------------------------------------------------
        # CURRENT SPOT
        #
        # Options provide a more current underlying value
        # when the historical index endpoint is stale.
        # ----------------------------------------------------

        current_price = (
            market[
                "latest"
            ].get(
                "close"
            )
        )

        price_source = (
            "historical_market"
        )

        if (
            options
            and options.get(
                "available"
            )
            and options.get(
                "underlying"
            ) is not None
        ):

            current_price = (
                options[
                    "underlying"
                ]
            )

            price_source = (
                "live_option_chain"
            )

        # ----------------------------------------------------
        # DATA FRESHNESS
        # ----------------------------------------------------

        freshness = {

            "generated_at":
                generated_at.isoformat(),

            "market_timestamp":
                market.get(
                    "latest_timestamp"
                ),

            "market_age_hours":
                market.get(
                    "age_hours"
                ),

            "market_is_fresh":
                market.get(
                    "is_fresh"
                ),

            "options_live":
                bool(
                    options
                    and options.get(
                        "available"
                    )
                ),

            "futures_live":
                bool(
                    futures
                    and futures.get(
                        "available"
                    )
                ),

            "current_price_source":
                price_source,
        }

        # ----------------------------------------------------
        # FINAL STATE
        # ----------------------------------------------------

        return {

            "generated_at":
                generated_at.isoformat(),

            "instrument": {

                "symbol":
                    config.symbol,

                "display_name":
                    config.display_name,

                "asset_type":
                    config.asset_type,

                "segment":
                    config.segment,

            },

            "current": {

                "price":
                    self._clean_value(
                        current_price
                    ),

                "price_source":
                    price_source,
            },

            "market":
                {
                    key: value
                    for key, value
                    in market.items()
                    if key != "history"
                },

            "options":
                {
                    key: value
                    for key, value
                    in (
                        options or {}
                    ).items()
                    if key != "data"
                },

            "futures":
                futures or {
                    "available": False,
                },

            "freshness":
                freshness,
        }


def create_realtime_state(
    symbol="NIFTY",
):

    orchestrator = (
        RealtimeDataOrchestrator()
    )

    return (
        orchestrator.build_state(
            symbol
        )
    )


if __name__ == "__main__":

    state = create_realtime_state(
        "NIFTY"
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "TradingAI - REAL-TIME STATE"
    )

    print(
        "=" * 70
    )

    print(
        "Instrument:",
        state[
            "instrument"
        ]
    )

    print(
        "\nCurrent:"
    )

    print(
        state[
            "current"
        ]
    )

    print(
        "\nMarket:"
    )

    print(
        state[
            "market"
        ]
    )

    print(
        "\nOptions:"
    )

    print(
        state[
            "options"
        ]
    )

    print(
        "\nFutures:"
    )

    print(
        state[
            "futures"
        ]
    )

    print(
        "\nFreshness:"
    )

    print(
        state[
            "freshness"
        ]
    )