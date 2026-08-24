from __future__ import annotations

import traceback
import pandas as pd
from datetime import datetime
from uuid import uuid4

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
    QProgressBar,
)

from ui import theme

from engine.market_worker import MarketWorker
from engine.trade_engine import TradeEngine
from engine.option_chain import OptionChain
from engine.option_parser import OptionParser
from data_engine.prediction_tracker import PredictionTracker

from ui.chart_widget import ChartWidget

from ui.trade_store import (
    load_tracked_trades,
    save_tracked_trades,
)


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
# MARKET OVERVIEW WIDGET
# ============================================================

class MarketOverviewWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("MarketOverviewWidget")

        self.setStyleSheet("""
            QWidget#MarketOverviewWidget {
                background: transparent;
            }

            QLabel {
                background: transparent;
                border: none;
            }

            QFrame#MetricBox {
                background: rgba(255,255,255,0.025);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 9px;
            }

            QProgressBar {
                background: #242B35;
                border: none;
                border-radius: 5px;
                height: 8px;
                text-align: center;
            }

            QProgressBar::chunk {
                border-radius: 5px;
            }
        """)

        main = QVBoxLayout(self)

        main.setContentsMargins(
            0,
            2,
            0,
            0
        )

        main.setSpacing(10)

        # ====================================================
        # TOP SECTION
        # ====================================================

        top = QHBoxLayout()
        top.setSpacing(12)

        # ----------------------------------------------------
        # PRICE AREA
        # ----------------------------------------------------

        price_box = QVBoxLayout()
        price_box.setSpacing(2)

        self.instrument_label = QLabel("NIFTY 50")

        self.instrument_label.setStyleSheet("""
            QLabel {
                color: #AEB8C8;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        price_box.addWidget(
            self.instrument_label
        )

        self.price_label = QLabel("--")

        self.price_label.setStyleSheet("""
            QLabel {
                color: #F5F7FA;
                font-size: 28px;
                font-weight: 800;
            }
        """)

        price_box.addWidget(
            self.price_label
        )

        self.change_label = QLabel("")

        self.change_label.setStyleSheet("""
            QLabel {
                color: #8F96A3;
                font-size: 11px;
                font-weight: 700;
            }
        """)

        price_box.addWidget(
            self.change_label
        )

        self.trend_label = QLabel("• Waiting")

        self.trend_label.setStyleSheet("""
            QLabel {
                color: #1683FF;
                font-size: 12px;
                font-weight: 700;
                padding-top: 4px;
            }
        """)

        price_box.addWidget(
            self.trend_label
        )

        top.addLayout(
            price_box,
            1
        )

        # ----------------------------------------------------
        # SENTIMENT SUMMARY
        # ----------------------------------------------------

        sentiment_box = QFrame()

        sentiment_box.setObjectName(
            "MetricBox"
        )

        sentiment_layout = QVBoxLayout(
            sentiment_box
        )

        sentiment_layout.setContentsMargins(
            10,
            8,
            10,
            8
        )

        sentiment_layout.setSpacing(5)

        sentiment_title = QLabel(
            "MARKET SENTIMENT"
        )

        sentiment_title.setStyleSheet("""
            QLabel {
                color: #8F9AAF;
                font-size: 9px;
                font-weight: 800;
                letter-spacing: 1px;
            }
        """)

        sentiment_layout.addWidget(
            sentiment_title
        )

        self.sentiment_label = QLabel(
            "SIDEWAYS"
        )

        self.sentiment_label.setStyleSheet("""
            QLabel {
                color: #1683FF;
                font-size: 17px;
                font-weight: 800;
            }
        """)

        sentiment_layout.addWidget(
            self.sentiment_label
        )

        top.addWidget(
            sentiment_box,
            1
        )

        main.addLayout(
            top
        )

        # ====================================================
        # BULL / BEAR
        # ====================================================

        sentiment_frame = QFrame()

        sentiment_frame.setObjectName(
            "MetricBox"
        )

        sentiment_layout = QVBoxLayout(
            sentiment_frame
        )

        sentiment_layout.setContentsMargins(
            10,
            8,
            10,
            8
        )

        sentiment_layout.setSpacing(6)

        # ---------------- BULL ----------------

        bull_row = QHBoxLayout()

        self.bull_title = QLabel(
            "BULLISH"
        )

        self.bull_title.setStyleSheet("""
            QLabel {
                color: #34D399;
                font-size: 10px;
                font-weight: 800;
            }
        """)

        bull_row.addWidget(
            self.bull_title
        )

        bull_row.addStretch()

        self.bull_value = QLabel(
            "0%"
        )

        self.bull_value.setStyleSheet("""
            QLabel {
                color: #34D399;
                font-size: 11px;
                font-weight: 800;
            }
        """)

        bull_row.addWidget(
            self.bull_value
        )

        sentiment_layout.addLayout(
            bull_row
        )

        self.bull_bar = QProgressBar()

        self.bull_bar.setRange(
            0,
            100
        )

        self.bull_bar.setValue(
            0
        )

        self.bull_bar.setTextVisible(
            False
        )

        self.bull_bar.setStyleSheet("""
            QProgressBar {
                background: #242B35;
                border: none;
                border-radius: 5px;
                height: 8px;
            }

            QProgressBar::chunk {
                background: #34D399;
                border-radius: 5px;
            }
        """)

        sentiment_layout.addWidget(
            self.bull_bar
        )

        # ---------------- BEAR ----------------

        bear_row = QHBoxLayout()

        self.bear_title = QLabel(
            "BEARISH"
        )

        self.bear_title.setStyleSheet("""
            QLabel {
                color: #FF5F57;
                font-size: 10px;
                font-weight: 800;
            }
        """)

        bear_row.addWidget(
            self.bear_title
        )

        bear_row.addStretch()

        self.bear_value = QLabel(
            "0%"
        )

        self.bear_value.setStyleSheet("""
            QLabel {
                color: #FF5F57;
                font-size: 11px;
                font-weight: 800;
            }
        """)

        bear_row.addWidget(
            self.bear_value
        )

        sentiment_layout.addLayout(
            bear_row
        )

        self.bear_bar = QProgressBar()

        self.bear_bar.setRange(
            0,
            100
        )

        self.bear_bar.setValue(
            0
        )

        self.bear_bar.setTextVisible(
            False
        )

        self.bear_bar.setStyleSheet("""
            QProgressBar {
                background: #242B35;
                border: none;
                border-radius: 5px;
                height: 8px;
            }

            QProgressBar::chunk {
                background: #FF5F57;
                border-radius: 5px;
            }
        """)

        sentiment_layout.addWidget(
            self.bear_bar
        )

        main.addWidget(
            sentiment_frame
        )

        # ====================================================
        # METRIC CARDS
        # ====================================================

        metrics = QHBoxLayout()

        metrics.setSpacing(7)

        # STRENGTH
        self.strength_box = self.create_metric_box(
            "STRENGTH",
            "--",
            "#1683FF"
        )

        metrics.addWidget(
            self.strength_box["frame"]
        )

        # VOLATILITY
        self.volatility_box = self.create_metric_box(
            "VOLATILITY",
            "--",
            "#A970FF"
        )

        metrics.addWidget(
            self.volatility_box["frame"]
        )

        # SIDEWAYS
        self.sideways_box = self.create_metric_box(
            "SIDEWAYS",
            "--",
            "#F5B83D"
        )

        metrics.addWidget(
            self.sideways_box["frame"]
        )

        main.addLayout(
            metrics
        )

    # ========================================================
    # METRIC BOX
    # ========================================================

    def create_metric_box(
        self,
        title,
        value,
        accent
    ):

        frame = QFrame()

        frame.setObjectName(
            "MetricBox"
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            9,
            7,
            9,
            7
        )

        layout.setSpacing(2)

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: #8F9AAF;
                font-size: 8px;
                font-weight: 800;
            }}
            """
        )

        layout.addWidget(
            title_label
        )

        value_label = QLabel(
            value
        )

        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: #F5F7FA;
                font-size: 16px;
                font-weight: 800;
            }}
            """
        )

        layout.addWidget(
            value_label
        )

        status_label = QLabel(
            "--"
        )

        status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {accent};
                font-size: 9px;
                font-weight: 700;
            }}
            """
        )

        layout.addWidget(
            status_label
        )

        return {
            "frame": frame,
            "value": value_label,
            "status": status_label
        }

    # ========================================================
    # UPDATE DATA
    # ========================================================

    def update_data(
        self,
        data,
        index="NIFTY 50"
    ):

        if not isinstance(
            data,
            dict
        ):
            return

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        price = number(
            data.get(
                "price"
            )
        )

        self.instrument_label.setText(
            str(index)
        )

        if price > 0:

            self.price_label.setText(
                f"₹{price:,.2f}"
            )

        else:

            self.price_label.setText(
                "₹--"
            )

        # ----------------------------------------------------
        # CHANGE
        # ----------------------------------------------------

        change = data.get(
            "change_percent"
        )

        if change is None:

            self.change_label.setText(
                ""
            )

        else:

            change_value = number(
                change
            )

            if change_value > 0:

                self.change_label.setStyleSheet("""
                    QLabel {
                        color: #34D399;
                        font-size: 11px;
                        font-weight: 700;
                    }
                """)

                self.change_label.setText(
                    f"▲ +{change_value:.2f}%"
                )

            elif change_value < 0:

                self.change_label.setStyleSheet("""
                    QLabel {
                        color: #FF5F57;
                        font-size: 11px;
                        font-weight: 700;
                    }
                """)

                self.change_label.setText(
                    f"▼ {change_value:.2f}%"
                )

            else:

                self.change_label.setStyleSheet("""
                    QLabel {
                        color: #8F96A3;
                        font-size: 11px;
                        font-weight: 700;
                    }
                """)

                self.change_label.setText(
                    "• 0.00%"
                )

        # ----------------------------------------------------
        # TREND
        # ----------------------------------------------------

        trend = str(
            data.get(
                "trend",
                "N/A"
            )
        )

        trend_lower = trend.lower()

        if "bull" in trend_lower:

            trend_color = "#34D399"

        elif "bear" in trend_lower:

            trend_color = "#FF5F57"

        else:

            trend_color = "#1683FF"

        self.trend_label.setStyleSheet(
            f"""
            QLabel {{
                color: {trend_color};
                font-size: 12px;
                font-weight: 700;
                padding-top: 4px;
            }}
            """
        )

        self.trend_label.setText(
            f"● {trend}"
        )

        # ----------------------------------------------------
        # BULL
        # ----------------------------------------------------

        bull = number(
            data.get(
                "bull_probability"
            )
        )

        bull = max(
            0,
            min(
                100,
                bull
            )
        )

        self.bull_value.setText(
            f"{bull:.1f}%"
        )

        self.bull_bar.setValue(
            int(bull)
        )

        # ----------------------------------------------------
        # BEAR
        # ----------------------------------------------------

        bear = number(
            data.get(
                "bear_probability"
            )
        )

        bear = max(
            0,
            min(
                100,
                bear
            )
        )

        self.bear_value.setText(
            f"{bear:.1f}%"
        )

        self.bear_bar.setValue(
            int(bear)
        )

        # ----------------------------------------------------
        # MARKET SENTIMENT
        # ----------------------------------------------------

        sideways = number(
            data.get(
                "sideways_probability"
            )
        )

        if bear >= bull and bear >= sideways:

            sentiment = "BEARISH"
            sentiment_color = "#FF5F57"

        elif bull >= bear and bull >= sideways:

            sentiment = "BULLISH"
            sentiment_color = "#34D399"

        else:

            sentiment = "SIDEWAYS"
            sentiment_color = "#1683FF"

        self.sentiment_label.setText(
            sentiment
        )

        self.sentiment_label.setStyleSheet(
            f"""
            QLabel {{
                color: {sentiment_color};
                font-size: 17px;
                font-weight: 800;
            }}
            """
        )

        # ----------------------------------------------------
        # STRENGTH
        # ----------------------------------------------------

        strength = data.get(
            "strength"
        )

        if strength is not None:

            strength_value = number(
                strength
            )

            self.strength_box[
                "value"
            ].setText(
                f"{strength_value:.2f}"
            )

            if strength_value >= 1.5:

                strength_status = "Strong"

            elif strength_value >= 1.0:

                strength_status = "Neutral"

            else:

                strength_status = "Weak"

            self.strength_box[
                "status"
            ].setText(
                strength_status
            )

        # ----------------------------------------------------
        # VOLATILITY
        # ----------------------------------------------------

        volatility = data.get(
            "volatility"
        )

        if volatility is not None:

            volatility_value = number(
                volatility
            )

            self.volatility_box[
                "value"
            ].setText(
                f"{volatility_value:.2f}"
            )

            if volatility_value >= 1.0:

                volatility_status = "High"

            elif volatility_value >= 0.5:

                volatility_status = "Moderate"

            else:

                volatility_status = "Low"

            self.volatility_box[
                "status"
            ].setText(
                volatility_status
            )

        # ----------------------------------------------------
        # SIDEWAYS
        # ----------------------------------------------------

        self.sideways_box[
            "value"
        ].setText(
            f"{sideways:.1f}%"
        )

        self.sideways_box[
            "status"
        ].setText(
            "Market Probability"
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
            250
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
                "TRACK AGAIN"
                if already_tracked
                else "TRACK"
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setMinimumHeight(
                26
            )

            # A new scan is a new decision point. TRACK AGAIN is always
            # allowed and creates a separate tracked position instance.
            button.setEnabled(
                True
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

    # Step 7 - publish exact generated result to the analysis page.
    # Existing Dashboard behavior remains unchanged.
    ai_trade_generated = Signal(dict)

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

        # Step 8 - reuse the existing prediction tracker.
        # Existing TRACK/journal behavior remains separate and unchanged.
        self.prediction_tracker = PredictionTracker()

        self.tracked_trades = load_tracked_trades()

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
        # ====================================================
        # VISUAL MARKET OVERVIEW
        # ====================================================

        self.market_card.text.hide()

        self.market_overview = (
            MarketOverviewWidget()
        )

        self.market_card.body.layout().addWidget(
            self.market_overview
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
        # RESTORE PERSISTED TRACKED TRADES
        # ====================================================

        # Delay until the event loop starts so MainWindow has time
        # to connect tracking_changed to the Tracking page.
        QTimer.singleShot(
            0,
            self.restore_tracked_trades
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
    # RESTORE TRACKED TRADES
    # =========================================================


    # =========================================================
    # TRACKING METADATA
    # =========================================================
    @staticmethod
    def _is_terminal_trade_status(status):
        return str(
            status or ""
        ).upper() in (
            "TARGET 1 HIT",
            "TARGET 2 HIT",
            "STOP LOSS HIT",
        )

    def _backfill_tracking_metadata(self, trade):
        changed = False

        instrument = str(
            trade.get(
                "instrument",
                trade.get("index", "NIFTY 50"),
            )
        ).upper()

        try:
            strike = float(trade.get("strike"))
        except Exception:
            strike = None

        option_type = str(
            trade.get("type", "")
        ).upper()

        entry = number(
            trade.get(
                "fixed_entry",
                trade.get("entry"),
            ),
            0.0,
        )

        quantity = int(
            trade.get(
                "quantity",
                trade.get(
                    "lot_size",
                    self.LOT_SIZES.get(
                        instrument,
                        1,
                    ),
                ),
            )
        )

        if quantity <= 0:
            quantity = self.LOT_SIZES.get(
                instrument,
                1,
            )

        if not trade.get("capital_required_1_lot"):
            trade["capital_required_1_lot"] = (
                entry * quantity
            )
            changed = True

        if trade.get("lot_size") != quantity:
            trade["lot_size"] = quantity
            changed = True

        if not trade.get("started_at") and strike is not None:
            try:
                ledger = (
                    self.prediction_tracker
                    .load_trade_predictions()
                )
            except Exception:
                ledger = None

            if ledger is not None and not ledger.empty:
                candidates = ledger.copy()

                if "symbol" in candidates.columns:
                    candidates = candidates[
                        candidates["symbol"].astype(str).str.upper().eq(
                            instrument
                        )
                    ]

                if "type" in candidates.columns:
                    candidates = candidates[
                        candidates["type"].astype(str).str.upper().eq(
                            option_type
                        )
                    ]

                if "strike" in candidates.columns:
                    candidates = candidates[
                        pd.to_numeric(
                            candidates["strike"],
                            errors="coerce",
                        ).eq(strike)
                    ]

                if not candidates.empty and "entry" in candidates.columns:
                    candidates["_entry_diff"] = (
                        pd.to_numeric(
                            candidates["entry"],
                            errors="coerce",
                        ) - entry
                    ).abs()

                    sort_cols = ["_entry_diff"]
                    asc = [True]
                    if "generated_at" in candidates.columns:
                        sort_cols.append("generated_at")
                        asc.append(False)

                    candidates = candidates.sort_values(
                        sort_cols,
                        ascending=asc,
                    )
                elif not candidates.empty and "generated_at" in candidates.columns:
                    candidates = candidates.sort_values(
                        "generated_at",
                        ascending=False,
                    )

                if not candidates.empty:
                    match = candidates.iloc[0]
                    generated_at = match.get("generated_at")
                    if generated_at:
                        trade["started_at"] = str(generated_at)
                        changed = True

                    if (
                        self._is_terminal_trade_status(
                            trade.get("status")
                        )
                        and not trade.get("ended_at")
                    ):
                        ended_at = match.get("outcome_timestamp")
                        if ended_at:
                            trade["ended_at"] = str(ended_at)
                            changed = True

        return changed

    def _backfill_all_tracking_metadata(self):
        changed = False
        for trade in self.tracked_trades:
            if self._backfill_tracking_metadata(trade):
                changed = True

        if changed:
            save_tracked_trades(
                self.tracked_trades
            )

        return changed

    def restore_tracked_trades(
        self
    ):
        """Restore active trades after the UI connections exist."""

        self._expire_previous_day_trades()
        # Backfill metadata for legacy persisted tracked trades.
        self._backfill_all_tracking_metadata()


        if not self.tracked_trades:
            self.refresh_dashboard_metrics()
            return

        # Make sure older persisted records still have the fields
        # required by the live tracker.
        for trade in self.tracked_trades:
            instrument = trade.get(
                "instrument",
                trade.get("index", "NIFTY 50")
            )
            trade.setdefault(
                "instrument",
                instrument
            )
            trade.setdefault(
                "index",
                instrument
            )
            trade.setdefault(
                "status",
                "LIVE"
            )
            trade.setdefault(
                "quantity",
                self.LOT_SIZES.get(
                    instrument,
                    1
                )
            )
            trade.setdefault(
                "lot_size",
                trade.get("quantity", 1)
            )

        self.tracking_changed.emit(
            [
                dict(trade)
                for trade in self.tracked_trades
            ]
        )

        self.trade_panel.set_trades(
            self.current_trades,
            self.tracked_keys()
        )

        self.refresh_dashboard_metrics()

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

        if not isinstance(
            data,
            dict
        ):
            return

        # =====================================================
        # VISUAL MARKET OVERVIEW
        # =====================================================

        self.market_overview.update_data(
            data,
            index
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

        self.update_tracked_prices()

        # =========================================================
        # STEP 8 - UPDATE GENERATED PREDICTION OUTCOMES
        # =========================================================
        try:
            for instrument, snapshot in snapshots.items():

                option_rows = (
                    snapshot.get("rows")
                    or []
                )

                self.prediction_tracker.update_market_snapshot(
                    instrument,
                    option_rows,
                )

        except Exception as exc:

            print(
                "[PREDICTION-TRACKER] Outcome update error:",
                exc,
            )

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

            self.restore_tracked_trade_values()

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

        # STEP 11 - resolve option-trade outcomes from live quotes.
        # The PredictionTracker keeps this ledger separate from the generic
        # ML prediction ledger and resolves TARGET 1 / TARGET 2 / STOP LOSS.
        try:
            self.prediction_tracker.update_market_snapshot(
                self.selected_instrument,
                rows,
            )
        except Exception as exc:
            print(
                "[PREDICTION-TRACKER] "
                "Market snapshot update failed:",
                exc,
            )

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

        # IMPORTANT:
        # Do not overwrite a fresh AI scan with an older tracked trade's
        # entry/SL/targets. Every Generate AI Trade result is a new signal.
        # The frozen values are captured only when TRACK is pressed.
        self.trade_panel.set_trades(
            self.current_trades,
            self.tracked_keys()
        )

        self.render_result(
            result
        )

        # =========================================================
        # STEP 8 - RECORD GENERATED AI TRADE PREDICTIONS
        # =========================================================
        try:
            self.prediction_tracker.record_generation(
                result
            )
        except Exception as exc:
            print(
                "[PREDICTION-TRACKER] Record error:",
                exc,
            )

        self.ai_trade_generated.emit(
            dict(self.current_result)
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
    # RESTORE FROZEN VALUES FOR TRACKED TRADES
    # =========================================================

    def restore_tracked_trade_values(self):
        """
        If an AI opportunity is already being tracked,
        keep the original Entry / SL / Targets.

        Only LIVE price is allowed to change.
        """

        tracked_by_key = {
            trade.get("key"): trade
            for trade in self.tracked_trades
        }

        for trade in self.current_trades:

            instrument = trade.get(
                "selected_index",
                self.selected_instrument
            )

            strike = trade.get("strike")
            option_type = trade.get("type")

            key = (
                f"{instrument}|"
                f"{strike}|"
                f"{option_type}"
            )

            tracked = tracked_by_key.get(key)

            if not tracked:
                continue

            # -------------------------------------------------
            # FROZEN ENTRY
            # -------------------------------------------------

            fixed_entry = tracked.get(
                "fixed_entry",
                tracked.get("entry")
            )

            if fixed_entry is not None:
                trade["entry"] = fixed_entry

                risk = trade.setdefault(
                    "risk",
                    {}
                )

                risk["entry"] = fixed_entry

            # -------------------------------------------------
            # FROZEN STOP LOSS
            # -------------------------------------------------

            fixed_sl = tracked.get(
                "fixed_sl",
                tracked.get("sl")
            )

            if fixed_sl is not None:
                trade["sl"] = fixed_sl

                risk = trade.setdefault(
                    "risk",
                    {}
                )

                risk["sl"] = fixed_sl

            # -------------------------------------------------
            # FROZEN TARGET 1
            # -------------------------------------------------

            fixed_target1 = tracked.get(
                "fixed_target1",
                tracked.get("target1")
            )

            if fixed_target1 is not None:
                trade["target1"] = fixed_target1

                risk = trade.setdefault(
                    "risk",
                    {}
                )

                risk["target1"] = fixed_target1

            # -------------------------------------------------
            # FROZEN TARGET 2
            # -------------------------------------------------

            fixed_target2 = tracked.get(
                "fixed_target2",
                tracked.get("target2")
            )

            if fixed_target2 is not None:
                trade["target2"] = fixed_target2

                risk = trade.setdefault(
                    "risk",
                    {}
                )

                risk["target2"] = fixed_target2
    # =========================================================
    # TRACKING LIFECYCLE
    # =========================================================

    @staticmethod
    def _is_terminal_tracking_status(
        status,
    ):
        return str(
            status or ""
        ).upper() in (
            "TARGET 1 HIT",
            "TARGET 2 HIT",
            "STOP LOSS HIT",
            "DAY ENDED",
        )

    def _expire_previous_day_trades(
        self,
    ):
        """
        Active trades belong to the trading day on which TRACK was pressed.

        On a later calendar day they become historical DAY ENDED rows.
        They remain persisted and visible, but no longer block new tracking.
        """
        today = datetime.now().date()
        changed = False

        for trade in self.tracked_trades:
            if self._is_terminal_tracking_status(
                trade.get("status")
            ):
                continue

            started_at = trade.get(
                "started_at"
            )

            if not started_at:
                continue

            try:
                started_date = (
                    datetime.fromisoformat(
                        str(started_at)
                    ).date()
                )
            except Exception:
                continue

            if started_date < today:
                trade["status"] = "DAY ENDED"

                if not trade.get(
                    "ended_at"
                ):
                    trade["ended_at"] = datetime.now().isoformat(
                        timespec="seconds"
                    )

                changed = True

        if changed:
            save_tracked_trades(
                self.tracked_trades
            )

        return changed

    # =========================================================
    # TRACKED KEYS
    # =========================================================

    def tracked_keys(
        self
    ):
        """
        Keys of ACTIVE trades only.

        Completed trades remain in history but do not block a new TRACK
        action on the same strike/type later.
        """
        terminal_statuses = {
            "TARGET 1 HIT",
            "TARGET 2 HIT",
            "STOP LOSS HIT",
            "DAY ENDED",
        }

        return {
            (
                f"{trade.get('instrument')}"
                f"|{trade.get('strike')}"
                f"|{trade.get('type')}"
            )

            for trade in (
                self.tracked_trades
            )
            if str(
                trade.get(
                    "status",
                    "LIVE",
                )
            ).upper()
            not in terminal_statuses
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
        # NEW TRACK INSTANCE
        # ----------------------------------------------------
        # Every click on TRACK represents a new potential position.
        # Previous completed/active instances are preserved separately.

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

            # Unique instance ID. The instrument/strike/type key remains
            # useful for live quote matching, but does NOT identify the
            # lifetime of the tracked position.
            "track_id":
                datetime.now().strftime(
                    "%Y%m%d%H%M%S%f"
                )
                + "_"
                + uuid4().hex[:8],

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

            # =================================================
            # IMMUTABLE TRADE DEFINITION
            # Captured exactly when TRACK is pressed.
            # These fields are never replaced by later AI scans.
            # =================================================
            "entry": entry,
            "fixed_entry": entry,

            # =================================================
            # LIVE MARKET PRICE
            # This is the ONLY price that changes after tracking.
            # =================================================
            "ltp": live,

            # Outcome checks are based on crossings AFTER TRACK is pressed.
            # A trade should not instantly become TARGET 1 HIT merely because
            # the current premium was already above the frozen target.
            "last_checked_ltp":
                live,

            "tracking_started_ltp":
                live,

            "sl": sl,
            "fixed_sl": sl,

            "target1": target1,
            "fixed_target1": target1,

            "target2": target2,
            "fixed_target2": target2,

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

            "started_at":
                datetime.now().isoformat(
                    timespec="seconds"
                ),

            "ended_at":
                None,

            # One-lot capital = frozen entry premium × lot size.
            "capital_required_1_lot":
                entry * quantity,

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

        # Persist the fixed trade definition immediately.
        # Live LTP will be refreshed from NSE after restart.
        save_tracked_trades(
            self.tracked_trades
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
                "TARGET 1 HIT",
                "TARGET 2 HIT",
                "STOP LOSS HIT",
                "DAY ENDED"
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

            # Always use the frozen entry for P&L.
            entry = number(
                trade.get(
                    "fixed_entry",
                    trade.get("entry")
                )
            )

            # Backfill frozen values for older tracked_trades.json files.
            trade.setdefault("fixed_entry", entry)
            trade.setdefault("fixed_sl", number(trade.get("sl")))
            trade.setdefault("fixed_target1", number(trade.get("target1")))
            trade.setdefault("fixed_target2", number(trade.get("target2", trade.get("target1"))))

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

            old_status = trade.get(
                "status",
                "LIVE",
            )

            previous_ltp = number(
                trade.get(
                    "last_checked_ltp",
                    ltp,
                ),
                ltp,
            )

            # =================================================
            # TARGET / STOP RESOLUTION
            # =================================================
            # Only a price CROSSING after TRACK can resolve the trade.
            # This prevents an immediate TARGET 1 HIT when the current
            # quote is already above the frozen target at the moment
            # the user presses TRACK.

            fixed_target2 = number(
                trade.get(
                    "fixed_target2",
                    trade.get("target2", 0),
                ),
                0,
            )

            fixed_target1 = number(
                trade.get(
                    "fixed_target1",
                    trade.get("target1", 0),
                ),
                0,
            )

            fixed_sl = number(
                trade.get(
                    "fixed_sl",
                    trade.get("sl", 0),
                ),
                0,
            )

            if (
                fixed_target2 > 0
                and previous_ltp < fixed_target2
                and ltp >= fixed_target2
            ):
                trade[
                    "status"
                ] = "TARGET 2 HIT"

            elif (
                fixed_target1 > 0
                and previous_ltp < fixed_target1
                and ltp >= fixed_target1
            ):
                trade[
                    "status"
                ] = "TARGET 1 HIT"

            elif (
                fixed_sl > 0
                and previous_ltp > fixed_sl
                and ltp <= fixed_sl
            ):
                trade[
                    "status"
                ] = "STOP LOSS HIT"

            trade[
                "last_checked_ltp"
            ] = ltp

            if (
                old_status == "LIVE"
                and self._is_terminal_trade_status(
                    trade.get("status")
                )
            ):
                trade["ended_at"] = (
                    datetime.now().isoformat(
                        timespec="seconds"
                    )
                )

            # Persist the live LTP/P&L/status so reopening the app
            # immediately restores the last known state.
            save_tracked_trades(
                self.tracked_trades
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
    # PERSIST / REMOVE TRACKED TRADES
    # =========================================================

    def persist_tracked_trades(
        self
    ):
        return save_tracked_trades(
            self.tracked_trades
        )

    def remove_tracked_trade(
        self,
        key
    ):
        """Remove an active tracked trade and persist the change."""

        before = len(
            self.tracked_trades
        )

        self.tracked_trades = [
            trade
            for trade in self.tracked_trades
            if trade.get("key") != key
        ]

        if len(self.tracked_trades) == before:
            return False

        save_tracked_trades(
            self.tracked_trades
        )

        self.tracking_changed.emit(
            [
                dict(trade)
                for trade in self.tracked_trades
            ]
        )

        self.trade_panel.set_trades(
            self.current_trades,
            self.tracked_keys()
        )

        self.refresh_dashboard_metrics()
        return True

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