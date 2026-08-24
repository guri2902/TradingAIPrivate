from __future__ import annotations

import traceback
import math

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QSizePolicy,
    QAbstractItemView,
)

from engine.trade_engine import TradeEngine


# ============================================================
# COLORS
# ============================================================

BG = "#070B12"
SURFACE = "#0B131E"
SURFACE_2 = "#0D1724"
SURFACE_3 = "#101B29"

BORDER = "#1D3045"
BORDER_HOVER = "#31536F"

TEXT = "#F4F8FC"
TEXT_SECONDARY = "#B6C4D4"
TEXT_MUTED = "#71859B"

CYAN = "#28C7FF"
CYAN_SOFT = "#8EDFFF"

PURPLE = "#8B6CFF"
PURPLE_SOFT = "#B7A5FF"

GREEN = "#39E6A2"
RED = "#FF5F68"
YELLOW = "#F3C85B"
BLUE = "#168BFF"


# ============================================================
# HELPERS
# ============================================================

def number(value, default=0.0):
    try:
        if value is None:
            return default

        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


def money(value):
    value = number(value)

    if value <= 0:
        return "--"

    return f"₹{value:,.2f}"


def price(value):
    value = number(value)

    if value <= 0:
        return "--"

    return f"{value:,.2f}"


def integer(value):
    value = number(value)

    if value <= 0:
        return "--"

    return f"{int(value):,}"


def compact(value):
    value = number(value)

    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if value >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:.0f}"


# ============================================================
# INDEX CARD
# ============================================================

