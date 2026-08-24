# ============================================================
# TradingAI - UNIFIED TRADING AI ENGINE
# ============================================================

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.feature_engineering import FeatureEngineering
from data_engine.combined_ai_score import CombinedAIScore
from data_engine.market_context import MarketContext
from data_engine.instrument_registry import InstrumentRegistry
from data_engine.nse_index_history import NseIndexHistory


class TradingAIEngine:

    def __init__(
        self,
        model_dir="market_data/models",
        default_source=None,
    ):

        # ----------------------------------------------------
        # default_source is only a fallback.
        #
        # InstrumentRegistry remains the authoritative source
        # routing mechanism.
        # ----------------------------------------------------

        self.default_source = (
            default_source
        )

        # ----------------------------------------------------
        # Instrument registry
        # ----------------------------------------------------

        self.registry = (
            InstrumentRegistry()
        )

        # ----------------------------------------------------
        # Existing unified market data layer
        # Used primarily for equity / EOD history.
        # ----------------------------------------------------

        self.unified = (
            UnifiedMarketData()
        )

        # ----------------------------------------------------
        # NSE index history adapter
        # Used for NIFTY / BANKNIFTY style indexes.
        # ----------------------------------------------------

        self.nse_index_history = (
            NseIndexHistory()
        )

        # ----------------------------------------------------
        # Technical / quant feature engine
        # ----------------------------------------------------

        self.features = (
            FeatureEngineering()
        )

        # ----------------------------------------------------
        # Combined ML engine
        # ----------------------------------------------------

        self.combined = (
            CombinedAIScore(
                model_dir=model_dir
            )
        )

        self.combined.load()

        # ----------------------------------------------------
        # Options + futures context
        # ----------------------------------------------------

        self.context = (
            MarketContext()
        )

    # ========================================================
    # RESOLVE INSTRUMENT
    # ========================================================

    def resolve_instrument(
        self,
        symbol: str,
    ):

        return self.registry.get(
            symbol
        )

    # ========================================================
    # RESOLVE MARKET SOURCE
    # ========================================================

    def resolve_market_source(
        self,
        symbol: str,
        source: Optional[str] = None,
    ) -> str:

        config = (
            self.resolve_instrument(
                symbol
            )
        )

        # ----------------------------------------------------
        # Explicit override wins.
        # ----------------------------------------------------

        if source:

            return (
                str(source)
                .strip()
                .lower()
            )

        # ----------------------------------------------------
        # Registry is the normal authority.
        # ----------------------------------------------------

        if config.market_source:

            return (
                config.market_source
                .strip()
                .lower()
            )

        # ----------------------------------------------------
        # Optional fallback.
        # ----------------------------------------------------

        if self.default_source:

            return (
                str(self.default_source)
                .strip()
                .lower()
            )

        raise RuntimeError(
            f"No market source configured "
            f"for {config.symbol}."
        )

    # ========================================================
    # DATE RANGE
    # ========================================================

    @staticmethod
    def _default_history_range():

        return (
            date(
                2020,
                1,
                1,
            ),
            datetime.now().date(),
        )

    # ========================================================
    # MARKET DATA - INDEX
    # ========================================================

    def _load_index_market_data(
        self,
        config,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:

        (
            default_from,
            default_to,
        ) = (
            self._default_history_range()
        )

        from_date = (
            from_date
            or default_from
        )

        to_date = (
            to_date
            or default_to
        )

        if from_date > to_date:

            raise ValueError(
                "from_date cannot be after "
                "to_date."
            )

        print(
            f"\n[TRADINGAI-INDEX] "
            f"Loading {config.symbol}"
        )

        df = (
            self.nse_index_history.get_history(
                symbol=config.symbol,
                from_date=from_date,
                to_date=to_date,
            )
        )

        if (
            df is None
            or df.empty
        ):

            raise RuntimeError(
                f"No NSE index data returned "
                f"for {config.symbol}."
            )

        return df.copy()

    # ========================================================
    # MARKET DATA - STOCK
    # ========================================================

    def _load_stock_market_data(
        self,
        config,
        source: str,
    ) -> pd.DataFrame:

        print(
            f"\n[TRADINGAI-STOCK] "
            f"Loading {config.symbol} "
            f"from {source}"
        )

        df = (
            self.unified.get_stock_history(
                symbol=config.market_symbol,
                source=source,
            )
        )

        if (
            df is None
            or df.empty
        ):

            raise RuntimeError(
                f"No market data returned "
                f"for {config.symbol} "
                f"from source={source}."
            )

        return df.copy()

    # ========================================================
    # MARKET DATA
    # ========================================================

    def load_market_data(
        self,
        symbol: str,
        source: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:

        config = (
            self.resolve_instrument(
                symbol
            )
        )

        actual_source = (
            self.resolve_market_source(
                symbol=config.symbol,
                source=source,
            )
        )

        # ----------------------------------------------------
        # INDEX ROUTING
        #
        # NIFTY / BANKNIFTY do NOT go through
        # UnifiedMarketData.get_stock_history().
        # ----------------------------------------------------

        if (
            config.asset_type.upper()
            == "INDEX"
        ):

            allowed_sources = {
                "nse",
                "nseindiaapi",
                "jugaad",
            }

            if (
                actual_source
                not in allowed_sources
            ):

                raise ValueError(
                    f"Invalid index market source "
                    f"for {config.symbol}: "
                    f"{actual_source}. "
                    f"Expected one of: "
                    f"{sorted(allowed_sources)}"
                )

            df = (
                self._load_index_market_data(
                    config=config,
                    from_date=from_date,
                    to_date=to_date,
                )
            )

        # ----------------------------------------------------
        # STOCK ROUTING
        # ----------------------------------------------------

        else:

            df = (
                self._load_stock_market_data(
                    config=config,
                    source=actual_source,
                )
            )

        # ----------------------------------------------------
        # Common final validation
        # ----------------------------------------------------

        if (
            df is None
            or df.empty
        ):

            raise RuntimeError(
                f"Market data is empty "
                f"for {config.symbol}."
            )

        # ----------------------------------------------------
        # Normalize column names
        # ----------------------------------------------------

        df.columns = [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            for column in df.columns
        ]

        required_ohlc = [
            "open",
            "high",
            "low",
            "close",
        ]

        missing_ohlc = [
            column
            for column in required_ohlc
            if column not in df.columns
        ]

        if missing_ohlc:

            raise RuntimeError(
                f"Market data for {config.symbol} "
                f"is missing OHLC columns: "
                f"{missing_ohlc}. "
                f"Available columns: "
                f"{df.columns.tolist()}"
            )

        # ----------------------------------------------------
        # Ensure symbol exists
        # ----------------------------------------------------

        if "symbol" not in df.columns:

            df["symbol"] = (
                config.symbol
            )

        # ----------------------------------------------------
        # Normalize timestamp
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            df["timestamp"] = (
                pd.to_datetime(
                    df["timestamp"],
                    errors="coerce",
                )
            )

        # ----------------------------------------------------
        # Numeric OHLC
        # ----------------------------------------------------

        for column in required_ohlc:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        if "volume" in df.columns:

            df["volume"] = pd.to_numeric(
                df["volume"],
                errors="coerce",
            )

        # ----------------------------------------------------
        # Remove invalid OHLC rows
        # ----------------------------------------------------

        df = df.dropna(
            subset=required_ohlc
        )

        # ----------------------------------------------------
        # Sort chronologically if timestamp exists
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            df = (
                df
                .dropna(
                    subset=["timestamp"]
                )
                .sort_values(
                    "timestamp"
                )
                .drop_duplicates(
                    subset=["timestamp"],
                    keep="last",
                )
                .reset_index(
                    drop=True
                )
            )

        if df.empty:

            raise RuntimeError(
                f"No valid OHLC rows remain "
                f"for {config.symbol}."
            )

        print(
            f"[TRADINGAI] "
            f"{config.symbol}: "
            f"{len(df)} valid market rows"
        )

        return df.copy()

    # ========================================================
    # FEATURES
    # ========================================================

    def build_features(
        self,
        market_df: pd.DataFrame,
    ) -> pd.DataFrame:

        if (
            market_df is None
            or market_df.empty
        ):

            raise ValueError(
                "Market dataframe is empty."
            )

        feature_df = (
            self.features.build_features(
                market_df.copy()
            )
        )

        if (
            feature_df is None
            or feature_df.empty
        ):

            raise RuntimeError(
                "Feature engineering returned "
                "an empty dataframe."
            )

        return feature_df

    # ========================================================
    # ML
    # ========================================================

    def calculate_ml(
        self,
        feature_df: pd.DataFrame,
        asset_type: str = "STOCK",
    ) -> pd.DataFrame:

        if feature_df is None or feature_df.empty:
            raise ValueError(
                "Feature dataframe is empty."
            )

        # Do not force equity-trained models onto indexes.
        # The current index models are experimental and have not
        # demonstrated sufficient out-of-sample performance to
        # control the production signal. Keep the state explicit.
        if str(asset_type).upper() == "INDEX":
            return pd.DataFrame([
                {
                    "ml_available": False,
                    "ml_status": "INDEX_ML_PARKED",
                    "signal": "UNAVAILABLE",
                    "strength": "NONE",
                    "trade_suitability": "CAUTION",
                }
            ])

        result = self.combined.predict(
            feature_df
        )

        if result is None or result.empty:
            raise RuntimeError(
                "Combined AI score returned no result."
            )

        return result.copy()

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
        data,
    ):

        if not isinstance(
            data,
            dict,
        ):

            return data

        return {
            key: cls._clean_value(
                value
            )
            for key, value in data.items()
        }

    # ========================================================
    # TECHNICAL EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_technical(
        row,
    ):

        candidates = [

            "return",
            "log_return",
            "price_change",

            "rsi",
            "rsi_14",

            "macd",
            "macd_signal",
            "macd_hist",

            "atr",
            "atr_percent",

            "volatility",
            "volatility_10",
            "volatility_20",

            "volume_ratio",
            "volume_sma",

            "momentum_5",
            "momentum_10",
            "momentum_20",

            "roc_5",
            "roc_10",
            "roc_20",

            "sma_5",
            "sma_10",
            "sma_20",
            "sma_50",
            "sma_200",

            "ema_9",
            "ema_21",
            "ema_20",
            "ema_50",
            "ema_200",

            "vwap",

            "bb_upper",
            "bb_middle",
            "bb_lower",
            "bb_width",
            "bb_position",

            "range",
            "range_pct",

            "body",
            "body_pct",

            "upper_wick",
            "lower_wick",

            "upper_wick_pct",
            "lower_wick_pct",
        ]

        return {
            key: row.get(
                key
            )
            for key in candidates
            if key in row
        }

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(
        self,
        symbol: str,
        source: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> dict[str, Any]:

        started_at = datetime.now()

        # ----------------------------------------------------
        # 1. Resolve instrument
        # ----------------------------------------------------

        config = (
            self.resolve_instrument(
                symbol
            )
        )

        actual_source = (
            self.resolve_market_source(
                symbol=config.symbol,
                source=source,
            )
        )

        # ----------------------------------------------------
        # 2. Derivative context
        # ----------------------------------------------------

        derivative_context = (
            self.context.build(
                config.symbol
            )
        )

        self.context.validate(
            derivative_context
        )

        # ----------------------------------------------------
        # 3. Market
        # ----------------------------------------------------

        market_df = (
            self.load_market_data(
                symbol=config.symbol,
                source=actual_source,
                from_date=from_date,
                to_date=to_date,
            )
        )

        # ----------------------------------------------------
        # 4. Technical features
        # ----------------------------------------------------

        feature_df = (
            self.build_features(
                market_df
            )
        )

        # ----------------------------------------------------
        # 5. Combined ML
        # ----------------------------------------------------

        ml_df = (
            self.calculate_ml(
                feature_df,
                asset_type=config.asset_type,
            )
        )

        # ----------------------------------------------------
        # 6. Latest market row
        # ----------------------------------------------------

        latest_market = (
            feature_df
            .tail(1)
            .iloc[0]
            .to_dict()
        )

        latest_ml = (
            ml_df
            .tail(1)
            .iloc[0]
            .to_dict()
        )

        latest_market = (
            self._clean_dict(
                latest_market
            )
        )

        latest_ml = (
            self._clean_dict(
                latest_ml
            )
        )

        # ----------------------------------------------------
        # 7. Timestamp
        # ----------------------------------------------------

        timestamp = (
            latest_market.get(
                "timestamp"
            )
        )

        if timestamp is None:

            timestamp = (
                started_at.isoformat()
            )

        # ----------------------------------------------------
        # 8. Unified result
        # ----------------------------------------------------

        result = {

            "timestamp":
                timestamp,

            "instrument": {

                "symbol":
                    config.symbol,

                "display_name":
                    config.display_name,

                "market_symbol":
                    config.market_symbol,

                "market_source":
                    config.market_source,

                "option_underlying":
                    config.option_underlying,

                "futures_underlying":
                    config.futures_underlying,

                "segment":
                    config.segment,

                "asset_type":
                    config.asset_type,
            },

            "symbol":
                config.symbol,

            "source":
                actual_source,

            # ------------------------------------------------
            # MARKET
            # ------------------------------------------------

            "market": {

                "open":
                    latest_market.get(
                        "open"
                    ),

                "high":
                    latest_market.get(
                        "high"
                    ),

                "low":
                    latest_market.get(
                        "low"
                    ),

                "close":
                    latest_market.get(
                        "close"
                    ),

                "volume":
                    latest_market.get(
                        "volume"
                    ),
            },

            # ------------------------------------------------
            # TECHNICAL / QUANT
            # ------------------------------------------------

            "technical":
                self._clean_dict(
                    self._extract_technical(
                        latest_market
                    )
                ),

            # ------------------------------------------------
            # ML
            # ------------------------------------------------

            "ml":
                latest_ml,

            # ------------------------------------------------
            # OPTIONS
            # ------------------------------------------------

            "options":
                derivative_context[
                    "options"
                ],

            # ------------------------------------------------
            # FUTURES
            # ------------------------------------------------

            "futures":
                derivative_context[
                    "futures"
                ],

            # ------------------------------------------------
            # ENGINE
            # ------------------------------------------------

            "engine": {

                "market_rows":
                    int(
                        len(
                            market_df
                        )
                    ),

                "feature_rows":
                    int(
                        len(
                            feature_df
                        )
                    ),

                "feature_columns":
                    int(
                        len(
                            feature_df.columns
                        )
                    ),

                "ml_rows":
                    int(
                        len(
                            ml_df
                        )
                    ),

                "generated_at":
                    datetime.now().isoformat(),
            },
        }

        self.validate_result(
            result
        )

        return result
    

    # ========================================================
    # VALIDATE
    # ========================================================

    @staticmethod
    def validate_result(
        result,
    ):

        if not isinstance(
            result,
            dict,
        ):

            raise ValueError(
                "TradingAI result must be "
                "a dictionary."
            )

        required = [

            "timestamp",

            "instrument",

            "symbol",

            "source",

            "market",

            "technical",

            "ml",

            "options",

            "futures",

            "engine",
        ]

        missing = [
            key
            for key in required
            if key not in result
        ]

        if missing:

            raise ValueError(
                "TradingAI result missing "
                f"sections: {missing}"
            )

        instrument = (
            result[
                "instrument"
            ]
        )

        if not instrument.get(
            "symbol"
        ):

            raise ValueError(
                "Instrument mapping is missing."
            )

        if not instrument.get(
            "market_source"
        ):

            raise ValueError(
                "Market source mapping is missing."
            )

        if result[
            "market"
        ].get(
            "close"
        ) is None:

            raise ValueError(
                "Market close is missing."
            )

        if not isinstance(
            result["ml"],
            dict,
        ):
            raise ValueError(
                "ML output must be a dictionary."
            )

        return True