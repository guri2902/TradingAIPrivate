# ============================================================
# TradingAI - MARKET WORKER
# ============================================================

from __future__ import annotations

import requests

from PySide6.QtCore import QThread, Signal

from engine.market_data import MarketData
from engine.analyzers.market_analyzer import MarketAnalyzer
from engine.analyzers.pattern_analyzer import PatternAnalyzer


# ============================================================
# API CONFIG
# ============================================================

TRADINGAI_API_URL = (
    "http://127.0.0.1:8000"
)


class MarketWorker(QThread):

    # ============================================================
    # SIGNALS
    # ============================================================

    market_updated = Signal(dict)

    chart_updated = Signal(dict)

    timeframe_changed = Signal(str)

    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        symbol="NIFTY",
    ):

        super().__init__()

        # --------------------------------------------------------
        # EXISTING COMPONENTS
        # --------------------------------------------------------

        self.market = MarketData()

        self.indicators = MarketAnalyzer()

        self.pattern_ai = PatternAnalyzer()

        # --------------------------------------------------------
        # SYMBOL
        # --------------------------------------------------------

        self.symbol = (
            str(symbol)
            .strip()
            .upper()
        )

        # --------------------------------------------------------
        # THREAD
        # --------------------------------------------------------

        self.running = True

        # --------------------------------------------------------
        # CHART
        # --------------------------------------------------------

        self.chart_interval = "5m"

        # --------------------------------------------------------
        # EXISTING ANALYSIS TIMEFRAME
        # --------------------------------------------------------

        self.analysis_interval = "5m"

        # --------------------------------------------------------
        # API
        # --------------------------------------------------------

        self.api_url = (
            TRADINGAI_API_URL
        )

        self.api_timeout = 45

    # ============================================================
    # SYMBOL
    # ============================================================

    def set_symbol(
        self,
        symbol,
    ):

        symbol = (
            str(symbol)
            .strip()
            .upper()
        )

        if not symbol:
            return

        if symbol == self.symbol:
            return

        print(
            "MarketWorker: switching symbol "
            f"{self.symbol} -> {symbol}"
        )

        self.symbol = symbol

    # ============================================================
    # CHART TIMEFRAME
    # ============================================================

    def set_chart_interval(
        self,
        interval,
    ):

        valid_intervals = [
            "1m",
            "5m",
            "15m",
            "30m",
            "1H",
            "1D",
        ]

        if interval not in valid_intervals:

            print(
                "MarketWorker: invalid timeframe:",
                interval,
            )

            return

        if interval == self.chart_interval:
            return

        print(
            f"MarketWorker: switching chart "
            f"timeframe {self.chart_interval} -> {interval}"
        )

        self.chart_interval = interval

        self.timeframe_changed.emit(
            interval
        )

    # ============================================================
    # API REQUEST
    # ============================================================

    def _fetch_tradingai_state(self):

        url = (
            f"{self.api_url}"
            f"/v1/tradingai/"
            f"{self.symbol}"
        )

        response = requests.get(
            url,
            timeout=self.api_timeout,
        )

        response.raise_for_status()

        payload = (
            response.json()
        )

        if not isinstance(
            payload,
            dict,
        ):

            raise RuntimeError(
                "TradingAI API returned "
                "an invalid response."
            )

        if not payload.get("ok"):

            raise RuntimeError(
                str(
                    payload.get(
                        "error",
                        "TradingAI API error.",
                    )
                )
            )

        data = (
            payload.get("data")
        )

        if not isinstance(
            data,
            dict,
        ):

            raise RuntimeError(
                "TradingAI API returned "
                "invalid market data."
            )

        return data

    # ============================================================
    # API → EXISTING DASHBOARD SCHEMA
    # ============================================================

    @staticmethod
    def _build_api_analysis(
        data,
        symbol,
    ):

        instrument = (
            data.get(
                "instrument"
            )
            or {}
        )

        current = (
            data.get(
                "current"
            )
            or {}
        )

        market = (
            data.get(
                "market"
            )
            or {}
        )

        technical = (
            market.get(
                "technical"
            )
            or {}
        )

        latest = (
            market.get(
                "latest"
            )
            or {}
        )

        options = (
            data.get(
                "options"
            )
            or {}
        )

        futures = (
            data.get(
                "futures"
            )
            or {}
        )

        freshness = (
            data.get(
                "freshness"
            )
            or {}
        )

        # --------------------------------------------------------
        # IMPORTANT:
        #
        # These are the exact keys expected by the existing
        # Dashboard. Do NOT make the Dashboard understand the
        # new backend structure.
        # --------------------------------------------------------

        ema20 = technical.get(
            "ema_21"
        )

        ema50 = technical.get(
            "sma_50"
        )

        ema200 = technical.get(
            "sma_200"
        )

        rsi = technical.get(
            "rsi_14"
        )

        macd = technical.get(
            "macd"
        )

        signal = technical.get(
            "macd_signal"
        )

        histogram = technical.get(
            "macd_histogram"
        )

        atr = technical.get(
            "atr_14"
        )

        volume = latest.get(
            "volume"
        )

        # --------------------------------------------------------
        # Current live price
        # --------------------------------------------------------

        price = current.get(
            "price"
        )

        # --------------------------------------------------------
        # Change %
        # --------------------------------------------------------

        change_percent = None

        if (
            latest.get("close") is not None
            and latest.get("open") is not None
        ):

            try:

                open_price = float(
                    latest["open"]
                )

                close_price = float(
                    latest["close"]
                )

                if open_price != 0:

                    change_percent = (
                        (
                            close_price
                            - open_price
                        )
                        / open_price
                    ) * 100.0

            except (
                TypeError,
                ValueError,
            ):

                change_percent = None

        # --------------------------------------------------------
        # Preserve a compatible legacy structure.
        #
        # Values which the current unified backend does not
        # produce are left as N/A instead of inventing data.
        # --------------------------------------------------------

        result = {

            "symbol":
                instrument.get(
                    "symbol",
                    symbol,
                ),

            "selected_index":
                instrument.get(
                    "display_name",
                    symbol,
                ),

            "index":
                instrument.get(
                    "display_name",
                    symbol,
                ),

            "display_name":
                instrument.get(
                    "display_name",
                    symbol,
                ),

            "price":
                price,

            "change_percent":
                change_percent,

            "change":
                change_percent,

            # ------------------------------------------------
            # Existing dashboard technical fields
            # ------------------------------------------------

            "ema20":
                ema20,

            "ema50":
                ema50,

            "ema200":
                ema200,

            "rsi":
                rsi,

            "macd":
                macd,

            "signal":
                signal,

            "histogram":
                histogram,

            # ------------------------------------------------
            # VWAP is not currently produced by the unified
            # backend, so leave it explicit rather than fake it.
            # ------------------------------------------------

            "vwap":
                technical.get(
                    "vwap"
                ),

            "atr":
                atr,

            "volume":
                volume,

            # ------------------------------------------------
            # Compatibility / status
            # ------------------------------------------------

            "trend":
                "N/A",

            "bull_probability":
                "N/A",

            "bear_probability":
                "N/A",

            "sideways_probability":
                "N/A",

            "strength":
                "N/A",

            "volatility":
                technical.get(
                    "volatility_20"
                ),

            "patterns":
                None,

            # ------------------------------------------------
            # New unified backend data
            # ------------------------------------------------

            "market":
                market,

            "options":
                options,

            "futures":
                futures,

            "freshness":
                freshness,

            "tradingai":
                data,

            "data_source":
                "tradingai_api",
        }

        return result

    # ============================================================
    # LEGACY FALLBACK
    # ============================================================

    def _run_legacy_analysis(
        self,
    ):

        analysis_candles = (
            self.market.get_nifty_candles(
                interval=self.analysis_interval
            )
        )

        if (
            analysis_candles is None
            or analysis_candles.empty
        ):

            return None

        analysis = (
            self.indicators.analyze(
                analysis_candles
            )
        )

        patterns = (
            self.pattern_ai.analyze(
                analysis_candles
            )
        )

        analysis[
            "patterns"
        ] = patterns

        analysis[
            "data_source"
        ] = "legacy_market_worker"

        return analysis

    # ============================================================
    # RUN
    # ============================================================

    def run(self):

        while (
            self.running
            and not self.isInterruptionRequested()
        ):

            try:

                # =================================================
                # EXISTING CHART PATH
                # =================================================

                chart_candles = (
                    self.market.get_nifty_candles(
                        interval=self.chart_interval
                    )
                )

                if (
                    chart_candles is not None
                    and not chart_candles.empty
                ):

                    chart_data = (
                        self._build_chart_data(
                            chart_candles
                        )
                    )

                    if chart_data[
                        "candles"
                    ]:

                        self.chart_updated.emit(
                            chart_data
                        )

                # =================================================
                # UNIFIED API
                # =================================================

                try:

                    tradingai_state = (
                        self._fetch_tradingai_state()
                    )

                    analysis = (
                        self._build_api_analysis(
                            tradingai_state,
                            self.symbol,
                        )
                    )
                    # ------------------------------------------------
                    # EXISTING MARKET ANALYZER
                    #
                    # Used only to populate the Dashboard's
                    # presentation probabilities / trend fields.
                    #
                    # The API remains the source of truth for:
                    # price, technicals, options, futures and freshness.
                    # ------------------------------------------------

                    try:

                        analysis_candles = (
                            self.market.get_nifty_candles(
                                interval=self.analysis_interval
                            )
                        )

                        if (
                            analysis_candles is not None
                            and not analysis_candles.empty
                        ):

                            legacy_analysis = (
                                self.indicators.analyze(
                                    analysis_candles
                                )
                            )

                            if isinstance(
                                legacy_analysis,
                                dict,
                            ):
                                for key in [
                                    "trend",
                                    "bull_probability",
                                    "bear_probability",
                                    "sideways_probability",
                                    "strength",
                                    "volatility",
                                    "confidence",
                                ]:

                                    if key in legacy_analysis:

                                        analysis[key] = (
                                            legacy_analysis[key]
                                        )

                                # Keep existing candle pattern display.
                                try:

                                    analysis["patterns"] = (
                                        self.pattern_ai.analyze(
                                            analysis_candles
                                        )
                                    )

                                except Exception:

                                    pass
                    except Exception as analyzer_error:

                        print(
                            "MarketAnalyzer Error:",
                            analyzer_error,
                        )

                    analysis[
                        "data_source"
                    ] = "tradingai_api"

                    self.market_updated.emit(
                        analysis
                    )

                except Exception as api_error:

                    print(
                        "MarketWorker API Error:",
                        api_error,
                    )

                    # ------------------------------------------------
                    # EXISTING FALLBACK
                    # ------------------------------------------------

                    fallback = (
                        self._run_legacy_analysis()
                    )

                    if fallback is not None:

                        self.market_updated.emit(
                            fallback
                        )

            except Exception as e:

                print(
                    "MarketWorker Error:",
                    e,
                )

            # =====================================================
            # EXISTING FREQUENCY
            # =====================================================

            self._sleep()

    # ============================================================
    # CHART DATA
    # ============================================================

    def _build_chart_data(
        self,
        candles,
    ):

        result = {

            "candles": [],

            "timestamps": [],

            "interval":
                self.chart_interval,

        }

        try:

            df = candles.copy()

            column_map = {

                str(column).lower(): column

                for column in df.columns

            }

            open_col = column_map.get(
                "open"
            )

            high_col = column_map.get(
                "high"
            )

            low_col = column_map.get(
                "low"
            )

            close_col = column_map.get(
                "close"
            )

            if not all(
                [
                    open_col,
                    high_col,
                    low_col,
                    close_col,
                ]
            ):

                print(
                    "MarketWorker: "
                    "OHLC columns not found.",
                    list(
                        df.columns
                    ),
                )

                return result

            timestamp_col = None

            possible_timestamp_names = [
                "timestamp",
                "time",
                "datetime",
                "date",
                "date_time",
            ]

            for name in (
                possible_timestamp_names
            ):

                if name in column_map:

                    timestamp_col = (
                        column_map[name]
                    )

                    break

            if timestamp_col is not None:

                timestamps = (
                    df[
                        timestamp_col
                    ].tolist()
                )

            else:

                timestamps = (
                    df.index.tolist()
                )

            candle_index = 0

            for _, row in df.iterrows():

                try:

                    open_price = float(
                        row[
                            open_col
                        ]
                    )

                    high_price = float(
                        row[
                            high_col
                        ]
                    )

                    low_price = float(
                        row[
                            low_col
                        ]
                    )

                    close_price = float(
                        row[
                            close_col
                        ]
                    )

                    values = [
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                    ]

                    if not all(
                        value == value
                        for value in values
                    ):

                        continue

                    high_price = max(
                        high_price,
                        open_price,
                        close_price,
                    )

                    low_price = min(
                        low_price,
                        open_price,
                        close_price,
                    )

                    result[
                        "candles"
                    ].append({

                        "x":
                            candle_index,

                        "open":
                            open_price,

                        "high":
                            high_price,

                        "low":
                            low_price,

                        "close":
                            close_price,

                    })

                    if candle_index < len(
                        timestamps
                    ):

                        result[
                            "timestamps"
                        ].append(
                            timestamps[
                                candle_index
                            ]
                        )

                    else:

                        result[
                            "timestamps"
                        ].append(
                            None
                        )

                    candle_index += 1

                except Exception:

                    continue

        except Exception as e:

            print(
                "Chart Data Error:",
                e,
            )

        return result

    # ============================================================
    # SLEEP
    # ============================================================

    def _sleep(self):

        for _ in range(50):

            if (
                not self.running
                or self.isInterruptionRequested()
            ):

                return

            self.msleep(
                100
            )

    # ============================================================
    # STOP
    # ============================================================

    def stop(self):

        self.running = False

        self.requestInterruption()