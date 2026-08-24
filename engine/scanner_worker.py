from PySide6.QtCore import QThread, Signal

from engine.trade_engine import TradeEngine
from engine.option_chain import OptionChain


class ScannerWorker(QThread):

    # ============================================================
    # SIGNALS
    # ============================================================

    scan_completed = Signal(dict)
    error = Signal(str)

    started_scan = Signal()
    finished_scan = Signal()

    # ============================================================
    # INIT
    # ============================================================

    def __init__(
        self,
        selected_index="NIFTY 50",
        expiry=None,
        parent=None
    ):
        super().__init__(parent)

        self.selected_index = (
            selected_index
            or "NIFTY 50"
        )

        self.expiry = expiry

        self.trade = TradeEngine()

        self._stopped = False

    # ============================================================
    # SET INDEX
    # ============================================================

    def set_index(self, selected_index):

        if not selected_index:
            return

        self.selected_index = (
            str(selected_index).strip()
        )

    # ============================================================
    # SET EXPIRY
    # ============================================================

    def set_expiry(self, expiry):

        if expiry:
            self.expiry = str(expiry).strip()

    # ============================================================
    # RESOLVE EXPIRY
    # ============================================================

    def resolve_expiry(self):

        # --------------------------------------------------------
        # If UI already supplied an expiry, use it.
        # --------------------------------------------------------

        if self.expiry:
            return self.expiry

        try:

            option_chain = OptionChain()

            # ----------------------------------------------------
            # Try generic index-aware expiry method first.
            # ----------------------------------------------------

            generic_method = getattr(
                option_chain,
                "get_current_expiry_for_symbol",
                None
            )

            if callable(generic_method):

                expiry = generic_method(
                    self.selected_index
                )

                if expiry:

                    self.expiry = str(
                        expiry
                    )

                    return self.expiry

            # ----------------------------------------------------
            # Try get_current_expiry(symbol)
            # ----------------------------------------------------

            current_method = getattr(
                option_chain,
                "get_current_expiry",
                None
            )

            if callable(current_method):

                try:

                    expiry = current_method(
                        self.selected_index
                    )

                    if expiry:

                        self.expiry = str(
                            expiry
                        )

                        return self.expiry

                except TypeError:

                    # ------------------------------------------------
                    # Current implementation only supports NIFTY.
                    # Fall back to get_current_expiry().
                    # ------------------------------------------------

                    pass

            # ----------------------------------------------------
            # Final fallback.
            #
            # Current OptionChain supports NIFTY directly.
            # ----------------------------------------------------

            expiry = option_chain.get_current_expiry()

            if expiry:

                self.expiry = str(
                    expiry
                )

                return self.expiry

            return None

        except Exception as e:

            print(
                "ScannerWorker expiry error:",
                e
            )

            return None

    # ============================================================
    # RUN
    # ============================================================

    def run(self):

        try:

            if self._stopped:
                return

            # ----------------------------------------------------
            # Resolve expiry
            # ----------------------------------------------------

            expiry = self.resolve_expiry()

            print(
                "========================================"
            )

            print(
                "AI SCANNER STARTED"
            )

            print(
                f"Index  : {self.selected_index}"
            )

            print(
                f"Expiry : {expiry}"
            )

            print(
                "========================================"
            )

            self.started_scan.emit()

            # ----------------------------------------------------
            # Validate expiry
            # ----------------------------------------------------

            if not expiry:

                raise RuntimeError(
                    f"Unable to determine expiry for "
                    f"{self.selected_index}."
                )

            # ----------------------------------------------------
            # Generate trades
            # ----------------------------------------------------

            result = self.trade.generate_trades(
                selected_index=self.selected_index,
                expiry=expiry
            )

            # ----------------------------------------------------
            # Normalize empty result
            # ----------------------------------------------------

            if result is None:
                result = {}

            if not isinstance(result, dict):

                raise RuntimeError(
                    "TradeEngine returned an invalid "
                    "scanner result."
                )

            # ----------------------------------------------------
            # Make sure selected index / expiry are always present.
            # This protects the UI from incomplete engine results.
            # ----------------------------------------------------

            result.setdefault(
                "selected_index",
                self.selected_index
            )

            result.setdefault(
                "expiry",
                expiry
            )

            # ----------------------------------------------------
            # SUCCESS
            # ----------------------------------------------------

            self.scan_completed.emit(
                result
            )

            print(
                "========================================"
            )

            print(
                "AI SCANNER COMPLETED"
            )

            print(
                "========================================"
            )

        except Exception as e:

            import traceback

            error_text = traceback.format_exc()

            print(
                "========================================"
            )

            print(
                "AI SCANNER ERROR"
            )

            print(
                error_text
            )

            print(
                "========================================"
            )

            self.error.emit(
                error_text
            )

        finally:

            self._stopped = True

            self.finished_scan.emit()

    # ============================================================
    # STOP
    # ============================================================

    def stop(self):

        self._stopped = True

        # --------------------------------------------------------
        # Do NOT call quit() while generate_trades() is executing.
        #
        # QThread.run() is doing the actual work. Once run()
        # returns, the thread naturally finishes.
        # --------------------------------------------------------

        if self.isRunning():

            self.wait(
                3000
            )