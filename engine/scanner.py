from PySide6.QtCore import QThread, Signal

from engine.trade_engine import TradeEngine
from engine.market_data import MarketData


# ============================================================
# SCANNER WORKER
# ============================================================

class ScannerWorker(QThread):

    scan_completed = Signal(dict)
    scan_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.running = True
        self.trade = TradeEngine()
        self.selected_index = "NIFTY 50"

    # --------------------------------------------------------
    # Set selected index
    # --------------------------------------------------------

    def set_index(self, index):
        self.selected_index = index

    # --------------------------------------------------------
    # Main worker loop
    # --------------------------------------------------------

    def run(self):

        while self.running:

            try:

                result = self.trade.generate_trades()

                if result is None:
                    result = {}

                # Add selected index information without
                # modifying the existing TradeEngine result.
                if isinstance(result, dict):

                    result["selected_index"] = self.selected_index

                self.scan_completed.emit(result)

            except Exception as e:

                error_message = str(e)

                print(f"Scanner error: {error_message}")

                self.scan_error.emit(error_message)

            # Refresh every 15 seconds.
            #
            # wait() is used instead of sleep() so the thread
            # can be stopped cleanly.
            for _ in range(15):

                if not self.running:
                    break

                self.msleep(1000)

    # --------------------------------------------------------
    # Stop worker
    # --------------------------------------------------------

    def stop(self):

        self.running = False

        # Wait for the thread to finish cleanly.
        if self.isRunning():
            self.wait(3000)


# ============================================================
# SCANNER
# ============================================================

class Scanner:

    SUPPORTED_INDICES = [
        "NIFTY 50",
        "BANK NIFTY",
        "FINNIFTY",
        "MIDCAP NIFTY"
    ]

    def __init__(self):

        self.market = MarketData()

        self.selected_index = "NIFTY 50"

    # ========================================================
    # INDEX
    # ========================================================

    def set_index(self, index):

        if index in self.SUPPORTED_INDICES:
            self.selected_index = index

    # ========================================================
    # SAFE SPOT FETCH
    # ========================================================

    def get_current_spot(self):

        """
        Get the latest spot price.

        Priority:
        1. MarketData direct spot methods
        2. Latest candle close

        This prevents the Scanner from treating ATM/max-pain
        as the spot price.
        """

        # ----------------------------------------------------
        # Try direct MarketData methods first
        # ----------------------------------------------------

        possible_methods = [
            "get_nifty_spot",
            "get_spot",
            "get_nifty_price",
            "get_current_price"
        ]

        for method_name in possible_methods:

            method = getattr(self.market, method_name, None)

            if callable(method):

                try:

                    value = method()

                    if value is not None:

                        value = float(value)

                        if value > 0:
                            return value

                except Exception:
                    pass

        # ----------------------------------------------------
        # Fallback: latest candle close
        # ----------------------------------------------------

        try:

            candles = self.market.get_nifty_candles()

            if candles is not None and not candles.empty:

                close = candles["Close"].iloc[-1]

                if close is not None:

                    close = float(close)

                    if close > 0:
                        return close

        except Exception as e:

            print(f"Unable to determine spot price: {e}")

        return None

    # ========================================================
    # CURRENT EXPIRY
    # ========================================================

    def get_current_expiry(self):

        """
        Try to obtain the current NIFTY expiry.

        We deliberately do not hard-code an expiry date.

        The NSE expiry currently available to the application
        should be used instead.
        """

        # ----------------------------------------------------
        # First check TradeEngine
        # ----------------------------------------------------

        trade = getattr(self, "_trade_engine", None)

        if trade is not None:

            for method_name in [
                "get_current_expiry",
                "get_nifty_expiry",
                "get_expiry"
            ]:

                method = getattr(trade, method_name, None)

                if callable(method):

                    try:

                        expiry = method()

                        if expiry:
                            return str(expiry)

                    except Exception:
                        pass

        # ----------------------------------------------------
        # Check if TradeEngine exposes option chain object
        # ----------------------------------------------------

        try:

            trade_engine = TradeEngine()
            self._trade_engine = trade_engine

            for attribute_name in [
                "option_chain",
                "options",
                "option",
                "oc"
            ]:

                option_chain = getattr(
                    trade_engine,
                    attribute_name,
                    None
                )

                if option_chain is None:
                    continue

                for method_name in [
                    "get_current_expiry",
                    "get_nifty_expiry",
                    "get_expiry"
                ]:

                    method = getattr(
                        option_chain,
                        method_name,
                        None
                    )

                    if callable(method):

                        try:

                            expiry = method()

                            if expiry:
                                return str(expiry)

                        except Exception:
                            pass

        except Exception:
            pass

        return None

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def get_market_snapshot(self):

        """
        Returns the basic information required by the
        Scanner UI.

        IMPORTANT:

        spot != ATM
        spot != max pain

        Spot comes from market data/candles.
        """

        spot = self.get_current_spot()

        expiry = self.get_current_expiry()

        return {
            "index": self.selected_index,
            "spot": spot,
            "expiry": expiry
        }

    # ========================================================
    # FULL SCAN
    # ========================================================

    def scan(self):

        from engine.analyzers.market_analyzer import MarketAnalyzer
        from engine.analyzers.multi_timeframe import MultiTimeframeAnalyzer
        from engine.analyzers.pattern_analyzer import PatternAnalyzer
        from engine.analyzers.smc_analyzer import SMCAnalyzer
        from engine.analyzers.volume_profile import VolumeProfile

        # ----------------------------------------------------
        # Get candles
        # ----------------------------------------------------

        candles = self.market.get_nifty_candles()

        if candles is None or candles.empty:

            return {
                "success": False,
                "error": "Unable to fetch NIFTY candles.",
                "snapshot": self.get_market_snapshot()
            }

        # ----------------------------------------------------
        # Technical analysis
        # ----------------------------------------------------

        market = MarketAnalyzer().analyze(candles)

        mtf = MultiTimeframeAnalyzer().analyze()

        patterns = PatternAnalyzer().analyze(candles)

        smc = SMCAnalyzer().analyze(candles)

        vp = VolumeProfile().analyze(candles)

        # ----------------------------------------------------
        # Snapshot
        # ----------------------------------------------------

        snapshot = self.get_market_snapshot()

        # ----------------------------------------------------
        # Return complete scanner result
        # ----------------------------------------------------

        return {

            "success": True,

            "selected_index": self.selected_index,

            "snapshot": snapshot,

            "spot": snapshot.get("spot"),

            "expiry": snapshot.get("expiry"),

            "market": market,

            "multi_timeframe": mtf,

            "patterns": patterns,

            "smc": smc,

            "volume_profile": vp

        }

    # ========================================================
    # SAFE SCAN
    # ========================================================

    def safe_scan(self):

        try:

            return self.scan()

        except Exception as e:

            print(f"Scanner failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "selected_index": self.selected_index,
                "snapshot": self.get_market_snapshot()
            }