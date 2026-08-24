from __future__ import annotations

import requests
import urllib3
import yfinance as yf


urllib3.disable_warnings()


class MarketData:

    # ============================================================
    # YAHOO FINANCE INDEX SYMBOLS
    # ============================================================

    INDEX_SYMBOLS = {

        "NIFTY 50": "^NSEI",

        "BANK NIFTY": "^NSEBANK",

        "FINNIFTY": "^CNXFIN",

        "MIDCAP NIFTY": "^NSEMDCP50",

    }

    # ============================================================
    # INIT
    # ============================================================

    def __init__(self):

        self.session = requests.Session()

        self.session.verify = False

    # ============================================================
    # CONNECTION TEST
    # ============================================================

    def test_connection(self):

        try:

            response = self.session.get(
                "https://www.google.com",
                timeout=5
            )

            return {
                "success": True,
                "status": response.status_code
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

    # ============================================================
    # GENERIC INDEX DATA
    # ============================================================

    def get_index(
        self,
        index_name
    ):

        try:

            candles = self.get_index_candles(
                index_name=index_name,
                interval="5m"
            )

            if candles is None or candles.empty:

                return None

            if len(candles) < 2:

                return None

            last = candles.iloc[-1]

            previous = candles.iloc[-2]

            # ----------------------------------------------------
            # PRICE
            # ----------------------------------------------------

            current_price = float(
                last["Close"]
            )

            previous_price = float(
                previous["Close"]
            )

            # ----------------------------------------------------
            # MOMENTUM
            # ----------------------------------------------------

            momentum = (
                current_price
                - previous_price
            )

            # ----------------------------------------------------
            # PERCENT CHANGE
            # ----------------------------------------------------

            if previous_price != 0:

                change_percent = (
                    momentum
                    / previous_price
                    * 100
                )

            else:

                change_percent = 0

            # ----------------------------------------------------
            # VOLATILITY
            # ----------------------------------------------------

            volatility = float(
                last["High"]
                - last["Low"]
            )

            # ----------------------------------------------------
            # VOLUME
            # ----------------------------------------------------

            try:

                volume = int(
                    last.get(
                        "Volume",
                        0
                    )
                )

            except Exception:

                volume = 0

            # ----------------------------------------------------
            # TREND
            # ----------------------------------------------------

            if current_price > previous_price:

                trend = "Bullish"

            elif current_price < previous_price:

                trend = "Bearish"

            else:

                trend = "Sideways"

            # ----------------------------------------------------
            # STRENGTH
            # ----------------------------------------------------

            strength = min(
                100,
                abs(momentum) * 10
            )

            # ----------------------------------------------------
            # RESULT
            # ----------------------------------------------------

            return {

                "index": index_name,

                "symbol": self.INDEX_SYMBOLS.get(
                    index_name
                ),

                "price": round(
                    current_price,
                    2
                ),

                "open": round(
                    float(last["Open"]),
                    2
                ),

                "high": round(
                    float(last["High"]),
                    2
                ),

                "low": round(
                    float(last["Low"]),
                    2
                ),

                "previous_close": round(
                    previous_price,
                    2
                ),

                "change": round(
                    momentum,
                    2
                ),

                "change_percent": round(
                    change_percent,
                    2
                ),

                "trend": trend,

                "momentum": round(
                    momentum,
                    2
                ),

                "strength": round(
                    strength,
                    2
                ),

                "volume": volume,

                "volatility": round(
                    volatility,
                    2
                )

            }

        except Exception as e:

            print(
                f"MarketData get_index "
                f"error [{index_name}]:",
                e
            )

            return None

    # ============================================================
    # NIFTY DATA
    # ============================================================

    def get_nifty(
        self
    ):

        return self.get_index(
            "NIFTY 50"
        )

    # ============================================================
    # BANK NIFTY DATA
    # ============================================================

    def get_banknifty(
        self
    ):

        return self.get_index(
            "BANK NIFTY"
        )

    # ============================================================
    # FINNIFTY DATA
    # ============================================================

    def get_finnifty(
        self
    ):

        return self.get_index(
            "FINNIFTY"
        )

    # ============================================================
    # MIDCAP NIFTY DATA
    # ============================================================

    def get_midcapnifty(
        self
    ):

        return self.get_index(
            "MIDCAP NIFTY"
        )

    # ============================================================
    # GENERIC CANDLES
    # ============================================================

    def get_index_candles(
        self,
        index_name,
        interval="5m"
    ):

        try:

            # ----------------------------------------------------
            # NORMALIZE INDEX
            # ----------------------------------------------------

            index_aliases = {

                "NIFTY":
                    "NIFTY 50",

                "NIFTY50":
                    "NIFTY 50",

                "NIFTY 50":
                    "NIFTY 50",

                "BANKNIFTY":
                    "BANK NIFTY",

                "BANK NIFTY":
                    "BANK NIFTY",

                "FIN NIFTY":
                    "FINNIFTY",

                "FINNIFTY":
                    "FINNIFTY",

                "MIDCAPNIFTY":
                    "MIDCAP NIFTY",

                "MIDCAP NIFTY":
                    "MIDCAP NIFTY",

                "MIDCPNIFTY":
                    "MIDCAP NIFTY",

            }

            normalized_index = index_aliases.get(
                str(
                    index_name
                ).strip().upper(),
                index_name
            )

            # ----------------------------------------------------
            # FIND YAHOO SYMBOL
            # ----------------------------------------------------

            yahoo_symbol = self.INDEX_SYMBOLS.get(
                normalized_index
            )

            if not yahoo_symbol:

                raise ValueError(
                    f"Unsupported index: "
                    f"{index_name}"
                )

            # ----------------------------------------------------
            # INTERVAL NORMALIZATION
            # ----------------------------------------------------

            interval_map = {

                "1m": "1m",

                "5m": "5m",

                "15m": "15m",

                "30m": "30m",

                "1H": "60m",

                "1h": "60m",

                "60m": "60m",

                "1D": "1d",

                "1d": "1d",

            }

            yahoo_interval = interval_map.get(
                interval,
                interval
            )

            # ----------------------------------------------------
            # YAHOO PERIOD LIMITS
            # ----------------------------------------------------

            if yahoo_interval == "1m":

                period = "7d"

            elif yahoo_interval in [
                "2m",
                "5m",
                "15m",
                "30m",
                "60m",
                "90m",
            ]:

                period = "60d"

            elif yahoo_interval in [
                "1d",
                "5d",
                "1wk",
                "1mo",
                "3mo",
            ]:

                period = "1y"

            else:

                period = "1y"

            # ----------------------------------------------------
            # FETCH
            # ----------------------------------------------------

            ticker = yf.Ticker(
                yahoo_symbol
            )

            candles = ticker.history(
                period=period,
                interval=yahoo_interval,
                auto_adjust=False,
                prepost=False
            )

            # ----------------------------------------------------
            # EMPTY CHECK
            # ----------------------------------------------------

            if candles is None:

                return None

            if candles.empty:

                return None

            # ----------------------------------------------------
            # CLEAN
            # ----------------------------------------------------

            candles = candles.copy()

            candles.dropna(
                inplace=True
            )

            # ----------------------------------------------------
            # SORT
            # ----------------------------------------------------

            try:

                candles.sort_index(
                    inplace=True
                )

            except Exception:

                pass

            return candles

        except Exception as e:

            print(
                f"MarketData candle error "
                f"[{index_name}]:",
                e
            )

            return None

    # ============================================================
    # NIFTY CANDLES
    # ============================================================

    def get_nifty_candles(
        self,
        interval="5m"
    ):

        return self.get_index_candles(
            "NIFTY 50",
            interval
        )

    # ============================================================
    # BANK NIFTY CANDLES
    # ============================================================

    def get_banknifty_candles(
        self,
        interval="5m"
    ):

        return self.get_index_candles(
            "BANK NIFTY",
            interval
        )

    # Alias used by TradeEngine

    def get_bank_nifty_candles(
        self,
        interval="5m"
    ):

        return self.get_banknifty_candles(
            interval
        )

    # ============================================================
    # FINNIFTY CANDLES
    # ============================================================

    def get_finnifty_candles(
        self,
        interval="5m"
    ):

        return self.get_index_candles(
            "FINNIFTY",
            interval
        )

    # Alias used by TradeEngine

    def get_fin_nifty_candles(
        self,
        interval="5m"
    ):

        return self.get_finnifty_candles(
            interval
        )

    # ============================================================
    # MIDCAP NIFTY CANDLES
    # ============================================================

    def get_midcapnifty_candles(
        self,
        interval="5m"
    ):

        return self.get_index_candles(
            "MIDCAP NIFTY",
            interval
        )

    # Alias used by TradeEngine

    def get_midcap_nifty_candles(
        self,
        interval="5m"
    ):

        return self.get_midcapnifty_candles(
            interval
        )

    # Another alias used by TradeEngine

    def get_midcpnifty_candles(
        self,
        interval="5m"
    ):

        return self.get_midcapnifty_candles(
            interval
        )