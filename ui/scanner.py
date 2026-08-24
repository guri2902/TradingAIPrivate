from __future__ import annotations

import traceback

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QGridLayout,
    QSizePolicy,
)

from ui import theme

from engine.scanner_worker import ScannerWorker
from engine.option_chain import OptionChain

# ============================================================
# SCAN RESULT CACHE
# ============================================================
# Keeps the last successful scan for every instrument.
#
# IMPORTANT:
# This is module-level, so even if the Scanner QWidget is
# recreated during navigation, the scan results remain available
# as long as the application process is running.
# ============================================================

_SCAN_CACHE = {}
# ============================================================
# CLICKABLE INDEX CARD
# ============================================================

class ClickableFrame(QFrame):

    clicked = Signal()

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            self.clicked.emit()

        super().mousePressEvent(event)


# ============================================================
# GENERIC CARD
# ============================================================

class ScannerCard(QFrame):

    def __init__(
        self,
        title
    ):

        super().__init__()

        self.setObjectName(
            "ScannerCard"
        )

        self.setStyleSheet(
            f"""
            QFrame#ScannerCard {{
                background: {theme.CARD};
                border: 1px solid {theme.BORDER};
                border-radius: {theme.RADIUS}px;
            }}
            """
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            16,
            14,
            16,
            16
        )

        layout.setSpacing(
            9
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.TEXT};
                font-family: "{theme.FONT}";
                font-size: 15px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
            """
        )

        layout.addWidget(
            title_label
        )

        self.body = QVBoxLayout()

        self.body.setSpacing(
            7
        )

        layout.addLayout(
            self.body
        )


# ============================================================
# SCANNER
# ============================================================

class Scanner(QWidget):

    SUPPORTED_INDICES = (
        "NIFTY 50",
        "BANK NIFTY",
        "FINNIFTY",
        "MIDCAP NIFTY",
    )

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self):

        super().__init__()

        # ----------------------------------------------------
        # SELECTION
        # ----------------------------------------------------

        self.selected_index = "NIFTY 50"

        self.selected_expiry = None

        # ----------------------------------------------------
        # WORKER
        # ----------------------------------------------------

        self.scan_worker = None

        # ----------------------------------------------------
        # DATA
        # ----------------------------------------------------

        self.last_result = {}

        self.metrics = {}

        self.index_cards = {}

        # ----------------------------------------------------
        # OPTION CHAIN
        # ----------------------------------------------------

        self.option_chain = OptionChain()

        # ----------------------------------------------------
        # BUILD UI
        # ----------------------------------------------------

        self.build_ui()

        # ----------------------------------------------------
        # Load initial expiry
        # ----------------------------------------------------

        self.load_expiry()
        # ========================================================
        # RESTORE PREVIOUS SCAN
        # ========================================================

        self.restore_cached_result()


    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            theme.CONTENT_MARGIN,
            theme.CONTENT_MARGIN,
            theme.CONTENT_MARGIN,
            theme.CONTENT_MARGIN
        )

        root.setSpacing(
            theme.CARD_GAP
        )

        # ====================================================
        # HEADER
        # ====================================================

        header = QHBoxLayout()

        header.setSpacing(
            10
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title_box = QVBoxLayout()

        title_box.setSpacing(
            2
        )

        title = QLabel(
            "AI Scanner"
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.TEXT};
                font-family: "{theme.FONT}";
                font-size: 24px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            """
        )

        subtitle = QLabel(
            "Scan the market and identify high-probability opportunities"
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.TEXT_SECONDARY};
                font-family: "{theme.FONT}";
                font-size: 12px;
                background: transparent;
                border: none;
            }}
            """
        )

        title_box.addWidget(
            title
        )

        title_box.addWidget(
            subtitle
        )

        header.addLayout(
            title_box
        )

        header.addStretch()

        # ----------------------------------------------------
        # SELECTED INDEX
        # ----------------------------------------------------

        self.selected_label = QLabel(
            "NIFTY 50"
        )

        self.selected_label.setStyleSheet(
            f"""
            QLabel {{
                background: transparent;
                color: {theme.TEXT_SECONDARY};
                border: none;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
            """
        )

        header.addWidget(
            self.selected_label
        )

        # ----------------------------------------------------
        # EXPIRY
        # ----------------------------------------------------

        self.expiry_label = QLabel(
            "Expiry: --"
        )

        self.expiry_label.setStyleSheet(
            f"""
            QLabel {{
                background: {theme.CARD};
                color: {theme.TEXT};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
                padding: 9px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
            """
        )

        header.addWidget(
            self.expiry_label
        )

        # ----------------------------------------------------
        # SCAN BUTTON
        # ----------------------------------------------------

        self.scan_button = QPushButton(
            "✦  Scan Market"
        )

        self.scan_button.setFixedHeight(
            38
        )

        self.scan_button.clicked.connect(
            self.scan_market
        )

        self.scan_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0px 18px;
                font-size: 12px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: #3395FF;
            }}

            QPushButton:pressed {{
                background: #0878E5;
            }}

            QPushButton:disabled {{
                background: {theme.BORDER};
                color: {theme.TEXT_SECONDARY};
            }}
            """
        )

        header.addWidget(
            self.scan_button
        )

        root.addLayout(
            header
        )

        # ====================================================
        # INDEX CARDS
        # ====================================================

        index_strip = QHBoxLayout()

        index_strip.setSpacing(
            8
        )

        for name in self.SUPPORTED_INDICES:

            card = ClickableFrame()

            card.setMinimumHeight(
                78
            )

            card.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )

            # ------------------------------------------------
            # SELECTED STYLE
            # ------------------------------------------------

            if name == self.selected_index:

                card.setObjectName(
                    "PrimaryIndex"
                )

            else:

                card.setObjectName(
                    ""
                )

            card.setStyleSheet(
                f"""
                QFrame {{
                    background: {theme.CARD};
                    border: 1px solid {theme.BORDER};
                    border-radius: 8px;
                }}

                QFrame#PrimaryIndex {{
                    background: #102033;
                    border: 1px solid {theme.PRIMARY};
                }}

                QFrame:hover {{
                    border: 1px solid {theme.PRIMARY};
                }}
                """
            )

            box = QVBoxLayout(
                card
            )

            box.setContentsMargins(
                12,
                8,
                12,
                8
            )

            box.setSpacing(
                1
            )

            # ------------------------------------------------
            # NAME
            # ------------------------------------------------

            name_label = QLabel(
                name
            )

            name_label.setAttribute(
                Qt.WA_TransparentForMouseEvents,
                True
            )

            name_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {theme.TEXT_SECONDARY};
                    font-size: 11px;
                    font-weight: 600;
                    background: transparent;
                    border: none;
                }}
                """
            )

            # ------------------------------------------------
            # PRICE
            # ------------------------------------------------

            price_label = QLabel(
                "--"
            )

            price_label.setAttribute(
                Qt.WA_TransparentForMouseEvents,
                True
            )

            price_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {theme.TEXT};
                    font-size: 18px;
                    font-weight: 700;
                    background: transparent;
                    border: none;
                }}
                """
            )

            # ------------------------------------------------
            # CHANGE
            # ------------------------------------------------

            change_label = QLabel(
                "--"
            )

            change_label.setAttribute(
                Qt.WA_TransparentForMouseEvents,
                True
            )

            change_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {theme.TEXT_SECONDARY};
                    font-size: 11px;
                    background: transparent;
                    border: none;
                }}
                """
            )

            box.addWidget(
                name_label
            )

            box.addWidget(
                price_label
            )

            box.addWidget(
                change_label
            )

            index_strip.addWidget(
                card
            )

            self.index_cards[name] = {
                "card": card,
                "price": price_label,
                "change": change_label,
            }

            # ------------------------------------------------
            # CLICK
            # ------------------------------------------------

            card.clicked.connect(
                lambda checked=False,
                index=name:
                self.select_index(index)
            )

        root.addLayout(
            index_strip
        )

        # ====================================================
        # MARKET REGIME
        # ====================================================

        self.regime_card = ScannerCard(
            "Market Regime"
        )

        grid = QGridLayout()

        grid.setHorizontalSpacing(
            30
        )

        grid.setVerticalSpacing(
            8
        )

        self.add_metric(
            grid,
            0,
            0,
            "Market Bias",
            "--",
            "bias"
        )

        self.add_metric(
            grid,
            0,
            1,
            "Confidence",
            "--",
            "confidence"
        )

        self.add_metric(
            grid,
            0,
            2,
            "Volatility",
            "--",
            "volatility"
        )

        self.add_metric(
            grid,
            1,
            0,
            "Trend",
            "--",
            "trend"
        )

        self.add_metric(
            grid,
            1,
            1,
            "Bull Probability",
            "--",
            "bull"
        )

        self.add_metric(
            grid,
            1,
            2,
            "Bear Probability",
            "--",
            "bear"
        )

        self.regime_card.body.addLayout(
            grid
        )

        root.addWidget(
            self.regime_card
        )

        # ====================================================
        # OPPORTUNITIES
        # ====================================================

        opportunities = QHBoxLayout()

        opportunities.setSpacing(
            theme.CARD_GAP
        )

        self.call_card = ScannerCard(
            "Bullish Opportunity"
        )

        self.put_card = ScannerCard(
            "Bearish Opportunity"
        )

        self.best_card = ScannerCard(
            "AI Recommendation"
        )

        opportunities.addWidget(
            self.call_card
        )

        opportunities.addWidget(
            self.put_card
        )

        opportunities.addWidget(
            self.best_card
        )

        root.addLayout(
            opportunities
        )

        # ====================================================
        # RESULTS
        # ====================================================

        self.results_card = ScannerCard(
            "Scanner Results"
        )

        self.results_grid = QGridLayout()

        self.results_grid.setHorizontalSpacing(
            20
        )

        self.results_grid.setVerticalSpacing(
            10
        )

        self.results_card.body.addLayout(
            self.results_grid
        )

        root.addWidget(
            self.results_card
        )

        root.addStretch()

        # ====================================================
        # INITIAL
        # ====================================================

        self.show_empty()


    # ========================================================
    # SELECT INDEX
    # ========================================================

    def select_index(
        self,
        index
    ):

        if index not in self.SUPPORTED_INDICES:

            return

        # ----------------------------------------------------
        # Do not change during active scan
        # ----------------------------------------------------

        if (
            self.scan_worker
            and self.scan_worker.isRunning()
        ):

            return
        # ----------------------------------------------------
        # Same instrument
        # ----------------------------------------------------

        if index == self.selected_index:
            return

        self.selected_index = index

        self.selected_label.setText(
            index
        )

        # ----------------------------------------------------
        # Update card styling
        # ----------------------------------------------------

        for name, widgets in self.index_cards.items():

            card = widgets["card"]

            if name == index:

                card.setObjectName(
                    "PrimaryIndex"
                )

            else:

                card.setObjectName(
                    ""
                )

            card.style().unpolish(
                card
            )

            card.style().polish(
                card
            )

            card.update()

        # ----------------------------------------------------
        # Reset
        # ----------------------------------------------------

        self.selected_expiry = None

        self.expiry_label.setText(
            "Expiry: loading..."
        )

        self.load_expiry()

        # ----------------------------------------------------
        # RESTORE PREVIOUS RESULT
        # ----------------------------------------------------

        restored = self.restore_cached_result()

        # ----------------------------------------------------
        # No previous scan for this instrument
        # ----------------------------------------------------

        if not restored:

            self.show_empty()

    # ========================================================
    # RESTORE CACHED SCAN
    # ========================================================

    def restore_cached_result(
        self
    ):

        result = _SCAN_CACHE.get(
            self.selected_index
        )

        # ----------------------------------------------------
        # Nothing scanned yet
        # ----------------------------------------------------

        if not isinstance(
            result,
            dict
        ) or not result:

            return False

        # ----------------------------------------------------
        # Restore result
        # ----------------------------------------------------

        self.last_result = result

        # ----------------------------------------------------
        # Restore expiry
        # ----------------------------------------------------

        expiry = (
            result.get("expiry")
            or result.get("selected_expiry")
            or self.selected_expiry
        )

        if expiry:

            self.selected_expiry = str(
                expiry
            )

            self.expiry_label.setText(
                f"Expiry: {self.selected_expiry}"
            )

        # ----------------------------------------------------
        # Restore selected instrument
        # ----------------------------------------------------

        selected = (
            result.get("selected_index")
            or self.selected_index
        )

        self.selected_index = selected

        self.selected_label.setText(
            selected
        )

        # ----------------------------------------------------
        # Restore complete scanner UI
        # ----------------------------------------------------

        self.update_market_strip(
            result
        )

        self.update_regime(
            result
        )

        self.update_opportunities(
            result
        )

        self.update_results(
            result
        )

        return True
    # ========================================================
    # LOAD EXPIRY
    # ========================================================

    def load_expiry(self):

        try:

            # ------------------------------------------------
            # Current OptionChain implementation supports
            # NIFTY directly.
            # ------------------------------------------------

            if self.selected_index == "NIFTY 50":

                expiry = (
                    self.option_chain.get_current_expiry()
                )

                if expiry:

                    self.selected_expiry = str(
                        expiry
                    )

                    self.expiry_label.setText(
                        f"Expiry: {expiry}"
                    )

                    return

            # ------------------------------------------------
            # If your OptionChain has a generic expiry method,
            # use it for other indices.
            # ------------------------------------------------

            generic_method = getattr(
                self.option_chain,
                "get_current_expiry_for_symbol",
                None
            )

            if callable(generic_method):

                expiry = generic_method(
                    self.selected_index
                )

                if expiry:

                    self.selected_expiry = str(
                        expiry
                    )

                    self.expiry_label.setText(
                        f"Expiry: {expiry}"
                    )

                    return

            # ------------------------------------------------
            # Another possible generic method
            # ------------------------------------------------

            generic_method = getattr(
                self.option_chain,
                "get_current_expiry",
                None
            )

            if callable(generic_method):

                try:

                    expiry = generic_method(
                        self.selected_index
                    )

                    if expiry:

                        self.selected_expiry = str(
                            expiry
                        )

                        self.expiry_label.setText(
                            f"Expiry: {expiry}"
                        )

                        return

                except TypeError:

                    pass

            # ------------------------------------------------
            # If engine/option chain has no generic expiry yet
            # ------------------------------------------------

            self.selected_expiry = None

            self.expiry_label.setText(
                "Expiry: auto"
            )

        except Exception as e:

            print(
                "Scanner expiry error:",
                e
            )

            self.selected_expiry = None

            self.expiry_label.setText(
                "Expiry: auto"
            )


    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def num(
        value,
        default=0
    ):

        try:

            value = float(
                value
            )

            if value != value:

                return default

            return value

        except (
            TypeError,
            ValueError
        ):

            return default


    # ========================================================

    @staticmethod
    def money(
        value
    ):

        return (
            f"₹{Scanner.num(value):.2f}"
        )


    # ========================================================

    @staticmethod
    def option_name(
        trade
    ):

        strike = Scanner.num(
            trade.get(
                "strike"
            )
        )

        option_type = str(
            trade.get(
                "type",
                ""
            )
        ).upper()

        return (
            f"{strike:.0f} "
            f"{'PE' if option_type == 'PE' else 'CE'}"
        )


    # ========================================================

    def add_metric(
        self,
        grid,
        row,
        column,
        name,
        value,
        key
    ):

        label = QLabel(
            f"{name}\n{value}"
        )

        label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme.TEXT};
                font-family: "{theme.FONT}";
                font-size: 13px;
                background: transparent;
                border: none;
            }}
            """
        )

        self.metrics[
            key
        ] = label

        grid.addWidget(
            label,
            row,
            column
        )


    # ========================================================

    def clear_layout(
        self,
        layout
    ):

        while layout.count():

            item = layout.takeAt(
                0
            )

            widget = item.widget()

            if widget:

                widget.deleteLater()

            elif item.layout():

                self.clear_layout(
                    item.layout()
                )


    # ========================================================

    def card_lines(
        self,
        card,
        lines
    ):

        self.clear_layout(
            card.body
        )

        for text, bold, accent in lines:

            label = QLabel(
                text
            )

            label.setWordWrap(
                True
            )

            color = (
                theme.PRIMARY
                if accent
                else theme.TEXT
            )

            weight = (
                "600"
                if bold
                else "400"
            )

            label.setStyleSheet(
                f"""
                QLabel {{
                    color: {color};
                    font-family: "{theme.FONT}";
                    font-size: 13px;
                    font-weight: {weight};
                    background: transparent;
                    border: none;
                }}
                """
            )

            card.body.addWidget(
                label
            )


    # ========================================================
    # EMPTY
    # ========================================================

    def show_empty(
        self
    ):

        self.card_lines(
            self.call_card,
            [
                (
                    f"{self.selected_index} CALL setup",
                    True,
                    False
                ),
                (
                    "Press Scan Market to analyse.",
                    False,
                    False
                )
            ]
        )

        self.card_lines(
            self.put_card,
            [
                (
                    f"{self.selected_index} PUT setup",
                    True,
                    False
                ),
                (
                    "Press Scan Market to analyse.",
                    False,
                    False
                )
            ]
        )

        self.card_lines(
            self.best_card,
            [
                (
                    f"{self.selected_index} selected",
                    True,
                    True
                ),
                (
                    "Press Scan Market to analyse.",
                    False,
                    False
                )
            ]
        )

        self.rebuild_headers()


    # ========================================================
    # SCAN
    # ========================================================

    def scan_market(
        self
    ):

        # ----------------------------------------------------
        # Prevent duplicate scan
        # ----------------------------------------------------

        if (
            self.scan_worker
            and self.scan_worker.isRunning()
        ):

            return

        # ----------------------------------------------------
        # Make sure expiry exists
        # ----------------------------------------------------

        if not self.selected_expiry:

            self.load_expiry()

        # ----------------------------------------------------
        # Disable button
        # ----------------------------------------------------

        self.scan_button.setEnabled(
            False
        )

        self.scan_button.setText(
            "⟳  Scanning..."
        )

        # ----------------------------------------------------
        # Loading UI
        # ----------------------------------------------------

        self.card_lines(
            self.call_card,
            [
                (
                    f"Analysing {self.selected_index} CALL opportunities...",
                    False,
                    False
                )
            ]
        )

        self.card_lines(
            self.put_card,
            [
                (
                    f"Analysing {self.selected_index} PUT opportunities...",
                    False,
                    False
                )
            ]
        )

        self.card_lines(
            self.best_card,
            [
                (
                    f"AI analysing {self.selected_index}...",
                    False,
                    False
                )
            ]
        )

        # ----------------------------------------------------
        # CREATE WORKER
        #
        # IMPORTANT:
        #
        # ScannerWorker itself is QThread.
        #
        # DO NOT create another QThread.
        # ----------------------------------------------------

        self.scan_worker = ScannerWorker(
            selected_index=self.selected_index,
            expiry=self.selected_expiry,
            parent=self
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        self.scan_worker.scan_completed.connect(
            self.scan_finished
        )

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        error_signal = getattr(
            self.scan_worker,
            "error",
            None
        )

        if error_signal is not None:
            error_signal.connect(
                self.scan_error
            )

        # ----------------------------------------------------
        # FINISHED
        #
        # Whether successful or error, QThread will finish
        # after run() returns.
        # ----------------------------------------------------

        self.scan_worker.finished.connect(
            self.scan_thread_finished
        )

        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

        self.scan_worker.start()


    # ========================================================
    # THREAD FINISHED
    # ========================================================

    def scan_thread_finished(
        self
    ):

        if self.scan_worker:

            self.scan_worker.deleteLater()

        self.scan_worker = None

        self.scan_button.setEnabled(
            True
        )

        self.scan_button.setText(
            "✦  Scan Market"
        )


    # ========================================================
    # RESULT
    # ========================================================

    def scan_finished(
        self,
        result
    ):

        if not isinstance(
            result,
            dict
        ):

            result = {}

        self.last_result = result

        # ----------------------------------------------------
        # CACHE SUCCESSFUL SCAN
        # ----------------------------------------------------

        cache_index = (
            result.get("selected_index")
            or self.selected_index
        )

        _SCAN_CACHE[
            cache_index
        ] = result.copy()

        # ----------------------------------------------------
        # SELECTED INDEX
        # ----------------------------------------------------

        selected = (
            result.get(
                "selected_index"
            )
            or self.selected_index
        )

        self.selected_index = selected

        self.selected_label.setText(
            selected
        )

        # ----------------------------------------------------
        # EXPIRY
        # ----------------------------------------------------

        expiry = (
            result.get(
                "expiry"
            )
            or self.selected_expiry
        )

        if expiry:

            self.selected_expiry = str(
                expiry
            )

            self.expiry_label.setText(
                f"Expiry: {expiry}"
            )

        # ----------------------------------------------------
        # MARKET STRIP
        # ----------------------------------------------------

        self.update_market_strip(
            result
        )

        # ----------------------------------------------------
        # REGIME
        # ----------------------------------------------------

        self.update_regime(
            result
        )

        # ----------------------------------------------------
        # OPPORTUNITIES
        # ----------------------------------------------------

        self.update_opportunities(
            result
        )

        # ----------------------------------------------------
        # RESULTS
        # ----------------------------------------------------

        self.update_results(
            result
        )


    # ========================================================
    # ERROR
    # ========================================================

    def scan_error(
        self,
        error
    ):

        error_text = str(
            error
        )

        print(
            error_text
        )

        self.card_lines(
            self.best_card,
            [
                (
                    "Scan failed",
                    True,
                    False
                ),
                (
                    error_text[-1200:],
                    False,
                    False
                )
            ]
        )


    # ========================================================
    # UPDATE MARKET STRIP
    # ========================================================

    def update_market_strip(
        self,
        result
    ):

        snapshots = (
            result.get(
                "index_snapshots"
            )
            if isinstance(
                result,
                dict
            )
            else None
        )

        if not isinstance(
            snapshots,
            dict
        ):

            # -----------------------------------------------
            # Selected index fallback
            # -----------------------------------------------

            selected = (
                result.get(
                    "selected_index"
                )
                or self.selected_index
            )

            card_data = self.index_cards.get(
                selected
            )

            if card_data:

                spot = self.num(
                    result.get(
                        "spot"
                    )
                )

                if spot > 0:

                    card_data[
                        "price"
                    ].setText(
                        f"{spot:,.2f}"
                    )

            return

        # ----------------------------------------------------
        # Update all four cards
        # ----------------------------------------------------

        for name in self.SUPPORTED_INDICES:

            widgets = self.index_cards[
                name
            ]

            snapshot = (
                snapshots.get(
                    name
                )
                or {}
            )

            if not isinstance(
                snapshot,
                dict
            ):

                snapshot = {}

            spot = (
                snapshot.get(
                    "spot"
                )
                or snapshot.get(
                    "underlyingValue"
                )
                or snapshot.get(
                    "underlying_value"
                )
            )

            change = (
                snapshot.get(
                    "change_percent"
                )
                or snapshot.get(
                    "change_pct"
                )
                or snapshot.get(
                    "pct_change"
                )
            )

            # ------------------------------------------------
            # PRICE
            # ------------------------------------------------

            try:

                spot = float(
                    spot
                )

                if spot > 0:

                    widgets[
                        "price"
                    ].setText(
                        f"{spot:,.2f}"
                    )

            except (
                TypeError,
                ValueError
            ):

                pass

            # ------------------------------------------------
            # CHANGE
            # ------------------------------------------------

            try:

                change = float(
                    change
                )

                widgets[
                    "change"
                ].setText(
                    f"{change:+.2f}%"
                )

                color = (
                    "#22C55E"
                    if change >= 0
                    else "#FF5C6C"
                )

                widgets[
                    "change"
                ].setStyleSheet(
                    f"""
                    QLabel {{
                        color: {color};
                        font-size: 11px;
                        font-weight: 600;
                        background: transparent;
                        border: none;
                    }}
                    """
                )

            except (
                TypeError,
                ValueError
            ):

                pass


    # ========================================================
    # REGIME
    # ========================================================

    def update_regime(
        self,
        result
    ):

        market = (
            result.get(
                "market"
            )
            or {}
        )

        bias = (
            result.get(
                "direction"
            )
            or result.get(
                "bias"
            )
            or "Neutral"
        )

        confidence = self.num(
            result.get(
                "confidence"
            ),
            50
        )

        bull = self.num(
            result.get(
                "bull_score"
            )
        )

        bear = self.num(
            result.get(
                "bear_score"
            )
        )

        total = bull + bear

        if total:

            bull_probability = (
                bull / total * 100
            )

            bear_probability = (
                bear / total * 100
            )

        else:

            bull_probability = 50

            bear_probability = 50

        volatility = self.num(
            market.get(
                "volatility"
            )
        )

        # ----------------------------------------------------
        # Volatility text
        # ----------------------------------------------------

        if volatility < 0.04:

            volatility_text = "Low"

        elif volatility < 0.10:

            volatility_text = "Moderate"

        elif volatility > 0:

            volatility_text = "High"

        else:

            volatility_text = "Unknown"

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        self.metrics[
            "bias"
        ].setText(
            f"Market Bias\n{bias}"
        )

        self.metrics[
            "confidence"
        ].setText(
            f"Confidence\n{confidence:.0f}%"
        )

        self.metrics[
            "volatility"
        ].setText(
            f"Volatility\n{volatility_text}"
        )

        self.metrics[
            "trend"
        ].setText(
            f"Trend\n"
            f"{market.get('trend', 'Unknown')}"
        )

        self.metrics[
            "bull"
        ].setText(
            f"Bull Probability\n"
            f"{bull_probability:.0f}%"
        )

        self.metrics[
            "bear"
        ].setText(
            f"Bear Probability\n"
            f"{bear_probability:.0f}%"
        )


    # ========================================================
    # OPPORTUNITIES
    # ========================================================

    def update_opportunities(
        self,
        result
    ):

        trades = list(
            result.get(
                "trades"
            )
            or []
        )

        # ----------------------------------------------------
        # CALL
        # ----------------------------------------------------

        calls = [
            trade
            for trade in trades
            if str(
                trade.get(
                    "type",
                    ""
                )
            ).upper() == "CE"
        ]

        # ----------------------------------------------------
        # PUT
        # ----------------------------------------------------

        puts = [
            trade
            for trade in trades
            if str(
                trade.get(
                    "type",
                    ""
                )
            ).upper() == "PE"
        ]

        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        calls.sort(
            key=lambda x:
            self.num(
                x.get(
                    "ai_score"
                )
            ),
            reverse=True
        )

        puts.sort(
            key=lambda x:
            self.num(
                x.get(
                    "ai_score"
                )
            ),
            reverse=True
        )

        # ----------------------------------------------------
        # CALL CARD
        # ----------------------------------------------------

        if calls:

            self.show_trade(
                self.call_card,
                calls[0]
            )

        else:

            self.card_lines(
                self.call_card,
                [
                    (
                        "No valid CALL setup",
                        False,
                        False
                    )
                ]
            )

        # ----------------------------------------------------
        # PUT CARD
        # ----------------------------------------------------

        if puts:

            self.show_trade(
                self.put_card,
                puts[0]
            )

        else:

            self.card_lines(
                self.put_card,
                [
                    (
                        "No valid PUT setup",
                        False,
                        False
                    )
                ]
            )

        # ----------------------------------------------------
        # BEST
        # ----------------------------------------------------

        if trades:

            best_trade = max(
                trades,
                key=lambda x:
                self.num(
                    x.get(
                        "ai_score"
                    )
                )
            )

            self.show_trade(
                self.best_card,
                best_trade
            )

        else:

            self.card_lines(
                self.best_card,
                [
                    (
                        "No trade opportunity found.",
                        False,
                        False
                    )
                ]
            )


    # ========================================================
    # TRADE CARD
    # ========================================================

    def show_trade(
        self,
        card,
        trade
    ):

        risk = (
            trade.get(
                "risk"
            )
            or {}
        )

        recommendation = str(
            trade.get(
                "recommendation",
                "WATCH"
            )
        )

        self.card_lines(
            card,
            [
                (
                    self.option_name(
                        trade
                    ),
                    True,
                    False
                ),

                (
                    recommendation,
                    True,
                    True
                ),

                (
                    f"AI Score       "
                    f"{self.num(trade.get('ai_score')):.0f}/100",
                    False,
                    False
                ),

                (
                    f"Probability    "
                    f"{self.num(trade.get('probability')):.0f}%",
                    False,
                    False
                ),

                (
                    f"Premium        "
                    f"{self.money(trade.get('premium'))}",
                    False,
                    False
                ),

                (
                    f"Entry          "
                    f"{self.money(risk.get('entry', trade.get('premium')))}",
                    False,
                    False
                ),

                (
                    f"Stop Loss      "
                    f"{self.money(risk.get('sl'))}",
                    False,
                    False
                ),

                (
                    f"Target 1       "
                    f"{self.money(risk.get('target1'))}",
                    False,
                    False
                )
            ]
        )


    # ========================================================
    # HEADERS
    # ========================================================

    def rebuild_headers(
        self
    ):

        self.clear_layout(
            self.results_grid
        )

        headers = [
            "Instrument",
            "Type",
            "Score",
            "Probability",
            "Premium",
            "Signal"
        ]

        for column, text in enumerate(
            headers
        ):

            label = QLabel(
                text
            )

            label.setStyleSheet(
                f"""
                QLabel {{
                    color: {theme.TEXT_SECONDARY};
                    font-size: 12px;
                    font-weight: 600;
                    background: transparent;
                    border: none;
                }}
                """
            )

            self.results_grid.addWidget(
                label,
                0,
                column
            )


    # ========================================================
    # RESULTS
    # ========================================================

    def update_results(
        self,
        result
    ):

        self.rebuild_headers()

        trades = list(
            result.get(
                "trades"
            )
            or []
        )

        trades.sort(
            key=lambda x:
            self.num(
                x.get(
                    "ai_score"
                )
            ),
            reverse=True
        )

        for row, trade in enumerate(
            trades[:6],
            start=1
        ):

            option_type = str(
                trade.get(
                    "type",
                    ""
                )
            ).upper()

            values = [

                self.option_name(
                    trade
                ),

                (
                    "PUT"
                    if option_type == "PE"
                    else "CALL"
                ),

                (
                    f"{self.num(trade.get('ai_score')):.0f}"
                ),

                (
                    f"{self.num(trade.get('probability')):.0f}%"
                ),

                self.money(
                    trade.get(
                        "premium"
                    )
                ),

                str(
                    trade.get(
                        "recommendation",
                        "WATCH"
                    )
                )
            ]

            for column, value in enumerate(
                values
            ):

                label = QLabel(
                    value
                )

                label.setWordWrap(
                    True
                )

                label.setSizePolicy(
                    QSizePolicy.Expanding,
                    QSizePolicy.Preferred
                )

                label.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {theme.TEXT};
                        font-size: 13px;
                        background: transparent;
                        border: none;
                    }}
                    """
                )

                self.results_grid.addWidget(
                    label,
                    row,
                    column
                )


    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        # ----------------------------------------------------
        # Stop scanner worker if active
        # ----------------------------------------------------

        if (
            self.scan_worker
            and self.scan_worker.isRunning()
        ):

            self.scan_worker.quit()

            self.scan_worker.wait(
                2000
            )

        event.accept()