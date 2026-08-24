from __future__ import annotations

import traceback
from datetime import datetime

from PySide6.QtCore import (
    QObject,
    QThread,
    QTimer,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui import theme

from engine.market_worker import MarketWorker
from engine.trade_engine import TradeEngine
from engine.option_chain import OptionChain
from engine.option_parser import OptionParser
from data_engine.prediction_tracker import PredictionTracker

from ui.chart_widget import ChartWidget


# ============================================================
# HELPERS
# ============================================================

def number(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def money(value):
    try:
        return f"₹{float(value):,.2f}"
    except Exception:
        return "₹--"


def get_index(result, fallback="NIFTY 50"):
    if not isinstance(result, dict):
        return fallback

    return str(
        result.get("selected_index")
        or result.get("index")
        or fallback
    )


# ============================================================
# CARD
# ============================================================

class Card(QFrame):

    def __init__(
        self,
        title,
        icon="",
        accent=None,
    ):

        super().__init__()

        self.setObjectName(
            "DashboardCard"
        )

        self.setStyleSheet(
            f"""
            QFrame#DashboardCard {{
                background:
                    {getattr(
                        theme,
                        "CARD",
                        "#151A22"
                    )};

                border:
                    1px solid
                    rgba(255,255,255,0.07);

                border-radius:
                    12px;
            }}

            QLabel {{
                background:
                    transparent;

                border:
                    none;
            }}
            """
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            10,
            14,
            12
        )

        layout.setSpacing(
            7
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        header.setSpacing(
            7
        )

        if icon:

            icon_label = QLabel(
                icon
            )

            icon_label.setStyleSheet(
                f"""
                QLabel {{
                    color:
                        {accent or getattr(
                            theme,
                            "PRIMARY",
                            "#1683FF"
                        )};

                    font-size:
                        14px;

                    font-weight:
                        800;
                }}
                """
            )

            header.addWidget(
                icon_label
            )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            QLabel {{
                color:
                    {getattr(
                        theme,
                        "TEXT",
                        "#F5F7FA"
                    )};

                font-family:
                    "{getattr(
                        theme,
                        "FONT",
                        "Segoe UI"
                    )}";

                font-size:
                    15px;

                font-weight:
                    700;
            }}
            """
        )

        header.addWidget(
            title_label
        )

        header.addStretch()

        layout.addLayout(
            header
        )

        # ----------------------------------------------------
        # LINE
        # ----------------------------------------------------

        line = QFrame()

        line.setFixedHeight(
            1
        )

        line.setStyleSheet(
            """
            background:
                rgba(255,255,255,0.06);

            border:
                none;
            """
        )

        layout.addWidget(
            line
        )

        # ----------------------------------------------------
        # BODY
        # ----------------------------------------------------

        self.body = QWidget()

        body_layout = QVBoxLayout(
            self.body
        )

        body_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        body_layout.setSpacing(
            0
        )

        self.text = QLabel()

        self.text.setWordWrap(
            True
        )

        self.text.setAlignment(
            Qt.AlignTop |
            Qt.AlignLeft
        )

        self.text.setStyleSheet(
            f"""
            QLabel {{
                color:
                    {getattr(
                        theme,
                        "TEXT_SECONDARY",
                        "#AEB8C8"
                    )};

                font-family:
                    "{getattr(
                        theme,
                        "FONT",
                        "Segoe UI"
                    )}";

                font-size:
                    12px;
            }}
            """
        )

        body_layout.addWidget(
            self.text
        )

        body_layout.addStretch()

        layout.addWidget(
            self.body,
            1
        )

    def set_text(
        self,
        text
    ):

        self.text.setText(
            str(text)
        )


# ============================================================
# MARKET TICKER
# ============================================================

class MarketTicker(QFrame):

    clicked = Signal(str)

    def __init__(
        self,
        name
    ):

        super().__init__()

        self.name = name
        self.selected = False

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setObjectName(
            "MarketTicker"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            11,
            6,
            11,
            6
        )

        layout.setSpacing(
            1
        )

        self.name_label = QLabel(
            name
        )

        self.value_label = QLabel(
            "--"
        )

        self.change_label = QLabel(
            "--"
        )

        layout.addWidget(
            self.name_label
        )

        layout.addWidget(
            self.value_label
        )

        layout.addWidget(
            self.change_label
        )

        self.update_style()

    def update_style(
        self
    ):

        if self.selected:

            background = "#13243A"
            border = "#1683FF"

        else:

            background = "#151A22"
            border = "rgba(255,255,255,0.07)"

        self.setStyleSheet(
            f"""
            QFrame#MarketTicker {{
                background:
                    {background};

                border:
                    1px solid
                    {border};

                border-radius:
                    10px;
            }}

            QLabel {{
                background:
                    transparent;

                border:
                    none;
            }}
            """
        )

        self.name_label.setStyleSheet(
            """
            QLabel {
                color:#8F9AAF;
                font-size:9px;
                font-weight:700;
            }
            """
        )

        self.value_label.setStyleSheet(
            """
            QLabel {
                color:#F7FAFF;
                font-size:17px;
                font-weight:800;
            }
            """
        )

        self.change_label.setStyleSheet(
            """
            QLabel {
                color:#34D399;
                font-size:10px;
                font-weight:700;
            }
            """
        )

    def set_selected(
        self,
        selected
    ):

        self.selected = bool(
            selected
        )

        self.update_style()

    def update_value(
        self,
        value,
        change="--"
    ):

        self.value_label.setText(
            str(value)
        )

        self.change_label.setText(
            str(change)
        )

        numeric = number(
            str(change)
            .replace(
                "%",
                ""
            )
            .replace(
                "+",
                ""
            )
        )

        if numeric > 0:

            color = "#34D399"

        elif numeric < 0:

            color = "#FF5F57"

        else:

            color = "#8F96A3"

        self.change_label.setStyleSheet(
            f"""
            QLabel {{
                color:
                    {color};

                font-size:
                    10px;

                font-weight:
                    700;
            }}
            """
        )

    def mousePressEvent(
        self,
        event
    ):

        if event.button() == Qt.LeftButton:

            self.clicked.emit(
                self.name
            )

        super().mousePressEvent(
            event
        )


# ============================================================
# AI TRADE PANEL
# ============================================================

class AITradePanel(QWidget):

    track_requested = Signal(dict)

    def __init__(
        self
    ):

        super().__init__()

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            5
        )

        self.summary = QLabel(
            "Generate AI trade to see ranked opportunities."
        )

        self.summary.setStyleSheet(
            """
            QLabel {
                color:#AEB8C8;
                font-size:11px;
                font-weight:500;
                padding:2px 0;
            }
            """
        )

        layout.addWidget(
            self.summary
        )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        self.table = QTableWidget(
            0,
            11
        )

        self.table.setHorizontalHeaderLabels(
            [
                "TRADE",
                "STRIKE",
                "ENTRY",
                "LIVE",
                "SL",
                "TARGET 1",
                "TARGET 2",
                "AI SCORE",
                "PROB.",
                "R:R",
                "ACTION",
            ]
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setShowGrid(
            False
        )

        self.table.setWordWrap(
            False
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        self.table.setStyleSheet(
            """
            QTableWidget {
                background:
                    transparent;

                border:
                    none;

                color:
                    #EAF0FA;

                font-size:
                    11px;

                outline:
                    none;
            }

            QHeaderView::section {
                background:
                    rgba(255,255,255,0.035);

                color:
                    #8490A5;

                border:
                    none;

                border-bottom:
                    1px solid
                    rgba(255,255,255,0.07);

                padding:
                    7px 4px;

                font-size:
                    9px;

                font-weight:
                    800;
            }

            QTableWidget::item {
                padding:
                    6px 4px;

                border-bottom:
                    1px solid
                    rgba(255,255,255,0.045);
            }

            QScrollBar:vertical {
                background:
                    transparent;

                width:
                    5px;
            }

            QScrollBar::handle:vertical {
                background:
                    rgba(255,255,255,0.18);

                border-radius:
                    3px;
            }
            """
        )

        header = (
            self.table.horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            10,
            QHeaderView.ResizeToContents
        )

        self.table.setMinimumHeight(
            205
        )

        layout.addWidget(
            self.table,
            1
        )

    # ========================================================
    # SET TRADES
    # ========================================================

    def set_trades(
        self,
        trades,
        tracked_keys=None
    ):

        tracked_keys = (
            tracked_keys
            or set()
        )

        self.table.setRowCount(
            0
        )

        if not trades:

            self.summary.setText(
                "No suitable AI trade found right now."
            )

            return

        self.summary.setText(
            f"{len(trades)} AI opportunities  •  "
            "Entry / SL / targets remain fixed."
        )

        for row, trade in enumerate(
            trades
        ):

            self.table.insertRow(
                row
            )

            risk = (
                trade.get(
                    "risk"
                )
                or {}
            )

            instrument = trade.get(
                "selected_index",
                "NIFTY 50"
            )

            option_type = str(
                trade.get(
                    "type",
                    ""
                )
            )

            strike = trade.get(
                "strike",
                "--"
            )

            entry = risk.get(
                "entry",
                trade.get(
                    "premium",
                    "--"
                )
            )

            live = trade.get(
                "live_premium",
                trade.get(
                    "premium",
                    entry
                )
            )

            sl = risk.get(
                "sl",
                "--"
            )

            target1 = risk.get(
                "target1",
                "--"
            )

            target2 = risk.get(
                "target2",
                "--"
            )

            score = trade.get(
                "ai_score",
                trade.get(
                    "score",
                    "--"
                )
            )

            probability = trade.get(
                "probability",
                "--"
            )

            rr = risk.get(
                "rr",
                "--"
            )

            key = (
                f"{instrument}|"
                f"{strike}|"
                f"{option_type}"
            )

            values = [
                (
                    f"{trade.get('recommendation', 'WATCH')} "
                    f"{option_type}"
                ),
                str(strike),
                money(entry),
                money(live),
                money(sl),
                money(target1),
                money(target2),
                f"{score}/100",
                f"{probability}%",
                str(rr),
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                if column == 0:

                    item.setTextAlignment(
                        Qt.AlignLeft |
                        Qt.AlignVCenter
                    )

                if (
                    column == 7
                    and number(score) >= 70
                ):

                    item.setForeground(
                        QColor("#F5C84B")
                    )

                if (
                    column == 8
                    and number(probability) >= 70
                ):

                    item.setForeground(
                        QColor("#34D399")
                    )

                self.table.setItem(
                    row,
                    column,
                    item
                )

            # ------------------------------------------------
            # TRACK BUTTON
            # ------------------------------------------------

            already_tracked = (
                key in tracked_keys
            )

            button = QPushButton(
                "TRACKED"
                if already_tracked
                else "TRACK"
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setMinimumHeight(
                26
            )

            button.setEnabled(
                not already_tracked
            )

            button.setStyleSheet(
                """
                QPushButton {
                    background:
                        #176B4D;

                    color:
                        #D9FFF0;

                    border:
                        1px solid
                        #23976C;

                    border-radius:
                        7px;

                    padding:
                        4px 9px;

                    font-size:
                        9px;

                    font-weight:
                        800;
                }

                QPushButton:hover {
                    background:
                        #1D8A63;
                }

                QPushButton:disabled {
                    background:
                        #263A35;

                    color:
                        #80A99B;

                    border:
                        1px solid
                        #35584C;
                }
                """
            )

            button.clicked.connect(
                lambda checked=False,
                selected=dict(trade):
                self.track_requested.emit(
                    selected
                )
            )

            self.table.setCellWidget(
                row,
                10,
                button
            )

            self.table.setRowHeight(
                row,
                35
            )


# ============================================================
# AI GENERATION WORKER
# ============================================================

class TradeGenerationWorker(
    QObject
):

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        engine,
        instrument,
        expiry
    ):

        super().__init__()

        self.engine = engine
        self.instrument = instrument
        self.expiry = expiry

    @Slot()
    def run(self):

        try:

            generate = (
                self.engine
                .generate_trades
            )

            # Latest multi-index engine
            try:

                result = generate(
                    selected_index=
                    self.instrument,

                    expiry=
                    self.expiry
                )

            except TypeError:

                # Compatibility with old
                # NIFTY-only engine.

                if (
                    self.instrument
                    != "NIFTY 50"
                ):

                    raise RuntimeError(
                        "Current TradeEngine does not "
                        "support selected_index. "
                        "Use the multi-index TradeEngine."
                    )

                result = generate()

            if result is None:

                result = {}

            result[
                "selected_index"
            ] = self.instrument

            result[
                "selected_expiry"
            ] = self.expiry

            self.finished.emit(
                result
            )

        except Exception:

            self.failed.emit(
                traceback.format_exc()
            )


# ============================================================
# FAST QUOTE WORKER
# ============================================================

class QuoteWorker(
    QThread
):

    quote_ready = Signal(dict)

    def __init__(
        self,
        option_chain,
        instruments,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.option_chain = (
            option_chain
        )

        self.instruments = list(
            instruments
        )

        self.running = True

        # Network polling is deliberately
        # kept above zero to avoid
        # hammering NSE.
        self.interval_ms = 500

        self.parser = OptionParser()

        self.expiries = {}

    def run(
        self
    ):

        while self.running:

            started = (
                datetime.now()
            )

            snapshots = {}

            for instrument in (
                self.instruments
            ):

                if not self.running:
                    break

                try:

                    expiry = (
                        self.expiries
                        .get(instrument)
                    )

                    if not expiry:

                        try:

                            expiry = (
                                self.option_chain
                                .get_current_expiry(
                                    instrument
                                )
                            )

                        except TypeError:

                            expiry = (
                                self.option_chain
                                .get_current_expiry()
                            )

                        if expiry:

                            self.expiries[
                                instrument
                            ] = expiry

                    data = (
                        self.option_chain
                        .get_chain(
                            symbol=
                            instrument,

                            expiry=
                            expiry
                        )
                    )

                    if not data:
                        continue

                    records = (
                        data.get(
                            "records"
                        )
                        or {}
                    )

                    spot = number(
                        records.get(
                            "underlyingValue"
                        )
                    )

                    rows = []

                    try:

                        rows = (
                            self.parser
                            .parse(
                                data
                            )
                            or []
                        )

                    except Exception:

                        rows = []

                    snapshots[
                        instrument
                    ] = {
                        "spot":
                            spot,

                        "rows":
                            rows,

                        "timestamp":
                            datetime.now()
                            .strftime(
                                "%H:%M:%S.%f"
                            )[:-3],
                    }

                except Exception as exc:

                    print(
                        f"Quote error "
                        f"[{instrument}]: "
                        f"{exc}"
                    )

            if snapshots:

                self.quote_ready.emit(
                    snapshots
                )

            elapsed = int(
                (
                    datetime.now()
                    - started
                ).total_seconds()
                * 1000
            )

            sleep_ms = max(
                25,
                self.interval_ms
                - elapsed
            )

            self.msleep(
                sleep_ms
            )

    def stop(
        self
    ):

        self.running = False

        if self.isRunning():

            self.wait(
                3000
            )


# ============================================================
# DASHBOARD
# ============================================================

class Dashboard(
    QWidget
):

    # --------------------------------------------------------
    # MAIN WINDOW SIGNALS
    # --------------------------------------------------------

    tracking_changed = Signal(
        list
    )

    tracking_page_requested = Signal()

    # --------------------------------------------------------
    # SUPPORTED INDEX
    # --------------------------------------------------------

    SUPPORTED = (
        "NIFTY 50",
        "BANK NIFTY",
        "FINNIFTY",
    )

    # --------------------------------------------------------
    # LOT SIZES
    # --------------------------------------------------------

    LOT_SIZES = {
        "NIFTY 50": 65,
        "BANK NIFTY": 30,
        "FINNIFTY": 60,
    }

    # --------------------------------------------------------
    # UI REFRESH
    # --------------------------------------------------------

    UI_REFRESH_MS = 50

    # --------------------------------------------------------
    # QUOTE REFRESH
    # --------------------------------------------------------

    QUOTE_REFRESH_MS = 500

    def __init__(
        self
    ):

        super().__init__()

        # ====================================================
        # STATE
        # ====================================================

        self.selected_instrument = (
            "NIFTY 50"
        )

        self.selected_expiry = None

        self.current_result = {}

        self.current_trades = []

        # Step 8/11: dedicated option-trade prediction ledger.
        self.prediction_tracker = PredictionTracker()

        self.tracked_trades = []

        self.latest_quotes = {}

        self.trade_report_active = False

        # ====================================================
        # ENGINE
        # ====================================================

        self.trade_engine = (
            TradeEngine()
        )

        self.option_chain = (
            OptionChain()
        )

        self.option_parser = (
            OptionParser()
        )

        # ====================================================
        # STYLE
        # ====================================================

        self.setObjectName(
            "Dashboard"
        )

        self.setStyleSheet(
            f"""
            QWidget#Dashboard {{
                background:
                    {getattr(
                        theme,
                        "BACKGROUND",
                        "#0D1015"
                    )};

                color:
                    {getattr(
                        theme,
                        "TEXT",
                        "#F5F7FA"
                    )};

                font-family:
                    "{getattr(
                        theme,
                        "FONT",
                        "Segoe UI"
                    )}";
            }}
            """
        )

        # ====================================================
        # ROOT
        # ====================================================

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            getattr(
                theme,
                "CONTENT_MARGIN",
                12
            ),
            10,
            getattr(
                theme,
                "CONTENT_MARGIN",
                12
            ),
            10
        )

        root.setSpacing(
            8
        )

        # ====================================================
        # TOP MARKET BAR
        # ====================================================

        top_bar = QHBoxLayout()

        top_bar.setSpacing(
            7
        )

        # ----------------------------------------------------
        # NIFTY
        # ----------------------------------------------------

        self.nifty_ticker = (
            MarketTicker(
                "NIFTY 50"
            )
        )

        # ----------------------------------------------------
        # BANK NIFTY
        # ----------------------------------------------------

        self.bank_ticker = (
            MarketTicker(
                "BANK NIFTY"
            )
        )

        # ----------------------------------------------------
        # FINNIFTY
        # ----------------------------------------------------

        self.finnifty_ticker = (
            MarketTicker(
                "FINNIFTY"
            )
        )

        for ticker in (
            self.nifty_ticker,
            self.bank_ticker,
            self.finnifty_ticker,
        ):

            ticker.clicked.connect(
                self.select_instrument
            )

            top_bar.addWidget(
                ticker
            )

        top_bar.addStretch()

        # ====================================================
        # TOP METRICS
        # ====================================================

        self.dashboard_pnl = (
            self.create_metric(
                top_bar,
                "TODAY'S P&L",
                "₹0.00"
            )
        )

        self.dashboard_trades = (
            self.create_metric(
                top_bar,
                "TRADES TODAY",
                "0"
            )
        )

        self.dashboard_winrate = (
            self.create_metric(
                top_bar,
                "WIN RATE",
                "0%"
            )
        )

        self.dashboard_risk = (
            self.create_metric(
                top_bar,
                "RISK STATUS",
                "● ALLOWED"
            )
        )

        root.addLayout(
            top_bar
        )

        # ====================================================
        # CARDS
        # ====================================================

        self.market_card = Card(
            "Market Overview",
            "•",
            getattr(
                theme,
                "CYAN",
                "#2F9BFF"
            )
        )

        self.chart_card = Card(
            "Live Chart",
            "•",
            getattr(
                theme,
                "PRIMARY",
                "#1683FF"
            )
        )

        self.analysis_card = Card(
            "AI Analysis",
            "✦",
            getattr(
                theme,
                "PURPLE",
                "#A970FF"
            )
        )

        self.option_card = Card(
            "Option Chain",
            "•",
            getattr(
                theme,
                "CYAN",
                "#2F9BFF"
            )
        )

        self.trade_card = Card(
            "AI Trade Opportunities",
            "◎",
            getattr(
                theme,
                "GREEN",
                "#34D399"
            )
        )

        self.risk_card = Card(
            "Risk Manager",
            "⚠",
            getattr(
                theme,
                "ORANGE",
                "#F5B83D"
            )
        )

        # ====================================================
        # AI TRADE TABLE
        # ====================================================

        self.trade_panel = (
            AITradePanel()
        )

        self.trade_panel.track_requested.connect(
            self.track_trade
        )

        self.trade_card.body.layout().addWidget(
            self.trade_panel
        )

        # ====================================================
        # CHART
        # ====================================================

        self.chart = (
            ChartWidget()
        )

        self.chart_card.body.layout().addWidget(
            self.chart,
            1
        )

        self.chart.plot_data(
            []
        )

        # ====================================================
        # GRID
        # ====================================================

        grid = QGridLayout()

        grid.setContentsMargins(
            0,
            0,
            0,
            0
        )

        grid.setHorizontalSpacing(
            8
        )

        grid.setVerticalSpacing(
            8
        )

        grid.addWidget(
            self.market_card,
            0,
            0
        )

        grid.addWidget(
            self.chart_card,
            0,
            1
        )

        grid.addWidget(
            self.analysis_card,
            0,
            2
        )

        grid.addWidget(
            self.option_card,
            1,
            0
        )

        grid.addWidget(
            self.trade_card,
            1,
            1
        )

        grid.addWidget(
            self.risk_card,
            1,
            2
        )

        grid.setColumnStretch(
            0,
            1
        )

        grid.setColumnStretch(
            1,
            2
        )

        grid.setColumnStretch(
            2,
            1
        )

        grid.setRowStretch(
            0,
            1
        )

        grid.setRowStretch(
            1,
            1
        )

        root.addLayout(
            grid,
            1
        )

        # ====================================================
        # INITIAL CONTENT
        # ====================================================

        self.market_card.set_text(
            "Waiting for market data..."
        )

        self.analysis_card.set_text(
            "Waiting for market data..."
        )

        self.option_card.set_text(
            "Loading option chain..."
        )

        self.risk_card.set_text(
            "Risk analysis will appear here."
        )

        self.set_selected_ticker(
            "NIFTY 50"
        )

        # ====================================================
        # MARKET WORKER
        # ====================================================

        self.worker = (
            MarketWorker()
        )

        try:

            self.worker.market_updated.connect(
                self.market_worker_update
            )

        except Exception:
            pass

        try:

            self.worker.chart_updated.connect(
                self.chart.plot_data
            )

        except Exception:
            pass

        try:

            self.chart.timeframe_changed.connect(
                self.worker.set_chart_interval
            )

        except Exception:
            pass

        self.worker.start()

        # ====================================================
        # FAST QUOTE WORKER
        # ====================================================

        self.quote_worker = (
            QuoteWorker(
                self.option_chain,
                self.SUPPORTED,
                self
            )
        )

        self.quote_worker.interval_ms = (
            self.QUOTE_REFRESH_MS
        )

        self.quote_worker.quote_ready.connect(
            self.quote_update
        )

        self.quote_worker.start()

        # ====================================================
        # UI TIMER
        # ====================================================

        self.ui_timer = QTimer(
            self
        )

        self.ui_timer.timeout.connect(
            self.ui_refresh
        )

        self.ui_timer.start(
            self.UI_REFRESH_MS
        )

        # ====================================================
        # METRICS TIMER
        # ====================================================

        self.metrics_timer = QTimer(
            self
        )

        self.metrics_timer.timeout.connect(
            self.refresh_dashboard_metrics
        )

        self.metrics_timer.start(
            1000
        )

        # ====================================================
        # INITIAL OPTION CHAIN
        # ====================================================

        QTimer.singleShot(
            300,
            self.load_selected_chain
        )

        # ====================================================
        # INITIAL AI SCANNER
        # ====================================================

        self.start_scanner(
            "NIFTY 50"
        )

    # =========================================================
    # METRIC
    # =========================================================

    def create_metric(
        self,
        parent,
        title,
        value
    ):

        card = QFrame()

        card.setStyleSheet(
            """
            QFrame {
                background:#151A22;
                border:
                    1px solid
                    rgba(255,255,255,.07);

                border-radius:
                    10px;
            }

            QLabel {
                background:
                    transparent;

                border:
                    none;
            }
            """
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            10,
            6,
            10,
            6
        )

        layout.setSpacing(
            1
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            """
            QLabel {
                color:#7F8BA0;
                font-size:9px;
                font-weight:600;
            }
            """
        )

        value_label = QLabel(
            value
        )

        value_label.setStyleSheet(
            """
            QLabel {
                color:#F5F7FA;
                font-size:15px;
                font-weight:800;
            }
            """
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        parent.addWidget(
            card
        )

        return value_label

    # =========================================================
    # SELECTED TICKER
    # =========================================================

    def set_selected_ticker(
        self,
        instrument
    ):

        for ticker in (
            self.nifty_ticker,
            self.bank_ticker,
            self.finnifty_ticker,
        ):

            ticker.set_selected(
                ticker.name
                == instrument
            )

    # =========================================================
    # SELECT INSTRUMENT
    # =========================================================

    def select_instrument(
        self,
        instrument
    ):

        if instrument not in (
            self.SUPPORTED
        ):

            return

        if (
            instrument
            == self.selected_instrument
        ):

            return

        self.selected_instrument = (
            instrument
        )

        self.selected_expiry = None

        self.current_result = {}

        self.current_trades = []

        self.set_selected_ticker(
            instrument
        )

        # IMPORTANT:
        # tracked_trades is NOT touched here.

        self.trade_panel.set_trades(
            []
        )

        self.market_card.set_text(
            f"{instrument}\n\n"
            "Loading market..."
        )

        self.analysis_card.set_text(
            "Loading technical analysis..."
        )

        self.option_card.set_text(
            "Loading option chain..."
        )

        self.risk_card.set_text(
            "Loading risk analysis..."
        )

        # Try to tell MarketWorker
        # about selected instrument.

        try:

            if hasattr(
                self.worker,
                "set_index"
            ):

                self.worker.set_index(
                    instrument
                )

        except Exception:
            pass

        self.restart_scanner(
            instrument
        )

        self.load_selected_chain()

    # =========================================================
    # START SCANNER
    # =========================================================

    def start_scanner(
        self,
        instrument
    ):

        try:

            from engine.scanner_worker import (
                ScannerWorker
            )

            self.scanner = (
                ScannerWorker()
            )

            if hasattr(
                self.scanner,
                "set_index"
            ):

                self.scanner.set_index(
                    instrument
                )

            else:

                self.scanner.selected_index = (
                    instrument
                )

            if hasattr(
                self.scanner,
                "scan_completed"
            ):

                self.scanner.scan_completed.connect(
                    self.live_trade_update
                )

            if hasattr(
                self.scanner,
                "scan_error"
            ):

                self.scanner.scan_error.connect(
                    lambda msg:
                    print(
                        "Scanner:",
                        msg
                    )
                )

            if hasattr(
                self.scanner,
                "error"
            ):

                self.scanner.error.connect(
                    lambda msg:
                    print(
                        "Scanner:",
                        msg
                    )
                )

            self.scanner.start()

        except Exception:

            self.scanner = None

            print(
                traceback.format_exc()
            )

    # =========================================================
    # STOP SCANNER
    # =========================================================

    def stop_scanner(
        self
    ):

        scanner = getattr(
            self,
            "scanner",
            None
        )

        if scanner is None:
            return

        try:

            if scanner.isRunning():

                if hasattr(
                    scanner,
                    "stop"
                ):

                    scanner.stop()

                else:

                    scanner.quit()

                    scanner.wait(
                        3000
                    )

        except Exception as exc:

            print(
                "Scanner stop:",
                exc
            )

    # =========================================================
    # RESTART SCANNER
    # =========================================================

    def restart_scanner(
        self,
        instrument
    ):

        self.stop_scanner()

        self.start_scanner(
            instrument
        )

    # =========================================================
    # MARKET WORKER
    # =========================================================

    def market_worker_update(
        self,
        data
    ):

        if not isinstance(
            data,
            dict
        ):

            return

        index = str(
            data.get(
                "selected_index"
            )
            or data.get(
                "index"
            )
            or ""
        )

        # Old MarketWorker is NIFTY-only.
        # Never let NIFTY overwrite BANK/FINNIFTY.

        if (
            not index
            and self.selected_instrument
            != "NIFTY 50"
        ):

            self.update_ticker(
                "NIFTY 50",
                data
            )

            return

        if not index:

            index = "NIFTY 50"

        self.update_ticker(
            index,
            data
        )

        if (
            index
            == self.selected_instrument
        ):

            self.render_market(
                data,
                index
            )

    # =========================================================
    # UPDATE TICKER
    # =========================================================

    def update_ticker(
        self,
        index,
        data
    ):

        price = number(
            data.get(
                "price"
            )
        )

        if price <= 0:
            return

        change = data.get(
            "change_percent",
            data.get(
                "change"
            )
        )

        if change is None:

            change_text = "--"

        else:

            change_text = (
                f"{number(change):+.2f}%"
            )

        ticker_map = {
            "NIFTY 50":
                self.nifty_ticker,

            "BANK NIFTY":
                self.bank_ticker,

            "FINNIFTY":
                self.finnifty_ticker,
        }

        ticker = (
            ticker_map.get(
                index
            )
        )

        if ticker:

            ticker.update_value(
                f"{price:,.2f}",
                change_text
            )

    # =========================================================
    # MARKET CARD
    # =========================================================

    def render_market(
        self,
        data,
        index
    ):

        price = number(
            data.get(
                "price"
            )
        )

        self.market_card.set_text(
            f"{index}\n\n"
            f"{money(price)}\n"
            f"• {data.get('trend','N/A')}\n\n"
            f"Bull        "
            f"{data.get('bull_probability','N/A')}%\n"
            f"Bear        "
            f"{data.get('bear_probability','N/A')}%\n"
            f"Strength    "
            f"{data.get('strength','N/A')}\n"
            f"Volatility  "
            f"{data.get('volatility','N/A')}\n"
            f"Sideways    "
            f"{data.get('sideways_probability','N/A')}%"
        )

        self.render_analysis(
            data
        )

    # =========================================================
    # AI ANALYSIS
    # =========================================================

    def render_analysis(
        self,
        data
    ):

        text = (
            "TECHNICAL SNAPSHOT\n\n"

            f"EMA20       "
            f"{data.get('ema20','N/A')}\n"

            f"EMA50       "
            f"{data.get('ema50','N/A')}\n"

            f"EMA200      "
            f"{data.get('ema200','N/A')}\n\n"

            f"RSI         "
            f"{data.get('rsi','N/A')}\n"

            f"MACD        "
            f"{data.get('macd','N/A')}\n"

            f"Signal      "
            f"{data.get('signal','N/A')}\n"

            f"Histogram   "
            f"{data.get('histogram','N/A')}\n\n"

            f"VWAP        "
            f"{data.get('vwap','N/A')}\n"

            f"ATR         "
            f"{data.get('atr','N/A')}\n"

            f"Volume      "
            f"{data.get('volume','N/A')}"
        )

        patterns = (
            data.get(
                "patterns"
            )
        )

        if patterns:

            text += (
                "\n\n"
                "CANDLE PATTERNS\n"
            )

            pattern_list = (
                patterns.get(
                    "patterns",
                    []
                )
            )

            if pattern_list:

                for pattern in (
                    pattern_list
                ):

                    text += (
                        f"\n• "
                        f"{pattern}"
                    )

            else:

                text += (
                    "\nNo strong pattern"
                )

            text += (
                "\n\nConfidence: "
                f"{patterns.get('confidence',0)}%"
            )

        self.analysis_card.set_text(
            text
        )

    # =========================================================
    # QUOTE UPDATE
    # =========================================================

    def quote_update(
        self,
        snapshots
    ):

        if not snapshots:
            return

        self.latest_quotes.update(
            snapshots
        )

        ticker_map = {
            "NIFTY 50":
                self.nifty_ticker,

            "BANK NIFTY":
                self.bank_ticker,

            "FINNIFTY":
                self.finnifty_ticker,
        }

        for instrument, snapshot in (
            snapshots.items()
        ):

            spot = number(
                snapshot.get(
                    "spot"
                )
            )

            ticker = (
                ticker_map.get(
                    instrument
                )
            )

            if ticker and spot > 0:

                ticker.update_value(
                    f"{spot:,.2f}",
                    "--"
                )

        selected = (
            snapshots.get(
                self.selected_instrument
            )
        )

        if selected:

            self.render_option_snapshot(
                self.selected_instrument,
                selected
            )

        self.update_current_trade_prices()

        # Step 8/11: resolve dedicated option-trade predictions
        # against the same live NSE option-chain snapshot.
        try:
            for instrument, snapshot in (
                snapshots.items()
            ):
                option_rows = (
                    snapshot.get("rows")
                    or []
                )

                if not option_rows:
                    continue

                self.prediction_tracker.update_market_snapshot(
                    instrument,
                    option_rows,
                )

        except Exception as exc:
            print(
                "[PREDICTION-TRACKER] Outcome update error:",
                exc,
            )

        self.update_tracked_prices()

    # =========================================================
    # OPTION SNAPSHOT
    # =========================================================

    def render_option_snapshot(
        self,
        instrument,
        snapshot
    ):

        spot = number(
            snapshot.get(
                "spot"
            )
        )

        rows = (
            snapshot.get(
                "rows"
            )
            or []
        )

        if not rows:

            self.option_card.set_text(
                f"{instrument}\n\n"
                f"SPOT       "
                f"{money(spot)}\n\n"
                "Waiting for option chain..."
            )

            return

        try:

            analysis = (
                self.trade_engine
                .chain_ai
                .analyze(
                    rows
                )
                or {}
            )

        except Exception:

            analysis = {}

        self.option_card.set_text(
            f"{instrument}\n\n"

            f"SPOT        "
            f"{money(spot)}\n"

            f"PCR         "
            f"{analysis.get('pcr','N/A')}\n"

            f"BIAS        "
            f"{analysis.get('bias','N/A')}\n"

            f"SUPPORT     "
            f"{analysis.get('support','N/A')}\n"

            f"RESISTANCE  "
            f"{analysis.get('resistance','N/A')}\n"

            f"MAX PAIN    "
            f"{analysis.get('max_pain','N/A')}\n\n"

            f"CE OI       "
            f"{number(analysis.get('total_ce_oi')):,.0f}\n"

            f"PE OI       "
            f"{number(analysis.get('total_pe_oi')):,.0f}\n"

            f"CE VOLUME   "
            f"{number(analysis.get('total_ce_volume')):,.0f}\n"

            f"PE VOLUME   "
            f"{number(analysis.get('total_pe_volume')):,.0f}"
        )

    # =========================================================
    # LOAD SELECTED CHAIN
    # =========================================================

    def load_selected_chain(
        self
    ):

        try:

            try:

                expiry = (
                    self.option_chain
                    .get_current_expiry(
                        self.selected_instrument
                    )
                )

            except TypeError:

                expiry = (
                    self.option_chain
                    .get_current_expiry()
                )

            self.selected_expiry = (
                expiry
            )

            data = (
                self.option_chain
                .get_chain(
                    symbol=
                    self.selected_instrument,

                    expiry=
                    expiry
                )
            )

            if not data:
                return

            records = (
                data.get(
                    "records"
                )
                or {}
            )

            rows = (
                self.option_parser
                .parse(
                    data
                )
                or []
            )

            self.render_option_snapshot(
                self.selected_instrument,
                {
                    "spot":
                        number(
                            records.get(
                                "underlyingValue"
                            )
                        ),

                    "rows":
                        rows,
                }
            )

        except Exception as exc:

            print(
                "Selected chain error:",
                exc
            )

    # =========================================================
    # LIVE AI SCANNER
    # =========================================================

    def live_trade_update(
        self,
        result
    ):

        try:

            if not result:
                return

            index = get_index(
                result,
                self.selected_instrument
            )

            if (
                index
                != self.selected_instrument
            ):

                return

            self.current_result = (
                result
            )

            trades = (
                result.get(
                    "trades"
                )
                or []
            )

            self.current_trades = (
                trades
            )

            for trade in (
                self.current_trades
            ):

                trade[
                    "selected_index"
                ] = index

                # IMPORTANT:
                # AI entry is fixed.
                trade.setdefault(
                    "live_premium",
                    trade.get(
                        "premium"
                    )
                )

            self.update_current_trade_prices()

            self.trade_panel.set_trades(
                self.current_trades,
                self.tracked_keys()
            )

            self.render_result(
                result
            )

        except Exception:

            print(
                traceback.format_exc()
            )

    # =========================================================
    # RENDER AI RESULT
    # =========================================================

    def render_result(
        self,
        result
    ):

        instrument = get_index(
            result,
            self.selected_instrument
        )

        spot = number(
            result.get(
                "spot"
            )
        )

        market = (
            result.get(
                "market"
            )
            or {}
        )

        confidence = (
            result.get(
                "confidence",
                "N/A"
            )
        )

        direction = (
            result.get(
                "direction",
                "N/A"
            )
        )

        self.market_card.set_text(
            f"{instrument}\n\n"

            f"{money(spot)}\n"

            f"• "
            f"{market.get('trend', direction)}\n\n"

            f"Confidence  "
            f"{confidence}%\n"

            f"Bull        "
            f"{market.get('bull_probability','N/A')}%\n"

            f"Bear        "
            f"{market.get('bear_probability','N/A')}%\n"

            f"Strength    "
            f"{market.get('strength','N/A')}\n"

            f"Volatility  "
            f"{market.get('volatility','N/A')}"
        )

        self.render_analysis(
            {
                **market,
                "patterns":
                    result.get(
                        "patterns"
                    )
            }
        )

        chain = (
            result.get(
                "chain"
            )
            or {}
        )

        self.option_card.set_text(
            f"{instrument}\n\n"

            f"SPOT        "
            f"{money(spot)}\n"

            f"PCR         "
            f"{chain.get('pcr','N/A')}\n"

            f"BIAS        "
            f"{chain.get('bias','N/A')}\n"

            f"SUPPORT     "
            f"{chain.get('support','N/A')}\n"

            f"RESISTANCE  "
            f"{chain.get('resistance','N/A')}\n"

            f"MAX PAIN    "
            f"{chain.get('max_pain','N/A')}\n\n"

            f"CE OI       "
            f"{number(chain.get('total_ce_oi')):,.0f}\n"

            f"PE OI       "
            f"{number(chain.get('total_pe_oi')):,.0f}"
        )

        sr = (
            result.get(
                "support_resistance"
            )
            or {}
        )

        vp = (
            result.get(
                "volume_profile"
            )
            or {}
        )

        self.risk_card.set_text(
            f"STATUS       ALLOWED\n\n"

            f"SUPPORT      "
            f"{sr.get('support', chain.get('support','N/A'))}\n"

            f"RESISTANCE   "
            f"{sr.get('resistance', chain.get('resistance','N/A'))}\n"

            f"PCR          "
            f"{sr.get('pcr', chain.get('pcr','N/A'))}\n"

            f"MAX PAIN     "
            f"{sr.get('max_pain', chain.get('max_pain','N/A'))}\n\n"

            f"POC          "
            f"{vp.get('poc','N/A')}\n"

            f"VAH          "
            f"{vp.get('vah','N/A')}\n"

            f"VAL          "
            f"{vp.get('val','N/A')}\n\n"

            f"Tracked      "
            f"{len(self.tracked_trades)}"
        )

    # =========================================================
    # UPDATE CURRENT AI TRADE LIVE PREMIUM
    # =========================================================

    def update_current_trade_prices(
        self
    ):

        snapshot = (
            self.latest_quotes.get(
                self.selected_instrument
            )
        )

        if not snapshot:
            return

        rows = (
            snapshot.get(
                "rows"
            )
            or []
        )

        by_strike = {
            row.get("strike"):
                row
            for row in rows
        }

        changed = False

        for trade in (
            self.current_trades
        ):

            row = (
                by_strike.get(
                    trade.get(
                        "strike"
                    )
                )
            )

            if not row:
                continue

            option_type = (
                trade.get(
                    "type"
                )
            )

            if option_type == "PE":

                live = row.get(
                    "pe_ltp"
                )

            else:

                live = row.get(
                    "ce_ltp"
                )

            if live is None:
                continue

            old = (
                trade.get(
                    "live_premium"
                )
            )

            trade[
                "live_premium"
            ] = number(
                live,
                old or number(
                    trade.get(
                        "premium"
                    )
                )
            )

            if (
                old
                != trade[
                    "live_premium"
                ]
            ):

                changed = True

        if changed:

            self.trade_panel.set_trades(
                self.current_trades,
                self.tracked_keys()
            )

    # =========================================================
    # GENERATE AI TRADE
    # =========================================================

    def generate_trade(
        self
    ):

        if self.trade_report_active:
            return

        self.trade_report_active = (
            True
        )

        self.trade_panel.summary.setText(
            f"AI is analysing "
            f"{self.selected_instrument}: "
            "momentum, option chain, "
            "patterns, SMC and risk..."
        )

        self.trade_panel.table.setRowCount(
            0
        )

        expiry = (
            self.selected_expiry
        )

        if expiry is None:

            try:

                expiry = (
                    self.option_chain
                    .get_current_expiry(
                        self.selected_instrument
                    )
                )

            except TypeError:

                expiry = (
                    self.option_chain
                    .get_current_expiry()
                )

            self.selected_expiry = (
                expiry
            )

        self.generate_thread = (
            QThread(
                self
            )
        )

        self.generate_worker = (
            TradeGenerationWorker(
                self.trade_engine,
                self.selected_instrument,
                expiry
            )
        )

        self.generate_worker.moveToThread(
            self.generate_thread
        )

        self.generate_thread.started.connect(
            self.generate_worker.run
        )

        self.generate_worker.finished.connect(
            self.generation_finished
        )

        self.generate_worker.failed.connect(
            self.generation_failed
        )

        self.generate_worker.finished.connect(
            self.generate_thread.quit
        )

        self.generate_worker.failed.connect(
            self.generate_thread.quit
        )

        self.generate_thread.finished.connect(
            self.generate_worker.deleteLater
        )

        self.generate_thread.finished.connect(
            self.generate_thread.deleteLater
        )

        self.generate_thread.start()

    # =========================================================
    # GENERATION FINISHED
    # =========================================================

    def generation_finished(
        self,
        result
    ):

        self.trade_report_active = (
            False
        )

        if not result:
            return

        self.current_result = (
            result
        )

        self.current_result[
            "selected_index"
        ] = (
            self.selected_instrument
        )

        trades = (
            result.get(
                "trades"
            )
            or []
        )

        self.current_trades = (
            trades
        )

        for trade in (
            self.current_trades
        ):

            trade[
                "selected_index"
            ] = (
                self.selected_instrument
            )

            # ------------------------------------------------
            # DO NOT CHANGE ENTRY
            # ------------------------------------------------

            trade.setdefault(
                "live_premium",
                trade.get(
                    "premium"
                )
            )

        self.update_current_trade_prices()

        self.trade_panel.set_trades(
            self.current_trades,
            self.tracked_keys()
        )

        self.render_result(
            result
        )

        # Step 8: freeze every generated option trade in the dedicated
        # trade prediction ledger for later live outcome tracking.
        try:
            self.prediction_tracker.record_generation(
                result
            )
        except Exception as exc:
            print(
                "[PREDICTION-TRACKER] Record generation error:",
                exc,
            )

    # =========================================================
    # GENERATION ERROR
    # =========================================================

    def generation_failed(
        self,
        error
    ):

        self.trade_report_active = (
            False
        )

        self.trade_panel.summary.setText(
            "AI trade generation failed. "
            "Check console."
        )

        print(
            error
        )

    # =========================================================
    # TRACKED KEYS
    # =========================================================

    def tracked_keys(
        self
    ):

        return {
            (
                f"{trade.get('instrument')}"
                f"|{trade.get('strike')}"
                f"|{trade.get('type')}"
            )

            for trade in (
                self.tracked_trades
            )
        }

    # =========================================================
    # TRACK TRADE
    # =========================================================

    def track_trade(
        self,
        trade
    ):

        instrument = (
            trade.get(
                "selected_index",
                self.selected_instrument
            )
        )

        strike = (
            trade.get(
                "strike"
            )
        )

        option_type = (
            trade.get(
                "type"
            )
        )

        key = (
            f"{instrument}|"
            f"{strike}|"
            f"{option_type}"
        )

        # ----------------------------------------------------
        # DUPLICATE
        # ----------------------------------------------------

        for existing in (
            self.tracked_trades
        ):

            if (
                existing.get(
                    "key"
                )
                == key
            ):

                self.tracking_page_requested.emit()

                return

        risk = (
            trade.get(
                "risk"
            )
            or {}
        )

        # ====================================================
        # FREEZE ENTRY
        # ====================================================

        entry = number(
            risk.get(
                "entry",
                trade.get(
                    "premium"
                )
            )
        )

        # ====================================================
        # FREEZE SL
        # ====================================================

        sl = number(
            risk.get(
                "sl"
            )
        )

        # ====================================================
        # FREEZE TARGET 1
        # ====================================================

        target1 = number(
            risk.get(
                "target1"
            )
        )

        # ====================================================
        # FREEZE TARGET 2
        # ====================================================

        target2 = number(
            risk.get(
                "target2",
                target1
            )
        )

        live = number(
            trade.get(
                "live_premium",
                trade.get(
                    "premium"
                )
            ),
            entry
        )

        quantity = int(
            self.LOT_SIZES.get(
                instrument,
                1
            )
        )

        tracked = {

            "key":
                key,

            "instrument":
                instrument,

            "index":
                instrument,

            "strike":
                strike,

            "type":
                option_type,

            "entry":
                entry,

            "ltp":
                live,

            "sl":
                sl,

            "target1":
                target1,

            "target2":
                target2,

            "ai_score":
                trade.get(
                    "ai_score",
                    "--"
                ),

            "probability":
                trade.get(
                    "probability",
                    "--"
                ),

            "status":
                "LIVE",

            # NIFTY = 65
            "quantity":
                quantity,

            "lot_size":
                quantity,

            "pnl_per_point":
                live - entry,

            "total_pnl":
                (
                    live - entry
                )
                * quantity,

            "updated":
                datetime.now()
                .strftime(
                    "%H:%M:%S.%f"
                )[:-3],
        }

        self.tracked_trades.append(
            tracked
        )

        # ====================================================
        # SEND TO TRACKING PAGE
        # ====================================================

        self.tracking_changed.emit(
            [
                dict(
                    trade
                )

                for trade in (
                    self.tracked_trades
                )
            ]
        )

        # Update dashboard table
        self.trade_panel.set_trades(
            self.current_trades,
            self.tracked_keys()
        )

        self.refresh_dashboard_metrics()

        # ====================================================
        # OPEN TRACKING PAGE
        # ====================================================

        self.tracking_page_requested.emit()

    # =========================================================
    # UPDATE TRACKED PRICES
    # =========================================================

    def update_tracked_prices(
        self
    ):

        if not self.tracked_trades:
            return

        changed = False

        for trade in (
            self.tracked_trades
        ):

            # Terminal trades remain visible
            # but are no longer modified.

            if trade.get(
                "status"
            ) in (
                "TARGET 2 HIT",
                "STOP LOSS HIT"
            ):

                continue

            instrument = (
                trade.get(
                    "instrument",
                    "NIFTY 50"
                )
            )

            snapshot = (
                self.latest_quotes.get(
                    instrument
                )
            )

            if not snapshot:
                continue

            rows = (
                snapshot.get(
                    "rows"
                )
                or []
            )

            by_strike = {
                row.get(
                    "strike"
                ):
                    row

                for row in rows
            }

            row = (
                by_strike.get(
                    trade.get(
                        "strike"
                    )
                )
            )

            if not row:
                continue

            if (
                trade.get(
                    "type"
                )
                == "PE"
            ):

                ltp = row.get(
                    "pe_ltp"
                )

            else:

                ltp = row.get(
                    "ce_ltp"
                )

            if ltp is None:
                continue

            ltp = number(
                ltp,
                trade.get(
                    "ltp",
                    trade.get(
                        "entry",
                        0
                    )
                )
            )

            # =================================================
            # LIVE PRICE ONLY
            # =================================================

            trade[
                "ltp"
            ] = ltp

            entry = number(
                trade.get(
                    "entry"
                )
            )

            quantity = int(
                trade.get(
                    "quantity",
                    self.LOT_SIZES.get(
                        instrument,
                        1
                    )
                )
            )

            # =================================================
            # P&L PER POINT
            # =================================================

            pnl_per_point = (
                ltp - entry
            )

            trade[
                "pnl_per_point"
            ] = pnl_per_point

            # =================================================
            # TOTAL P&L
            #
            # NIFTY:
            # 1 point = ₹65
            # =================================================

            trade[
                "total_pnl"
            ] = (
                pnl_per_point
                * quantity
            )

            trade[
                "updated"
            ] = (
                datetime.now()
                .strftime(
                    "%H:%M:%S.%f"
                )[:-3]
            )

            # =================================================
            # TARGET 2
            # =================================================

            if (
                trade.get(
                    "target2",
                    0
                ) > 0

                and

                ltp >= trade[
                    "target2"
                ]
            ):

                trade[
                    "status"
                ] = (
                    "TARGET 2 HIT"
                )

            # =================================================
            # TARGET 1
            # =================================================

            elif (
                trade.get(
                    "target1",
                    0
                ) > 0

                and

                ltp >= trade[
                    "target1"
                ]
            ):

                trade[
                    "status"
                ] = (
                    "TARGET 1 HIT"
                )

            # =================================================
            # STOP LOSS
            # =================================================

            elif (
                trade.get(
                    "sl",
                    0
                ) > 0

                and

                ltp <= trade[
                    "sl"
                ]
            ):

                trade[
                    "status"
                ] = (
                    "STOP LOSS HIT"
                )

            changed = True

        if changed:

            self.tracking_changed.emit(
                [
                    dict(
                        trade
                    )

                    for trade in (
                        self.tracked_trades
                    )
                ]
            )

            self.refresh_dashboard_metrics()

    # =========================================================
    # UI REFRESH
    # =========================================================

    def ui_refresh(
        self
    ):

        # 50ms UI refresh.
        #
        # This does NOT regenerate AI trades.
        #
        # This does NOT change entry.
        #
        # It only keeps displayed LIVE values
        # synchronized with the latest quote cache.

        if self.current_trades:

            self.update_current_trade_prices()

    # =========================================================
    # DASHBOARD METRICS
    # =========================================================

    def refresh_dashboard_metrics(
        self
    ):

        try:

            total_pnl = sum(
                number(
                    trade.get(
                        "total_pnl"
                    )
                )

                for trade in (
                    self.tracked_trades
                )
            )

            # ------------------------------------------------
            # P&L
            # ------------------------------------------------

            self.dashboard_pnl.setText(
                (
                    "+"
                    if total_pnl >= 0
                    else "-"
                )
                + "₹"
                + f"{abs(total_pnl):,.2f}"
            )

            self.dashboard_pnl.setStyleSheet(
                f"""
                QLabel {{
                    color:
                        {
                            '#34D399'
                            if total_pnl >= 0
                            else '#FF5F57'
                        };

                    font-size:
                        15px;

                    font-weight:
                        800;

                    background:
                        transparent;

                    border:
                        none;
                }}
                """
            )

            # ------------------------------------------------
            # TRACKED TRADES
            # ------------------------------------------------

            self.dashboard_trades.setText(
                str(
                    len(
                        self.tracked_trades
                    )
                )
            )

            # ------------------------------------------------
            # WIN RATE
            # ------------------------------------------------

            closed = [
                trade

                for trade in (
                    self.tracked_trades
                )

                if trade.get(
                    "status"
                ) in (
                    "TARGET 1 HIT",
                    "TARGET 2 HIT",
                    "STOP LOSS HIT",
                )
            ]

            if closed:

                wins = sum(
                    1

                    for trade in (
                        closed
                    )

                    if "TARGET"
                    in str(
                        trade.get(
                            "status"
                        )
                    )
                )

                winrate = (
                    wins
                    / len(
                        closed
                    )
                    * 100
                )

            else:

                winrate = 0

            self.dashboard_winrate.setText(
                f"{winrate:.0f}%"
            )

            # ------------------------------------------------
            # RISK
            # ------------------------------------------------

            self.dashboard_risk.setText(
                "● ALLOWED"
            )

            self.dashboard_risk.setStyleSheet(
                """
                QLabel {
                    color:#34D399;
                    font-size:15px;
                    font-weight:800;
                    background:transparent;
                    border:none;
                }
                """
            )

            # ------------------------------------------------
            # RISK CARD
            # ------------------------------------------------

            self.risk_card.text.setText(
                f"STATUS       ALLOWED\n\n"

                f"Tracked      "
                f"{len(self.tracked_trades)}\n\n"

                f"Live P&L     "
                f"{'+' if total_pnl >= 0 else '-'}"
                f"₹{abs(total_pnl):,.2f}\n\n"

                f"Selected     "
                f"{self.selected_instrument}"
            )

        except Exception:

            print(
                "Dashboard metrics error:",
                traceback.format_exc()
            )

    # =========================================================
    # SHOW EVENT
    # =========================================================

    def showEvent(
        self,
        event
    ):

        super().showEvent(
            event
        )

        self.refresh_dashboard_metrics()

    # =========================================================
    # STOP
    # =========================================================

    def stop(
        self
    ):

        # -----------------------------------------------------
        # TIMERS
        # -----------------------------------------------------

        for timer_name in (
            "ui_timer",
            "metrics_timer",
        ):

            timer = getattr(
                self,
                timer_name,
                None
            )

            if timer:

                timer.stop()

        # -----------------------------------------------------
        # QUOTE WORKER
        # -----------------------------------------------------

        try:

            if hasattr(
                self,
                "quote_worker"
            ):

                self.quote_worker.stop()

        except Exception:

            pass

        # -----------------------------------------------------
        # MARKET WORKER
        # -----------------------------------------------------

        try:

            if (
                hasattr(
                    self,
                    "worker"
                )

                and

                self.worker.isRunning()
            ):

                self.worker.stop()

                self.worker.wait(
                    3000
                )

        except Exception:

            pass

        # -----------------------------------------------------
        # SCANNER
        # -----------------------------------------------------

        self.stop_scanner()

        # -----------------------------------------------------
        # AI GENERATION THREAD
        # -----------------------------------------------------

        try:

            thread = getattr(
                self,
                "generate_thread",
                None
            )

            if (
                thread
                and
                thread.isRunning()
            ):

                thread.quit()

                thread.wait(
                    3000
                )

        except Exception:

            pass