class IndexCard(QFrame):

    clicked = Signal(str)

    def __init__(
        self,
        name,
        parent=None
    ):
        super().__init__(parent)

        self.name = name

        self.setObjectName("IndexCard")
        self.setCursor(Qt.PointingHandCursor)

        self.setMinimumHeight(72)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            13,
            8,
            13,
            8
        )

        layout.setSpacing(2)

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        self.name_label = QLabel(name)

        self.name_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: #8EA2B8;
                font-size: 11px;
                font-weight: 700;
            }
        """)

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        self.price_label = QLabel("--")

        self.price_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: #F7FBFF;
                font-size: 22px;
                font-weight: 750;
            }
        """)

        # ----------------------------------------------------
        # META
        # ----------------------------------------------------

        self.meta_label = QLabel("--")

        self.meta_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: #71859D;
                font-size: 10px;
            }
        """)

        layout.addWidget(self.name_label)
        layout.addWidget(self.price_label)
        layout.addWidget(self.meta_label)

        self.set_selected(False)

    # ========================================================

    def set_selected(self, selected):

        if selected:

            self.setStyleSheet("""
                QFrame#IndexCard {
                    background: #0D263D;
                    border: 1px solid #1B9DFF;
                    border-radius: 12px;
                }
            """)

        else:

            self.setStyleSheet("""
                QFrame#IndexCard {
                    background: #0D151F;
                    border: 1px solid #1C2D40;
                    border-radius: 12px;
                }

                QFrame#IndexCard:hover {
                    background: #112131;
                    border: 1px solid #31536F;
                }
            """)

    # ========================================================

    def set_data(
        self,
        value,
        meta="--"
    ):

        self.price_label.setText(
            price(value)
        )

        self.meta_label.setText(
            str(meta)
        )

    # ========================================================

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            self.clicked.emit(
                self.name
            )

        super().mousePressEvent(event)


# ============================================================
# OPTION CHAIN WORKER
# ============================================================

class OptionChainWorker(QThread):

    completed = Signal(dict)
    error = Signal(str)

    def __init__(
        self,
        selected_index,
        expiry=None,
        parent=None
    ):
        super().__init__(parent)

        self.selected_index = selected_index
        self.expiry = expiry

    # ========================================================

    def run(self):

        try:

            print(
                "========================================"
            )

            print(
                "OPTION CHAIN STARTED"
            )

            print(
                f"Index  : {self.selected_index}"
            )

            print(
                f"Expiry : {self.expiry}"
            )

            print(
                "========================================"
            )

            # ------------------------------------------------
            # EXISTING ENGINE
            # ------------------------------------------------

            engine = TradeEngine()

            # ------------------------------------------------
            # EXPIRIES
            # ------------------------------------------------

            expiries = []

            try:

                expiries = (
                    engine.chain.get_expiry_dates(
                        self.selected_index
                    )
                    or []
                )

            except Exception as exc:

                print(
                    "Expiry fetch error:",
                    exc
                )

            # ------------------------------------------------
            # RESOLVE EXPIRY
            # ------------------------------------------------

            selected_expiry = self.expiry

            if (
                selected_expiry
                and selected_expiry not in expiries
            ):

                selected_expiry = None

            if not selected_expiry:

                selected_expiry = (
                    engine.chain.get_current_expiry(
                        self.selected_index
                    )
                )

            if not selected_expiry:

                raise RuntimeError(
                    f"Unable to determine expiry for "
                    f"{self.selected_index}."
                )

            # ------------------------------------------------
            # GENERATE DATA
            # ------------------------------------------------

            result = engine.generate_trades(
                selected_index=self.selected_index,
                expiry=selected_expiry
            )

            if not result:

                raise RuntimeError(
                    "Trade engine returned no data."
                )

            result["expiries"] = expiries

            result["selected_expiry"] = (
                selected_expiry
            )

            # ------------------------------------------------
            # MARKET SNAPSHOTS
            # ------------------------------------------------

            snapshots = {}

            market_methods = {

                "NIFTY 50":
                    "get_nifty",

                "BANK NIFTY":
                    "get_banknifty",

                "FINNIFTY":
                    "get_finnifty",

                "MIDCAP NIFTY":
                    "get_midcapnifty",
            }

            for name, method_name in (
                market_methods.items()
            ):

                try:

                    method = getattr(
                        engine.market,
                        method_name,
                        None
                    )

                    if callable(method):

                        data = method()

                        if isinstance(
                            data,
                            dict
                        ):

                            snapshots[name] = data

                except Exception as exc:

                    print(
                        f"Snapshot error "
                        f"[{name}]:",
                        exc
                    )

            result["snapshots"] = snapshots

            # ------------------------------------------------
            # COMPLETE
            # ------------------------------------------------

            self.completed.emit(
                result
            )

            print(
                "========================================"
            )

            print(
                "OPTION CHAIN COMPLETED"
            )

            print(
                "========================================"
            )

        except Exception:

            error_text = (
                traceback.format_exc()
            )

            print(
                "========================================"
            )

            print(
                "OPTION CHAIN ERROR"
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


# ============================================================
# OPTION CHAIN PAGE
# ============================================================

class OptionChain(QWidget):

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

        self.selected_index = (
            "NIFTY 50"
        )

        self.selected_expiry = None

        self.worker = None

        self.last_result = {}

        self.index_cards = {}

        self.setObjectName(
            "OptionChainPage"
        )

        self.apply_styles()

        self.build_ui()

        self.load_chain()

    # ========================================================
    # GLOBAL STYLE
    # ========================================================

    def apply_styles(self):

        self.setStyleSheet("""

            /* =================================================
               PAGE
               ================================================= */

            QWidget#OptionChainPage {
                background: #070B12;
                color: #F4F8FC;
                font-family: "Segoe UI";
            }


            QLabel {
                background: transparent;
                color: #F4F8FC;
            }


            /* =================================================
               EXPIRY
               ================================================= */

            QComboBox {

                background: #0D1623;

                color: #F4F8FC;

                border:
                    1px solid #29425D;

                border-radius:
                    10px;

                padding:
                    9px 13px;

                min-width:
                    155px;

                min-height:
                    38px;

                font-size:
                    13px;

                font-weight:
                    600;
            }


            QComboBox:hover {

                background:
                    #101D2D;

                border:
                    1px solid #16A8FF;
            }


            QComboBox:focus {

                border:
                    1px solid #8B6CFF;
            }


            QComboBox::drop-down {

                width:
                    30px;

                border:
                    none;
            }


            /* IMPORTANT:
               Styles the actual popup list.
            */

            QComboBox QAbstractItemView {

                background:
                    #0D1623;

                color:
                    #F4F8FC;

                border:
                    1px solid #29425D;

                selection-background-color:
                    #164B73;

                selection-color:
                    #FFFFFF;

                padding:
                    6px;

                outline:
                    none;

                font-size:
                    13px;
            }


            /* =================================================
               REFRESH BUTTON
               ================================================= */

            QPushButton {

                background:
                    #1683FF;

                color:
                    #FFFFFF;

                border:
                    1px solid #2997FF;

                border-radius:
                    10px;

                padding:
                    9px 18px;

                min-height:
                    38px;

                font-size:
                    13px;

                font-weight:
                    700;
            }


            QPushButton:hover {

                background:
                    #2295FF;

                border:
                    1px solid #65BAFF;
            }


            QPushButton:pressed {

                background:
                    #0E6DCE;
            }


            QPushButton:disabled {

                background:
                    #172536;

                color:
                    #68788D;

                border:
                    1px solid #23364C;
            }


            /* =================================================
               TABLE
               ================================================= */

            QTableWidget {

                background:
                    #0B111A;

                color:
                    #EDF4FB;

                border:
                    none;

                gridline-color:
                    #1E3044;

                selection-background-color:
                    #173B5D;

                selection-color:
                    #FFFFFF;

                font-size:
                    13px;

                font-weight:
                    500;

                outline:
                    none;
            }


            QTableWidget::item {

                padding:
                    4px 8px;

                border-bottom:
                    1px solid #152437;
            }


            QTableWidget::item:hover {

                background:
                    #101D2C;
            }


            /* =================================================
               TABLE HEADER
               ================================================= */

            QHeaderView::section {

                background:
                    #101A28;

                color:
                    #8FD7FF;

                border:
                    none;

                border-bottom:
                    1px solid #2A4965;

                padding:
                    6px 6px;

                min-height:
                    30px;

                font-size:
                    12px;

                font-weight:
                    700;
            }


            /* =================================================
               SCROLLBAR
               ================================================= */

            QScrollBar:vertical {

                background:
                    #08101A;

                width:
                    9px;

                margin:
                    2px;
            }


            QScrollBar::handle:vertical {

                background:
                    #29445E;

                border-radius:
                    4px;

                min-height:
                    30px;
            }


            QScrollBar::handle:vertical:hover {

                background:
                    #3C6B91;
            }

        """)

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            16,
            12,
            16,
            10
        )

        root.setSpacing(
            7
        )

        # ====================================================
        # TOP HEADER
        # ====================================================

        header = QHBoxLayout()

        header.setSpacing(
            10
        )

        title_box = QVBoxLayout()

        title_box.setSpacing(
            1
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = QLabel(
            "Option Chain"
        )

        title.setStyleSheet("""
            QLabel {
                color: #F7FBFF;
                font-size: 28px;
                font-weight: 750;
            }
        """)

        title_box.addWidget(
            title
        )

        # ----------------------------------------------------
        # SUBTITLE
        # ----------------------------------------------------

        subtitle = QLabel(
            "Live option-chain analysis • OI intelligence • AI signals"
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #8295AA;
                font-size: 13px;
                font-weight: 400;
            }
        """)

        title_box.addWidget(
            subtitle
        )

        header.addLayout(
            title_box
        )

        header.addStretch()

        # ----------------------------------------------------
        # EXPIRY LABEL
        # ----------------------------------------------------

        expiry_label = QLabel(
            "Expiry"
        )

        expiry_label.setStyleSheet("""
            QLabel {
                color: #8DA3B9;
                font-size: 12px;
                font-weight: 700;
                margin-right: 2px;
            }
        """)

        header.addWidget(
            expiry_label
        )

        # ----------------------------------------------------
        # EXPIRY COMBO
        # ----------------------------------------------------

        self.expiry_combo = QComboBox()

        self.expiry_combo.currentIndexChanged.connect(
            self.expiry_changed
        )

        header.addWidget(
            self.expiry_combo
        )

        # ----------------------------------------------------
        # REFRESH
        # ----------------------------------------------------

        self.refresh_button = QPushButton(
            "↻  Refresh"
        )

        self.refresh_button.clicked.connect(
            self.refresh_chain
        )

        header.addWidget(
            self.refresh_button
        )

        root.addLayout(
            header
        )

        # ====================================================
        # INDEX CARDS
        # ====================================================

        cards_layout = QHBoxLayout()

        cards_layout.setSpacing(
            8
        )

        for index in self.SUPPORTED_INDICES:

            card = IndexCard(
                index
            )

            card.clicked.connect(
                self.select_index
            )

            self.index_cards[index] = card

            cards_layout.addWidget(
                card
            )

        root.addLayout(
            cards_layout
        )

        self.update_selected_card()

        # ====================================================
        # MARKET SUMMARY
        # ====================================================

        summary = QHBoxLayout()

        summary.setSpacing(
            8
        )

        self.spot_value = (
            self.create_metric(
                summary,
                "SPOT"
            )
        )

        self.pcr_value = (
            self.create_metric(
                summary,
                "PCR"
            )
        )

        self.max_pain_value = (
            self.create_metric(
                summary,
                "MAX PAIN"
            )
        )

        self.atm_value = (
            self.create_metric(
                summary,
                "ATM"
            )
        )

        self.bias_value = (
            self.create_metric(
                summary,
                "BIAS"
            )
        )

        root.addLayout(
            summary
        )

        # ====================================================
        # OPTION TABLE CARD
        # ====================================================

        table_card = QFrame()

        table_card.setObjectName(
            "TableCard"
        )

        table_card.setStyleSheet("""
            QFrame#TableCard {

                background:
                    #0B131E;

                border:
                    1px solid #20364D;

                border-radius:
                    13px;
            }
        """)

        table_layout = QVBoxLayout(
            table_card
        )

        table_layout.setContentsMargins(
            9,
            7,
            9,
            7
        )

        table_layout.setSpacing(
            3
        )

        # Keep the option-chain card compact.  The previous layout allowed
        # this card to vertically expand far beyond the actual table,
        # leaving a large empty area underneath the rows.
        table_card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        # ----------------------------------------------------
        # TABLE TITLE
        # ----------------------------------------------------

        table_title = QLabel(
            "OPTION CHAIN"
        )

        table_title.setStyleSheet("""
            QLabel {
                color: #E9F5FF;
                font-size: 14px;
                font-weight: 750;
                letter-spacing: 0.5px;
            }
        """)

        table_layout.addWidget(
            table_title
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.table_status = QLabel(
            "Loading live NSE data..."
        )

        self.table_status.setStyleSheet("""
            QLabel {
                color: #71869D;
                font-size: 11px;
            }
        """)

        table_layout.addWidget(
            self.table_status
        )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(
            11
        )

        self.table.setHorizontalHeaderLabels([
            "CALL OI",
            "CALL LTP",
            "CALL Δ",
            "CALL IV",
            "STRIKE",
            "PUT IV",
            "PUT Δ",
            "PUT LTP",
            "PUT OI",
            "SIGNAL",
            "AI SCORE",
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.horizontalHeader().setMinimumSectionSize(
            70
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.verticalHeader().setDefaultSectionSize(
            35
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setAlternatingRowColors(
            False
        )

        self.table.setFocusPolicy(
            Qt.NoFocus
        )

        # ----------------------------------------------------
        # COMPACT TABLE HEIGHT
        # ----------------------------------------------------
        # The old table-card was allowed to stretch vertically while
        # the table itself stayed fixed at 305px.  That created the
        # large blank area visible underneath the table.
        #
        # Give the table a little more usable height and keep the
        # surrounding card fixed so there is no empty vertical region.

        self.table.setMinimumHeight(
            0
        )

        self.table.setMaximumHeight(
            350
        )

        self.table.setFixedHeight(
            350
        )

        table_layout.addWidget(
            self.table
        )

        # 350px table + compact title/status/margins.
        # Prevent the card from growing into the unused page space.
        table_card.setFixedHeight(
            398
        )

        root.addWidget(
            table_card
        )

        # ====================================================
        # BOTTOM ANALYSIS
        # ====================================================

        bottom = QHBoxLayout()

        bottom.setSpacing(
            8
        )

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        self.ai_card = (
            self.create_analysis_card(
                "AI OPTION ANALYSIS",
                PURPLE
            )
        )

        # ----------------------------------------------------
        # OI
        # ----------------------------------------------------

        self.oi_card = (
            self.create_analysis_card(
                "OI INTELLIGENCE",
                CYAN
            )
        )

        # ----------------------------------------------------
        # RISK
        # ----------------------------------------------------

        self.risk_card = (
            self.create_analysis_card(
                "TRADE RISK",
                GREEN
            )
        )

        bottom.addWidget(
            self.ai_card
        )

        bottom.addWidget(
            self.oi_card
        )

        bottom.addWidget(
            self.risk_card
        )

        root.addLayout(
            bottom
        )

    # ========================================================
    # METRIC CARD
    # ========================================================

    def create_metric(
        self,
        parent_layout,
        title
    ):

        card = QFrame()

        card.setObjectName(
            "MetricCard"
        )
        card.setFixedHeight(125)

        card.setStyleSheet("""
            QFrame#MetricCard {

                background:
                    #0D1622;

                border:
                    1px solid #1D3349;

                border-radius:
                    11px;
            }

            QFrame#MetricCard:hover {

                border:
                    1px solid #31536F;

                background:
                    #101C2A;
            }
        """)

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            10,
            7,
            10,
            7
        )

        layout.setSpacing(
            1
        )

        label = QLabel(
            title
        )

        label.setStyleSheet("""
            QLabel {
                color: #7F96AD;
                font-size: 11px;
                font-weight: 700;
            }
        """)

        value = QLabel(
            "--"
        )

        value.setStyleSheet("""
            QLabel {
                color: #F5F9FF;
                font-size: 21px;
                font-weight: 750;
            }
        """)

        layout.addWidget(
            label
        )

        layout.addWidget(
            value
        )

        parent_layout.addWidget(
            card
        )

        return value

    # ========================================================
    # ANALYSIS CARD
    # ========================================================

    def create_analysis_card(
        self,
        title,
        accent
    ):

        card = QFrame()

        card.setObjectName(
            "AnalysisCard"
        )

        card.setStyleSheet(
            f"""
            QFrame#AnalysisCard {{

                background:
                    #0D1622;

                border:
                    1px solid #20364D;

                border-radius:
                    12px;
            }}

            QFrame#AnalysisCard:hover {{

                border:
                    1px solid {accent};
            }}
            """
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            11,
            9,
            11,
            9
        )

        layout.setSpacing(
            5
        )

        # ----------------------------------------------------
        # HEADING
        # ----------------------------------------------------

        heading = QLabel(
            title
        )

        heading.setStyleSheet(
            f"""
            QLabel {{

                color:
                    {accent};

                font-size:
                    12px;

                font-weight:
                    750;
            }}
            """
        )

        # ----------------------------------------------------
        # BODY
        # ----------------------------------------------------

        body = QLabel(
            "Loading..."
        )

        body.setWordWrap(
            True
        )

        body.setAlignment(
            Qt.AlignTop
        )

        body.setTextFormat(
            Qt.RichText
        )

        body.setStyleSheet("""
            QLabel {

                color:
                    #DBE8F5;

                font-size:
                    13px;
            }
        """)

        layout.addWidget(
            heading
        )

        layout.addWidget(
            body,
            1
        )

        card.body = body

        card.setMinimumHeight(
            145
        )

        card.setMaximumHeight(
            160
        )

        return card

    # ========================================================
    # INDEX SELECTION
    # ========================================================

    def select_index(
        self,
        index
    ):

        if index not in self.SUPPORTED_INDICES:
            return

        if (
            self.worker
            and self.worker.isRunning()
        ):
            return

        if index == self.selected_index:
            return

        self.selected_index = index

        self.selected_expiry = None

        self.update_selected_card()

        self.expiry_combo.blockSignals(
            True
        )

        self.expiry_combo.clear()

        self.expiry_combo.addItem(
            "Loading expiries..."
        )

        self.expiry_combo.blockSignals(
            False
        )

        self.set_loading_state()

        self.load_chain()

    # ========================================================
    # SELECTED CARD
    # ========================================================

    def update_selected_card(self):

        for name, card in (
            self.index_cards.items()
        ):

            card.set_selected(
                name == self.selected_index
            )

    # ========================================================
    # EXPIRY CHANGED
    # ========================================================

    def expiry_changed(
        self,
        index
    ):

        if index < 0:
            return

        text = (
            self.expiry_combo.currentText()
        )

        if not text:
            return

        if text == "Loading expiries...":
            return

        if text == "No expiry available":
            return

        self.selected_expiry = text

        self.load_chain()

    # ========================================================
    # LOAD
    # ========================================================

    def load_chain(self):

        if (
            self.worker
            and self.worker.isRunning()
        ):
            return

        self.set_loading_state()

        expiry = (
            self.selected_expiry
        )

        self.worker = OptionChainWorker(
            selected_index=self.selected_index,
            expiry=expiry,
            parent=self
        )

        self.worker.completed.connect(
            self.on_data_loaded
        )

        self.worker.error.connect(
            self.on_error
        )

        self.worker.finished.connect(
            self.on_worker_finished
        )

        self.refresh_button.setEnabled(
            False
        )

        self.worker.start()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_chain(self):

        if (
            self.worker
            and self.worker.isRunning()
        ):
            return

        self.load_chain()

    # ========================================================
    # LOADING
    # ========================================================

    def set_loading_state(self):

        self.table_status.setText(
            f"Loading live NSE option chain for "
            f"{self.selected_index}..."
        )

        self.spot_value.setText(
            "..."
        )

        self.pcr_value.setText(
            "..."
        )

        self.max_pain_value.setText(
            "..."
        )

        self.atm_value.setText(
            "..."
        )

        self.bias_value.setText(
            "..."
        )

        self.ai_card.body.setText(
            "Analysing live option-chain data..."
        )

        self.oi_card.body.setText(
            "Calculating open-interest structure..."
        )

        self.risk_card.body.setText(
            "Calculating best available setup..."
        )

    # ========================================================
    # DATA LOADED
    # ========================================================

    def on_data_loaded(
        self,
        result
    ):

        self.last_result = (
            result or {}
        )

        self.selected_expiry = (
            result.get(
                "selected_expiry"
            )
        )

        self.populate_expiries(
            result.get(
                "expiries",
                []
            )
        )

        self.update_index_cards(
            result.get(
                "snapshots",
                {}
            ),
            result
        )

        self.update_summary(
            result
        )

        self.update_table(
            result
        )

        self.update_analysis(
            result
        )

        self.table_status.setText(
            f"Live NSE data  •  "
            f"{result.get('selected_index', self.selected_index)}  •  "
            f"Expiry {self.selected_expiry or '--'}"
        )

    # ========================================================
    # EXPIRIES
    # ========================================================

    def populate_expiries(
        self,
        expiries
    ):

        expiries = [
            str(x)
            for x in expiries
            if x
        ]

        current = (
            self.selected_expiry
        )

        self.expiry_combo.blockSignals(
            True
        )

        self.expiry_combo.clear()

        if not expiries:

            self.expiry_combo.addItem(
                "No expiry available"
            )

        else:

            self.expiry_combo.addItems(
                expiries
            )

            if current in expiries:

                self.expiry_combo.setCurrentText(
                    current
                )

            else:

                self.expiry_combo.setCurrentIndex(
                    0
                )

                self.selected_expiry = (
                    expiries[0]
                )

        self.expiry_combo.blockSignals(
            False
        )

    # ========================================================
    # INDEX CARDS
    # ========================================================

    def update_index_cards(
        self,
        snapshots,
        result
    ):

        selected = (
            result.get(
                "selected_index",
                self.selected_index
            )
        )

        selected_spot = number(
            result.get(
                "spot"
            )
        )

        for name, card in (
            self.index_cards.items()
        ):

            if name == selected:

                card.set_data(
                    selected_spot,
                    f"Expiry {result.get('selected_expiry', '--')}"
                )

                continue

            data = snapshots.get(
                name,
                {}
            )

            card.set_data(
                data.get(
                    "price"
                ),
                data.get(
                    "trend",
                    "--"
                )
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    def update_summary(
        self,
        result
    ):

        spot = number(
            result.get(
                "spot"
            )
        )

        chain = (
            result.get(
                "chain"
            )
            or {}
        )

        sr = (
            result.get(
                "support_resistance"
            )
            or {}
        )

        pcr = number(
            chain.get(
                "pcr"
            ),
            0
        )

        bias = (
            result.get(
                "direction"
            )
            or chain.get(
                "bias"
            )
            or "Neutral"
        )

        max_pain = (
            chain.get(
                "max_pain"
            )
        )

        if max_pain is None:

            max_pain = (
                sr.get(
                    "max_pain"
                )
            )

        rows = self.get_rows(
            result
        )

        atm = self.find_atm(
            rows,
            spot
        )

        self.spot_value.setText(
            price(spot)
        )

        self.pcr_value.setText(
            f"{pcr:.2f}"
        )

        self.max_pain_value.setText(
            price(max_pain)
        )

        self.atm_value.setText(
            price(atm)
        )

        self.bias_value.setText(
            str(bias).upper()
        )

        # ----------------------------------------------------
        # BIAS COLOR
        # ----------------------------------------------------

        if str(bias).lower() == "bullish":

            color = GREEN

        elif str(bias).lower() == "bearish":

            color = RED

        else:

            color = YELLOW

        self.bias_value.setStyleSheet(
            f"""
            QLabel {{

                color:
                    {color};

                font-size:
                    19px;

                font-weight:
                    750;
            }}
            """
        )

    # ========================================================
    # GET ROWS
    # ========================================================

    def get_rows(
        self,
        result
    ):

        trades = (
            result.get(
                "all_trades"
            )
            or result.get(
                "trades"
            )
            or []
        )

        grouped = {}

        for trade in trades:

            if not isinstance(
                trade,
                dict
            ):
                continue

            strike = number(
                trade.get(
                    "strike"
                )
            )

            if strike <= 0:
                continue

            key = strike

            if key not in grouped:

                grouped[key] = {

                    "strike":
                        strike,

                    "CE":
                        None,

                    "PE":
                        None,
                }

            option_type = str(
                trade.get(
                    "type",
                    ""
                )
            ).upper()

            if option_type in (
                "CE",
                "PE"
            ):

                grouped[key][
                    option_type
                ] = trade

        rows = list(
            grouped.values()
        )

        rows.sort(
            key=lambda x:
            x["strike"]
        )

        return rows

    # ========================================================
    # ATM
    # ========================================================

    @staticmethod
    def find_atm(
        rows,
        spot
    ):

        if not rows:
            return None

        valid = [
            row["strike"]
            for row in rows
            if row.get("strike")
        ]

        if not valid:
            return None

        return min(
            valid,
            key=lambda x:
            abs(x - spot)
        )

    # ========================================================
    # TABLE
    # ========================================================

    def update_table(
        self,
        result
    ):

        rows = self.get_rows(
            result
        )

        self.table.setRowCount(
            0
        )

        if not rows:

            self.table_status.setText(
                "No option-chain rows returned."
            )

            return

        atm = self.find_atm(
            rows,
            number(
                result.get(
                    "spot"
                )
            )
        )

        self.table.setRowCount(
            len(rows)
        )

        for row_index, row in enumerate(
            rows
        ):

            strike = row[
                "strike"
            ]

            ce = row.get(
                "CE"
            ) or {}

            pe = row.get(
                "PE"
            ) or {}

            ce_greeks = (
                ce.get(
                    "greeks"
                )
                or {}
            )

            pe_greeks = (
                pe.get(
                    "greeks"
                )
                or {}
            )

            ce_delta = number(
                ce_greeks.get(
                    "delta"
                )
            )

            pe_delta = number(
                pe_greeks.get(
                    "delta"
                )
            )

            # ------------------------------------------------
            # VALUES
            # ------------------------------------------------

            values = [

                integer(
                    ce.get(
                        "ce_oi"
                    )
                ),

                price(
                    ce.get(
                        "ce_ltp",
                        ce.get(
                            "premium"
                        )
                    )
                ),

                f"{ce_delta:.2f}"
                if ce
                else "--",

                f"{number(ce.get('ce_iv')):.1f}"
                if ce
                else "--",

                f"{strike:,.0f}",

                f"{number(pe.get('pe_iv')):.1f}"
                if pe
                else "--",

                f"{pe_delta:.2f}"
                if pe
                else "--",

                price(
                    pe.get(
                        "pe_ltp",
                        pe.get(
                            "premium"
                        )
                    )
                ),

                integer(
                    pe.get(
                        "pe_oi"
                    )
                ),

                self.best_signal(
                    ce,
                    pe
                ),

                self.best_score(
                    ce,
                    pe
                ),
            ]

            # ------------------------------------------------
            # CREATE ITEMS
            # ------------------------------------------------

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                item.setFont(
                    QFont(
                        "Segoe UI",
                        11
                    )
                )

                self.table.setItem(
                    row_index,
                    column,
                    item
                )

            # ------------------------------------------------
            # SIGNAL COLOR
            # ------------------------------------------------

            signal_text = (
                str(
                    values[9]
                ).upper()
            )

            if (
                "TRADEABLE"
                in signal_text
                or
                "STRONG"
                in signal_text
            ):

                signal_color = GREEN

            elif "AVOID" in signal_text:

                signal_color = RED

            else:

                signal_color = YELLOW

            signal_item = (
                self.table.item(
                    row_index,
                    9
                )
            )

            if signal_item:

                signal_item.setForeground(
                    QBrush(
                        QColor(
                            signal_color
                        )
                    )
                )

                font = signal_item.font()

                font.setBold(
                    True
                )

                signal_item.setFont(
                    font
                )

            # ------------------------------------------------
            # SCORE COLOR
            # ------------------------------------------------

            score_item = (
                self.table.item(
                    row_index,
                    10
                )
            )

            if score_item:

                score = number(
                    values[10]
                )

                if score >= 70:

                    score_color = GREEN

                elif score >= 50:

                    score_color = YELLOW

                else:

                    score_color = RED

                score_item.setForeground(
                    QBrush(
                        QColor(
                            score_color
                        )
                    )
                )

                font = score_item.font()

                font.setBold(
                    True
                )

                score_item.setFont(
                    font
                )

            # ------------------------------------------------
            # STRIKE EMPHASIS
            # ------------------------------------------------

            strike_item = (
                self.table.item(
                    row_index,
                    4
                )
            )

            if strike_item:

                strike_item.setForeground(
                    QBrush(
                        QColor(
                            CYAN_SOFT
                        )
                    )
                )

                font = strike_item.font()

                font.setBold(
                    True
                )

                strike_item.setFont(
                    font
                )

            # ------------------------------------------------
            # ATM HIGHLIGHT
            # ------------------------------------------------

            if (
                atm is not None
                and strike == atm
            ):

                for column in range(
                    self.table.columnCount()
                ):

                    item = (
                        self.table.item(
                            row_index,
                            column
                        )
                    )

                    if item:

                        item.setBackground(
                            QBrush(
                                QColor(
                                    "#12304B"
                                )
                            )
                        )

                        item.setForeground(
                            QBrush(
                                QColor(
                                    "#FFFFFF"
                                )
                            )
                        )

                        font = item.font()

                        font.setBold(
                            True
                        )

                        item.setFont(
                            font
                        )

        # Keep rows compact.
        self.table.resizeRowsToContents()

        for row in range(
            self.table.rowCount()
        ):

            self.table.setRowHeight(
                row,
                34
            )

    # ========================================================
    # SCORE
    # ========================================================

    @staticmethod
    def best_score(
        ce,
        pe
    ):

        scores = []

        if ce:

            scores.append(
                number(
                    ce.get(
                        "ai_score"
                    )
                )
            )

        if pe:

            scores.append(
                number(
                    pe.get(
                        "ai_score"
                    )
                )
            )

        if not scores:
            return "--"

        return str(
            int(
                max(scores)
            )
        )

    # ========================================================
    # SIGNAL
    # ========================================================

    @staticmethod
    def best_signal(
        ce,
        pe
    ):

        candidates = []

        if ce:

            candidates.append(
                (
                    number(
                        ce.get(
                            "ai_score"
                        )
                    ),
                    "CE",
                    ce.get(
                        "recommendation",
                        "WATCH"
                    )
                )
            )

        if pe:

            candidates.append(
                (
                    number(
                        pe.get(
                            "ai_score"
                        )
                    ),
                    "PE",
                    pe.get(
                        "recommendation",
                        "WATCH"
                    )
                )
            )

        if not candidates:
            return "--"

        candidates.sort(
            reverse=True
        )

        score, option_type, recommendation = (
            candidates[0]
        )

        recommendation = str(
            recommendation
        )

        if "STRONG" in recommendation.upper():

            return (
                f"{option_type} • STRONG"
            )

        if "TRADEABLE" in recommendation.upper():

            return (
                f"{option_type} • TRADEABLE"
            )

        if "WATCH" in recommendation.upper():

            return (
                f"{option_type} • WATCH"
            )

        if "AVOID" in recommendation.upper():

            return (
                f"{option_type} • AVOID"
            )

        return (
            f"{option_type} • WATCH"
        )

    # ========================================================
    # ANALYSIS
    # ========================================================

    def update_analysis(
        self,
        result
    ):

        rows = self.get_rows(
            result
        )

        chain = (
            result.get(
                "chain"
            )
            or {}
        )

        # ====================================================
        # BEST TRADE
        # ====================================================

        trades = (
            result.get(
                "trades"
            )
            or []
        )

        best = (
            trades[0]
            if trades
            else None
        )

        if best:

            option_type = str(
                best.get(
                    "type",
                    ""
                )
            ).upper()

            strike = number(
                best.get(
                    "strike"
                )
            )

            score = number(
                best.get(
                    "ai_score"
                )
            )

            probability = number(
                best.get(
                    "probability"
                )
            )

            premium = number(
                best.get(
                    "premium"
                )
            )

            recommendation = str(
                best.get(
                    "recommendation",
                    "WATCH"
                )
            )

            market_bias = (
                result.get(
                    "direction"
                )
                or "Neutral"
            )

            support = (
                best.get(
                    "support"
                )
            )

            resistance = (
                best.get(
                    "resistance"
                )
            )

            max_pain = (
                best.get(
                    "max_pain"
                )
            )

            # ------------------------------------------------
            # AI CARD
            # ------------------------------------------------

            ai_text = (

                f"""
                <div style="
                    color:#B7A5FF;
                    font-size:12px;
                    font-weight:700;
                ">
                    BEST AI SETUP
                </div>

                <div style="
                    color:#F7FBFF;
                    font-size:20px;
                    font-weight:750;
                    margin-top:4px;
                ">
                    {strike:,.0f} {option_type}
                </div>

                <div style="
                    margin-top:6px;
                    color:#D8E7F5;
                    font-size:13px;
                    line-height:1.45;
                ">
                    AI Score
                    <b style="color:#39E6A2;">
                        {score:.0f}/100
                    </b>
                    <br>

                    Probability
                    <b style="color:#39E6A2;">
                        {probability:.0f}%
                    </b>
                    <br>

                    Premium
                    <b>
                        {money(premium)}
                    </b>
                    <br><br>

                    <b style="color:#F3C85B;">
                        {recommendation}
                    </b>
                    <br><br>

                    Market Bias
                    <b>{market_bias}</b>
                    <br>

                    Support
                    <b>{price(support)}</b>
                    <br>

                    Resistance
                    <b>{price(resistance)}</b>
                    <br>

                    Max Pain
                    <b>{price(max_pain)}</b>
                </div>
                """
            )

            self.ai_card.body.setText(
                ai_text
            )

            # ------------------------------------------------
            # RISK
            # ------------------------------------------------

            risk = (
                best.get(
                    "risk"
                )
                or {}
            )

            entry = number(
                risk.get(
                    "entry",
                    premium
                )
            )

            sl = number(
                risk.get(
                    "sl"
                )
            )

            target1 = number(
                risk.get(
                    "target1"
                )
            )

            max_loss = number(
                risk.get(
                    "max_loss"
                )
            )

            rr = number(
                risk.get(
                    "rr"
                )
            )

            risk_text = (

                f"""
                <div style="
                    color:#39E6A2;
                    font-size:12px;
                    font-weight:700;
                ">
                    TRADE PLAN
                </div>

                <div style="
                    color:#F7FBFF;
                    font-size:20px;
                    font-weight:750;
                    margin-top:4px;
                ">
                    {strike:,.0f} {option_type}
                </div>

                <div style="
                    margin-top:6px;
                    color:#D8E7F5;
                    font-size:13px;
                    line-height:1.5;
                ">
                    Entry
                    <b>{money(entry)}</b>
                    <br>

                    Stop Loss
                    <b style="color:#FF6570;">
                        {money(sl)}
                    </b>
                    <br>

                    Target 1
                    <b style="color:#39E6A2;">
                        {money(target1)}
                    </b>
                    <br><br>

                    Max Risk
                    <b style="color:#FF6570;">
                        {money(max_loss)}
                    </b>
                    <br>

                    Risk / Reward
                    <b style="color:#39E6A2;">
                        {rr:.2f}
                    </b>
                </div>
                """
            )

            self.risk_card.body.setText(
                risk_text
            )

        else:

            self.ai_card.body.setText(
                """
                <span style="color:#71859B;">
                    No valid AI setup returned.
                </span>
                """
            )

            self.risk_card.body.setText(
                """
                <span style="color:#71859B;">
                    Risk data unavailable.
                </span>
                """
            )

        # ====================================================
        # OI INTELLIGENCE
        # ====================================================

        spot = number(
            result.get(
                "spot"
            )
        )

        calls = []
        puts = []

        for row in rows:

            strike = number(
                row.get(
                    "strike"
                )
            )

            ce = row.get(
                "CE"
            ) or {}

            pe = row.get(
                "PE"
            ) or {}

            ce_oi = number(
                ce.get(
                    "ce_oi"
                )
            )

            pe_oi = number(
                pe.get(
                    "pe_oi"
                )
            )

            if strike >= spot:

                calls.append(
                    (
                        ce_oi,
                        strike
                    )
                )

            if strike <= spot:

                puts.append(
                    (
                        pe_oi,
                        strike
                    )
                )

        calls.sort(
            reverse=True
        )

        puts.sort(
            reverse=True
        )

        text = ""

        # ----------------------------------------------------
        # CALL OI
        # ----------------------------------------------------

        if calls:

            text += (
                """
                <div style="
                    color:#8EDFFF;
                    font-weight:700;
                ">
                    CALL WRITING / OI
                </div>
                """
            )

            for oi, strike in calls[:3]:

                text += (
                    f"""
                    <div style="
                        margin-top:3px;
                    ">
                        {strike:,.0f} CE
                        <b style="color:#F4F8FC;">
                            {compact(oi)}
                        </b>
                    </div>
                    """
                )

        # ----------------------------------------------------
        # PUT OI
        # ----------------------------------------------------

        if puts:

            text += (
                """
                <div style="
                    margin-top:8px;
                    color:#39E6A2;
                    font-weight:700;
                ">
                    PUT SUPPORT / OI
                </div>
                """
            )

            for oi, strike in puts[:3]:

                text += (
                    f"""
                    <div style="
                        margin-top:3px;
                    ">
                        {strike:,.0f} PE
                        <b style="color:#F4F8FC;">
                            {compact(oi)}
                        </b>
                    </div>
                    """
                )

        # ----------------------------------------------------
        # TOTAL OI
        # ----------------------------------------------------

        total_ce_oi = number(
            chain.get(
                "total_ce_oi"
            )
        )

        total_pe_oi = number(
            chain.get(
                "total_pe_oi"
            )
        )

        text += (

            f"""
            <div style="
                margin-top:8px;
                padding-top:6px;
                border-top:1px solid #20364D;
            ">
                Total CE OI
                <b>{compact(total_ce_oi)}</b>
                <br>

                Total PE OI
                <b>{compact(total_pe_oi)}</b>
            </div>
            """
        )

        self.oi_card.body.setText(
            text
        )

    # ========================================================
    # ERROR
    # ========================================================

    def on_error(
        self,
        error_text
    ):

        self.table_status.setText(
            "Option-chain request failed."
        )

        self.ai_card.body.setText(
            "<b style='color:#FF6570;'>"
            "Scan failed"
            "</b><br><br>"
            + error_text
        )

        self.oi_card.body.setText(
            """
            <span style="color:#FF6570;">
                Option-chain intelligence unavailable.
            </span>
            """
        )

        self.risk_card.body.setText(
            """
            <span style="color:#FF6570;">
                Risk calculation unavailable.
            </span>
            """
        )

    # ========================================================
    # WORKER FINISHED
    # ========================================================

    def on_worker_finished(
        self
    ):

        self.refresh_button.setEnabled(
            True
        )

        self.worker = None

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        try:

            if (
                self.worker
                and self.worker.isRunning()
            ):

                self.worker.quit()

                self.worker.wait(
                    3000
                )

        except Exception:

            pass

        event.accept()