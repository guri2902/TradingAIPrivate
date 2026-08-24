from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
)

from ui.sidebar import Sidebar
from ui.dashboard import Dashboard
from ui.ai_trade_analysis import AITradeAnalysisPage
from ui.tracking_page import TradeTrackingPage
from ui import theme


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("TradingAI Pro")

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {theme.BACKGROUND};
            }}
            """
        )

        # =========================================================
        # CENTRAL
        # =========================================================

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # =========================================================
        # SIDEBAR
        # =========================================================

        self.sidebar = Sidebar()

        # =========================================================
        # STACKED PAGES
        # =========================================================

        self.pages = QStackedWidget()

        # ---------------------------------------------------------
        # DASHBOARD
        # ---------------------------------------------------------

        self.dashboard = Dashboard()

        self.pages.addWidget(
            self.dashboard
        )

        # ---------------------------------------------------------
        # TRACKING
        # ---------------------------------------------------------

        self.tracking_page = TradeTrackingPage()

        self.pages.addWidget(
            self.tracking_page
        )

        # Step 7 - separate AI Trade Analysis page.
        self.ai_trade_analysis_page = AITradeAnalysisPage()

        self.pages.addWidget(
            self.ai_trade_analysis_page
        )

        # Page registry
        self.page_widgets = {
            "dashboard": self.dashboard,
            "tracking": self.tracking_page,
            "ai_trade_analysis": self.ai_trade_analysis_page,
        }

        # =========================================================
        # OPTIONAL SIDEBAR PAGES
        # =========================================================

        self._load_optional_page(
            "scanner",
            "ui.scanner",
            (
                "Scanner",
                "ScannerPage",
            ),
        )

        self._load_optional_page(
            "market",
            "ui.market",
            (
                "Market",
                "MarketPage",
            ),
        )

        self._load_optional_page(
            "option_chain",
            "ui.option_chain",
            (
                "OptionChain",
                "OptionChainPage",
            ),
        )

        self._load_optional_page(
            "journal",
            "ui.trade_journal",
            (
                "TradeJournal",
            ),
        )

        self._load_optional_page(
            "backtest",
            "ui.backtest",
            (
                "Backtest",
                "BacktestPage",
            ),
        )

        self._load_optional_page(
            "risk_manager",
            "ui.risk_manager",
            (
                "RiskManager",
            ),
        )

        self._load_optional_page(
            "settings",
            "ui.settings",
            (
                "Settings",
                "SettingsPage",
            ),
        )

        # =========================================================
        # MAIN LAYOUT
        # =========================================================

        layout.addWidget(
            self.sidebar
        )

        layout.addWidget(
            self.pages,
            1
        )

        # =========================================================
        # SIDEBAR NAVIGATION
        # =========================================================

        self.sidebar.page_changed.connect(
            self.change_page
        )

        # =========================================================
        # GENERATE AI TRADE
        # =========================================================

        if hasattr(
            self.sidebar,
            "generate_trade_clicked"
        ):
            self.sidebar.generate_trade_clicked.connect(
                self.dashboard.generate_trade
            )

        # =========================================================
        # STEP 7 - AI TRADE ANALYSIS
        # =========================================================

        if hasattr(
            self.dashboard,
            "ai_trade_generated"
        ):
            self.dashboard.ai_trade_generated.connect(
                self.ai_trade_analysis_page.set_result
            )

        # =========================================================
        # TRACKING SIGNAL
        # =========================================================

        if hasattr(
            self.dashboard,
            "tracking_changed"
        ):
            self.dashboard.tracking_changed.connect(
                self.update_tracking_page
            )

        # =========================================================
        # AUTO OPEN TRACKING
        # =========================================================

        if hasattr(
            self.dashboard,
            "tracking_page_requested"
        ):
            self.dashboard.tracking_page_requested.connect(
                self.open_tracking_page
            )

        # =========================================================
        # INITIAL TRACKING SYNC
        # =========================================================
        # Restore the sidebar count from the persisted dashboard tracker
        # immediately. Do not wait for the next tracking_changed signal.
        self._sync_tracking()

        # =========================================================
        # INITIAL PAGE
        # =========================================================

        self.change_page(
            "dashboard"
        )

    # =============================================================
    # OPTIONAL PAGE LOADER
    # =============================================================

    def _load_optional_page(
        self,
        page_name,
        module_name,
        class_names,
    ):

        try:

            module = __import__(
                module_name,
                fromlist=list(class_names),
            )

        except Exception as exc:

            print(
                f"Page import skipped [{page_name}]: {exc}"
            )

            return

        page_class = None

        for class_name in class_names:

            candidate = getattr(
                module,
                class_name,
                None,
            )

            if candidate is not None:

                page_class = candidate

                break

        if page_class is None:

            print(
                f"No page class found for [{page_name}]"
            )

            return

        try:

            page = page_class()

            self.pages.addWidget(
                page
            )

            self.page_widgets[
                page_name
            ] = page

        except Exception as exc:

            print(
                f"Page creation failed [{page_name}]: {exc}"
            )

    # =============================================================
    # NAVIGATION
    # =============================================================

    def change_page(
        self,
        page,
    ):

        # ---------------------------------------------------------
        # TRACKING
        # ---------------------------------------------------------

        if page in (
            "tracking",
            "tracking_trades",
        ):

            self.open_tracking_page()

            return

        # ---------------------------------------------------------
        # NORMAL PAGE
        # ---------------------------------------------------------

        target = self.page_widgets.get(
            page
        )

        # ---------------------------------------------------------
        # UNKNOWN PAGE
        # ---------------------------------------------------------

        if target is None:

            print(
                f"Unknown page requested: {page}"
            )

            self.pages.setCurrentWidget(
                self.dashboard
            )

            self._set_active(
                "dashboard"
            )

            return

        # ---------------------------------------------------------
        # SHOW PAGE
        # ---------------------------------------------------------

        self.pages.setCurrentWidget(
            target
        )

        self._set_active(
            page
        )

    # =============================================================
    # ACTIVE SIDEBAR BUTTON
    # =============================================================

    def _set_active(
        self,
        page,
    ):

        if hasattr(
            self.sidebar,
            "set_active_page",
        ):

            self.sidebar.set_active_page(
                page
            )

    # =============================================================
    # OPEN TRACKING
    # =============================================================

    def open_tracking_page(
        self,
    ):

        self.pages.setCurrentWidget(
            self.tracking_page
        )

        self._set_active(
            "tracking"
        )

        self._sync_tracking()

    # =============================================================
    # SYNC TRACKING
    # =============================================================

    def _sync_tracking(
        self,
    ):

        trades = list(
            getattr(
                self.dashboard,
                "tracked_trades",
                [],
            )
        )

        self.tracking_page.update_trades(
            trades
        )

        active_count = sum(
            1
            for trade in trades
            if str(
                trade.get(
                    "status",
                    "LIVE",
                )
            ).upper()
            not in (
                "TARGET 1 HIT",
                "TARGET 2 HIT",
                "STOP LOSS HIT",
                "DAY ENDED",
            )
        )

        self.update_tracking_count(
            active_count
        )

    # =============================================================
    # TRACKING UPDATE
    # =============================================================

    def update_tracking_page(
        self,
        trades,
    ):

        trades = list(
            trades or []
        )

        self.tracking_page.update_trades(
            trades
        )

        active_count = sum(
            1
            for trade in trades
            if str(
                trade.get(
                    "status",
                    "LIVE",
                )
            ).upper()
            not in (
                "TARGET 1 HIT",
                "TARGET 2 HIT",
                "STOP LOSS HIT",
                "DAY ENDED",
            )
        )

        self.update_tracking_count(
            active_count
        )

    # =============================================================
    # SIDEBAR COUNT
    # =============================================================

    def update_tracking_count(
        self,
        count,
    ):

        if hasattr(
            self.sidebar,
            "set_tracking_count",
        ):

            self.sidebar.set_tracking_count(
                count
            )

    # =============================================================
    # CLOSE
    # =============================================================

    def closeEvent(
        self,
        event,
    ):

        try:

            if hasattr(
                self.dashboard,
                "stop",
            ):

                self.dashboard.stop()

        except Exception as exc:

            print(
                "Dashboard shutdown error:",
                exc
            )

        try:

            worker = getattr(
                self.dashboard,
                "quote_worker",
                None,
            )

            if (
                worker is not None
                and worker.isRunning()
            ):

                worker.stop()

        except Exception as exc:

            print(
                "Quote worker shutdown error:",
                exc
            )

        super().closeEvent(
            event
        )