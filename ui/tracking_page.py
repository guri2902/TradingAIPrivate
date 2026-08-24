from __future__ import annotations

import pandas as pd

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


LOT_SIZES = {
    "NIFTY 50": 65,
    "BANK NIFTY": 30,
    "FINNIFTY": 60,
}


TERMINAL_STATUSES = {
    "TARGET 1 HIT",
    "TARGET 2 HIT",
    "STOP LOSS HIT",
    "DAY ENDED",
}


def number(
    value,
    default=0.0,
):
    try:
        return float(value)
    except Exception:
        return default


def money(
    value,
):
    try:
        return f"₹{float(value):,.2f}"
    except Exception:
        return "₹--"


def pct(
    value,
):
    try:
        return f"{float(value):+.2f}%"
    except Exception:
        return "—"


def date_part(value):
    if not value:
        return "—"
    try:
        return pd.to_datetime(
            value,
            errors="coerce",
        ).strftime("%d-%b-%Y")
    except Exception:
        return "—"


def time_part(value):
    if not value:
        return "—"
    try:
        return pd.to_datetime(
            value,
            errors="coerce",
        ).strftime("%H:%M:%S")
    except Exception:
        text = str(value)
        return text.split(
            "T",
            1,
        )[-1][:8]


def is_terminal_status(
    status,
):
    return str(
        status or ""
    ).upper() in TERMINAL_STATUSES


def is_positive(
    value,
):
    return number(
        value,
        0.0,
    ) > 0


def is_negative(
    value,
):
    return number(
        value,
        0.0,
    ) < 0


class TradeRow(QFrame):
    """
    Dense but readable trade row matching the requested TradingAI Pro look.
    """

    action_clicked = Signal(dict)

    def __init__(
        self,
        trade,
        completed=False,
        parent=None,
    ):
        super().__init__(parent)

        self.trade = dict(trade)
        self.completed = completed

        self.setObjectName(
            "tradeRow"
        )

        self.setStyleSheet(
            """
            QFrame#tradeRow {
                background: #101821;
                border: 1px solid #1F2B3A;
                border-radius: 10px;
            }

            QFrame#tradeRow:hover {
                background: #131E2A;
                border: 1px solid #2A4058;
            }

            QLabel {
                background: transparent;
                border: none;
            }
            """
        )

        layout = QGridLayout(
            self
        )
        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )
        layout.setHorizontalSpacing(
            12
        )
        layout.setVerticalSpacing(
            2
        )

        status = str(
            trade.get(
                "status",
                "LIVE",
            )
        )

        # ------------------------------------------------------
        # Primary information
        # ------------------------------------------------------

        status_pill = QLabel(
            status
        )
        status_pill.setAlignment(
            Qt.AlignCenter
        )
        status_pill.setMinimumWidth(
            92
        )
        status_pill.setMaximumWidth(
            108
        )

        if status == "LIVE":
            status_pill.setStyleSheet(
                """
                QLabel {
                    color: #30E18F;
                    background: rgba(28, 145, 98, 0.16);
                    border: 1px solid rgba(48, 225, 143, 0.28);
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-size: 10px;
                    font-weight: 800;
                }
                """
            )
        elif "TARGET" in status:
            status_pill.setStyleSheet(
                """
                QLabel {
                    color: #25E88F;
                    background: rgba(24, 170, 102, 0.15);
                    border: 1px solid rgba(37, 232, 143, 0.25);
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-size: 10px;
                    font-weight: 800;
                }
                """
            )
        elif "STOP LOSS" in status:
            status_pill.setStyleSheet(
                """
                QLabel {
                    color: #FF5B63;
                    background: rgba(255, 91, 99, 0.12);
                    border: 1px solid rgba(255, 91, 99, 0.24);
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-size: 10px;
                    font-weight: 800;
                }
                """
            )
        else:
            status_pill.setStyleSheet(
                """
                QLabel {
                    color: #F5C84B;
                    background: rgba(245, 200, 75, 0.12);
                    border: 1px solid rgba(245, 200, 75, 0.22);
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-size: 10px;
                    font-weight: 800;
                }
                """
            )

        instrument = str(
            trade.get(
                "instrument",
                trade.get(
                    "index",
                    "NIFTY 50",
                ),
            )
        )

        option_type = str(
            trade.get(
                "type",
                "",
            )
        ).upper()

        strike = trade.get(
            "strike",
            "—",
        )

        try:
            strike_text = f"{float(strike):.0f}"
        except Exception:
            strike_text = str(strike)

        instrument_label = QLabel(
            instrument
        )
        instrument_label.setStyleSheet(
            """
            QLabel {
                color: #E9EFF8;
                font-size: 11px;
                font-weight: 700;
            }
            """
        )

        type_badge = QLabel(
            option_type
        )
        type_badge.setAlignment(
            Qt.AlignCenter
        )
        type_badge.setMinimumWidth(
            30
        )
        type_badge.setStyleSheet(
            """
            QLabel {
                color: #FF8D95;
                background: rgba(255, 95, 103, .15);
                border-radius: 5px;
                padding: 4px 6px;
                font-size: 10px;
                font-weight: 800;
            }
            """
        )

        if option_type == "CE":
            type_badge.setStyleSheet(
                """
                QLabel {
                    color: #45E0A5;
                    background: rgba(69, 224, 165, .12);
                    border-radius: 5px;
                    padding: 4px 6px;
                    font-size: 10px;
                    font-weight: 800;
                }
                """
            )

        strike_label = QLabel(
            strike_text
        )
        strike_label.setStyleSheet(
            """
            QLabel {
                color: #F5F8FC;
                font-size: 13px;
                font-weight: 800;
            }
            """
        )

        start = (
            f"{date_part(trade.get('started_at'))}\n"
            f"{time_part(trade.get('started_at'))}"
        )

        start_label = QLabel(
            start
        )
        start_label.setStyleSheet(
            """
            QLabel {
                color: #A9B6C8;
                font-size: 9px;
                line-height: 1.1;
            }
            """
        )

        end = (
            f"{date_part(trade.get('ended_at'))}\n"
            f"{time_part(trade.get('ended_at'))}"
        )

        end_label = QLabel(
            end
        )
        end_label.setStyleSheet(
            """
            QLabel {
                color: #8795A8;
                font-size: 9px;
                line-height: 1.1;
            }
            """
        )

        # ------------------------------------------------------
        # Financial values
        # ------------------------------------------------------

        entry = number(
            trade.get(
                "fixed_entry",
                trade.get(
                    "entry",
                ),
            ),
            0.0,
        )

        live = number(
            trade.get(
                "ltp",
                trade.get(
                    "live_price",
                    entry,
                ),
            ),
            entry,
        )

        qty = int(
            number(
                trade.get(
                    "quantity",
                    trade.get(
                        "lot_size",
                        LOT_SIZES.get(
                            instrument,
                            1,
                        ),
                    ),
                ),
                LOT_SIZES.get(
                    instrument,
                    1,
                ),
            )
        )

        capital = number(
            trade.get(
                "capital_required_1_lot",
                entry * qty,
            ),
            entry * qty,
        )

        stop = number(
            trade.get(
                "fixed_sl",
                trade.get(
                    "sl",
                ),
            ),
            0.0,
        )

        target1 = number(
            trade.get(
                "fixed_target1",
                trade.get(
                    "target1",
                ),
            ),
            0.0,
        )

        target2 = number(
            trade.get(
                "fixed_target2",
                trade.get(
                    "target2",
                ),
            ),
            0.0,
        )

        pnl_point = (
            live - entry
        )

        total_pnl = number(
            trade.get(
                "total_pnl",
                pnl_point * qty,
            ),
            pnl_point * qty,
        )

        premium = QLabel(
            money(entry)
        )

        premium_badge = QLabel(
            "locked"
        )
        premium_badge.setAlignment(
            Qt.AlignCenter
        )
        premium_badge.setStyleSheet(
            """
            QLabel {
                color: #59B8FF;
                background: rgba(46, 151, 255, .13);
                border-radius: 4px;
                padding: 2px 5px;
                font-size: 8px;
            }
            """
        )

        premium_box = QWidget()
        premium_box_layout = QVBoxLayout(
            premium_box
        )
        premium_box_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        premium_box_layout.setSpacing(
            2
        )
        premium_box_layout.addWidget(
            premium
        )
        premium_box_layout.addWidget(
            premium_badge
        )

        live_label = QLabel(
            money(live)
        )
        live_label.setStyleSheet(
            f"""
            QLabel {{
                color: {"#2FE393" if pnl_point >= 0 else "#FF626A"};
                font-size: 11px;
                font-weight: 800;
            }}
            """
        )

        live_delta = QLabel(
            pct(
                (
                    (
                        live - entry
                    )
                    / entry
                    * 100
                )
                if entry
                else 0
            )
        )
        live_delta.setStyleSheet(
            f"""
            QLabel {{
                color: {"#2FE393" if pnl_point >= 0 else "#FF626A"};
                font-size: 8px;
            }}
            """
        )

        live_box = QWidget()
        live_box_layout = QVBoxLayout(
            live_box
        )
        live_box_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        live_box_layout.setSpacing(
            2
        )
        live_box_layout.addWidget(
            live_label
        )
        live_box_layout.addWidget(
            live_delta
        )

        score = trade.get(
            "ai_score",
            "—",
        )
        probability = trade.get(
            "probability",
            "—",
        )

        ai_label = QLabel(
            f"{score} / {probability}%"
        )
        ai_label.setStyleSheet(
            """
            QLabel {
                color: #D8E4F2;
                font-size: 10px;
                font-weight: 700;
            }
            """
        )

        stars = QLabel(
            "★★★"
        )
        stars.setStyleSheet(
            """
            QLabel {
                color: #F7C948;
                font-size: 12px;
                letter-spacing: 1px;
            }
            """
        )

        ai_box = QWidget()
        ai_box_layout = QVBoxLayout(
            ai_box
        )
        ai_box_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        ai_box_layout.setSpacing(
            0
        )
        ai_box_layout.addWidget(
            ai_label
        )
        ai_box_layout.addWidget(
            stars
        )

        pnl_point_label = QLabel(
            money(pnl_point)
        )

        total_pnl_label = QLabel(
            money(total_pnl)
        )

        pnl_color = (
            "#2FE393"
            if total_pnl >= 0
            else "#FF626A"
        )

        for label in (
            pnl_point_label,
            total_pnl_label,
        ):
            label.setStyleSheet(
                f"""
                QLabel {{
                    color: {pnl_color};
                    font-size: 10px;
                    font-weight: 800;
                }}
                """
            )

        qty_label = QLabel(
            str(qty)
        )
        qty_label.setStyleSheet(
            """
            QLabel {
                color: #DDE7F2;
                font-size: 10px;
            }
            """
        )

        # ------------------------------------------------------
        # Add columns
        # ------------------------------------------------------

        columns = [
            status_pill,
            instrument_label,
            type_badge,
            strike_label,
            self._small_label(
                start,
            ),
            self._small_label(
                end,
            ),
            premium_box,
            self._small_label(
                money(capital),
            ),
            live_box,
            qty_label,
            self._small_label(
                money(stop),
            ),
            self._small_label(
                money(target1),
            ),
            self._small_label(
                money(target2),
            ),
            pnl_point_label,
            total_pnl_label,
            ai_box,
        ]

        widths = [
            100,
            75,
            35,
            60,
            82,
            82,
            80,
            95,
            82,
            42,
            75,
            75,
            75,
            75,
            85,
            90,
        ]

        for column, (
            widget,
            width,
        ) in enumerate(
            zip(
                columns,
                widths,
            )
        ):
            widget.setMinimumWidth(
                width
            )
            widget.setMaximumWidth(
                width
            )
            layout.addWidget(
                widget,
                0,
                column,
            )

        action = QPushButton(
            "⋮"
        )
        action.setCursor(
            Qt.PointingHandCursor
        )
        action.setFixedSize(
            28,
            28,
        )
        action.setStyleSheet(
            """
            QPushButton {
                color: #7F8DA1;
                background: #17212D;
                border: 1px solid #283646;
                border-radius: 8px;
                font-size: 15px;
            }

            QPushButton:hover {
                color: white;
                background: #1E2C3A;
            }
            """
        )

        action.clicked.connect(
            lambda: self.action_clicked.emit(
                dict(
                    self.trade
                )
            )
        )

        layout.addWidget(
            action,
            0,
            len(columns),
        )

        layout.setColumnStretch(
            len(columns) + 1,
            1,
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

    @staticmethod
    def _small_label(
        text,
    ):
        label = QLabel(
            str(text)
        )
        label.setStyleSheet(
            """
            QLabel {
                color: #C8D3E1;
                font-size: 9px;
            }
            """
        )
        return label


class TradeTrackingPage(QWidget):

    def __init__(
        self,
    ):
        super().__init__()

        self.all_trades = []
        self.filtered_trades = []

        # Default filter state must exist before the first update_trades()
        # call made by MainWindow startup synchronization.
        self.filter_mode = "all"

        self.setObjectName(
            "TradeTrackingPage"
        )

        self.setStyleSheet(
            """
            QWidget#TradeTrackingPage {
                background: #0B1118;
                color: #EDF3FA;
            }

            QLabel {
                background: transparent;
                border: none;
            }

            QLineEdit {
                color: #E9F0F7;
                background: #101923;
                border: 1px solid #263445;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 10px;
            }

            QLineEdit:focus {
                border: 1px solid #2C8CFF;
            }

            QComboBox {
                color: #DDE7F2;
                background: #101923;
                border: 1px solid #263445;
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 10px;
            }

            QComboBox:hover {
                border: 1px solid #2C8CFF;
            }

            QComboBox QAbstractItemView {
                color: #EAF2FA;
                background: #101923;
                border: 1px solid #263445;
                selection-background-color: #0A84FF;
                selection-color: white;
                padding: 4px;
                outline: none;
            }

            QPushButton {
                color: #DDE7F2;
                background: #121C27;
                border: 1px solid #263445;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 10px;
                font-weight: 700;
            }

            QPushButton:hover {
                background: #182535;
                border: 1px solid #2C8CFF;
            }

            QScrollArea {
                background: #0B1118;
                border: none;
            }

            QScrollArea > QWidget {
                background: #0B1118;
            }

            QScrollArea > QWidget > QWidget {
                background: #0B1118;
            }

            QScrollBar:vertical {
                background: #0B1118;
                width: 10px;
            }

            QScrollBar::handle:vertical {
                background: #283647;
                border-radius: 5px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

        root = QVBoxLayout(
            self
        )
        root.setContentsMargins(
            18,
            16,
            18,
            16,
        )
        root.setSpacing(
            12
        )

        # ------------------------------------------------------
        # Header
        # ------------------------------------------------------

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title_box.setSpacing(
            2
        )

        title = QLabel(
            "Trade Tracking"
        )
        title.setStyleSheet(
            """
            QLabel {
                color: #F7FAFF;
                font-size: 24px;
                font-weight: 850;
            }
            """
        )

        self.subtitle = QLabel(
            "Live AI trade monitoring • Fixed entry • Live premium • P&L • Lot size"
        )
        self.subtitle.setStyleSheet(
            """
            QLabel {
                color: #7E8EA4;
                font-size: 10px;
            }
            """
        )

        title_box.addWidget(
            title
        )
        title_box.addWidget(
            self.subtitle
        )

        header.addLayout(
            title_box
        )
        header.addStretch()

        root.addLayout(
            header
        )

        # ------------------------------------------------------
        # Top summary cards
        # ------------------------------------------------------

        stats = QHBoxLayout()
        stats.setSpacing(
            10
        )

        self.active_card = self._stat_card(
            "ACTIVE TRADES",
            "0",
            "#25E88F",
            "• Live",
        )

        self.history_card = self._stat_card(
            "HISTORY",
            "0",
            "#7B90A8",
            "Completed",
        )

        self.capital_card = self._stat_card(
            "1-LOT CAPITAL",
            "₹0.00",
            "#4AB0FF",
            "",
        )

        self.pnl_card = self._stat_card(
            "TOTAL P&L",
            "₹0.00",
            "#25E88F",
            "",
        )

        stats.addWidget(
            self.active_card,
            1
        )
        stats.addWidget(
            self.history_card,
            1
        )
        stats.addWidget(
            self.capital_card,
            1
        )
        stats.addWidget(
            self.pnl_card,
            1
        )

        root.addLayout(
            stats
        )

        # ------------------------------------------------------
        # Toolbar
        # ------------------------------------------------------

        toolbar = QFrame()
        toolbar.setStyleSheet(
            """
            QFrame {
                background: #0F1822;
                border: 1px solid #1F2C3A;
                border-radius: 10px;
            }
            """
        )

        toolbar_layout = QHBoxLayout(
            toolbar
        )
        toolbar_layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )
        toolbar_layout.setSpacing(
            8
        )

        self.all_button = self._filter_button(
            "All Trades",
            True,
        )

        self.active_button = self._filter_button(
            "● Active",
            False,
        )

        self.completed_button = self._filter_button(
            "◉ Completed",
            False,
        )

        self.all_button.clicked.connect(
            lambda: self._set_filter(
                "all"
            )
        )

        self.active_button.clicked.connect(
            lambda: self._set_filter(
                "active"
            )
        )

        self.completed_button.clicked.connect(
            lambda: self._set_filter(
                "completed"
            )
        )

        toolbar_layout.addWidget(
            self.all_button
        )
        toolbar_layout.addWidget(
            self.active_button
        )
        toolbar_layout.addWidget(
            self.completed_button
        )

        toolbar_layout.addSpacing(
            10
        )

        self.status_combo = QComboBox()
        self.status_combo.addItems(
            [
                "By Status",
                "LIVE",
                "TARGET 1 HIT",
                "TARGET 2 HIT",
                "STOP LOSS HIT",
                "DAY ENDED",
            ]
        )
        self.status_combo.currentIndexChanged.connect(
            self._apply_filters
        )

        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems(
            [
                "By Instrument",
                "NIFTY 50",
                "BANK NIFTY",
                "FINNIFTY",
            ]
        )
        self.instrument_combo.currentIndexChanged.connect(
            self._apply_filters
        )

        toolbar_layout.addWidget(
            self.status_combo
        )
        toolbar_layout.addWidget(
            self.instrument_combo
        )

        toolbar_layout.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search trade..."
        )
        self.search.setMinimumWidth(
            170
        )
        self.search.textChanged.connect(
            self._apply_filters
        )

        toolbar_layout.addWidget(
            self.search
        )

        export_button = QPushButton(
            "↥  Export"
        )
        export_button.clicked.connect(
            self._export_visible
        )

        toolbar_layout.addWidget(
            export_button
        )

        root.addWidget(
            toolbar
        )

        # ------------------------------------------------------
        # Scroll content
        # ------------------------------------------------------

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(
            True
        )
        self.scroll.setFrameShape(
            QFrame.NoFrame
        )
        self.scroll.setStyleSheet(
            """
            QScrollArea {
                background: #0B1118;
                border: none;
            }

            QScrollArea > QWidget {
                background: #0B1118;
            }

            QScrollBar:vertical {
                background: #0B1118;
                width: 10px;
            }

            QScrollBar::handle:vertical {
                background: #283647;
                border-radius: 5px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.content = QWidget()
        self.content.setAutoFillBackground(True)
        self.content.setStyleSheet(
            """
            QWidget {
                background: #0B1118;
                color: #EDF3FA;
            }
            """
        )

        self.content_layout = QVBoxLayout(
            self.content
        )
        self.content_layout.setContentsMargins(
            0,
            0,
            4,
            20,
        )
        self.content_layout.setSpacing(
            8
        )
        self.content_layout.setAlignment(
            Qt.AlignTop
        )

        self.scroll.setWidget(
            self.content
        )

        root.addWidget(
            self.scroll,
            1,
        )

        # ------------------------------------------------------
        # Bottom performance cards
        # ------------------------------------------------------

        bottom = QHBoxLayout()
        bottom.setSpacing(
            10
        )

        self.total_card = self._bottom_card(
            "TOTAL TRADES",
            "0",
            "All time",
        )

        self.win_card = self._bottom_card(
            "WIN RATE",
            "0.00%",
            "0 wins / 0 losses",
        )

        self.best_card = self._bottom_card(
            "BEST TRADE",
            "₹0.00",
            "—",
            positive=True,
        )

        self.worst_card = self._bottom_card(
            "WORST TRADE",
            "₹0.00",
            "—",
            positive=False,
        )

        self.avg_card = self._bottom_card(
            "AVG P&L / TRADE",
            "₹0.00",
            "—",
        )

        self.factor_card = self._bottom_card(
            "PROFIT FACTOR",
            "—",
            "Gross profit / gross loss",
        )

        bottom.addWidget(
            self.total_card,
            1
        )
        bottom.addWidget(
            self.win_card,
            1
        )
        bottom.addWidget(
            self.best_card,
            1
        )
        bottom.addWidget(
            self.worst_card,
            1
        )
        bottom.addWidget(
            self.avg_card,
            1
        )
        bottom.addWidget(
            self.factor_card,
            1
        )

        root.addLayout(
            bottom
        )

        footer = QLabel(
            "Data updates automatically • All prices are live • Times in IST"
        )
        footer.setAlignment(
            Qt.AlignCenter
        )
        footer.setStyleSheet(
            """
            QLabel {
                color: #67778C;
                font-size: 9px;
                padding: 4px;
            }
            """
        )

        root.addWidget(
            footer
        )

        self._clear_content()

    # ======================================================
    # UI helpers
    # ======================================================

    def _stat_card(
        self,
        title,
        value,
        accent,
        suffix,
    ):
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background: #101923;
                border: 1px solid #1F2C3A;
                border-radius: 10px;
            }}
            """
        )

        layout = QVBoxLayout(
            card
        )
        layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )
        layout.setSpacing(
            4
        )

        top = QLabel(
            title
        )
        top.setStyleSheet(
            """
            QLabel {
                color: #718196;
                font-size: 8px;
                font-weight: 800;
            }
            """
        )

        value_row = QHBoxLayout()
        value_row.setSpacing(
            7
        )

        value_label = QLabel(
            value
        )
        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: #F3F7FB;
                font-size: 17px;
                font-weight: 850;
            }}
            """
        )

        suffix_label = QLabel(
            suffix
        )
        suffix_label.setStyleSheet(
            f"""
            QLabel {{
                color: {accent};
                font-size: 8px;
                font-weight: 800;
            }}
            """
        )

        value_row.addWidget(
            value_label
        )
        value_row.addWidget(
            suffix_label
        )
        value_row.addStretch()

        layout.addWidget(
            top
        )
        layout.addLayout(
            value_row
        )

        card.value_label = value_label

        return card

    def _bottom_card(
        self,
        title,
        value,
        subtitle,
        positive=None,
    ):
        card = QFrame()
        card.setStyleSheet(
            """
            QFrame {
                background: #101923;
                border: 1px solid #1F2C3A;
                border-radius: 10px;
            }
            """
        )

        layout = QVBoxLayout(
            card
        )
        layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )
        layout.setSpacing(
            3
        )

        title_label = QLabel(
            title
        )
        title_label.setStyleSheet(
            """
            QLabel {
                color: #718196;
                font-size: 8px;
                font-weight: 800;
            }
            """
        )

        value_label = QLabel(
            value
        )

        if positive is True:
            value_color = "#2FE393"
        elif positive is False:
            value_color = "#FF5F68"
        else:
            value_color = "#F2F6FB"

        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {value_color};
                font-size: 20px;
                font-weight: 850;
            }}
            """
        )

        sub_label = QLabel(
            subtitle
        )
        sub_label.setStyleSheet(
            """
            QLabel {
                color: #69798E;
                font-size: 8px;
            }
            """
        )

        layout.addWidget(
            title_label
        )
        layout.addWidget(
            value_label
        )
        layout.addWidget(
            sub_label
        )

        card.value_label = value_label
        card.subtitle_label = sub_label

        return card

    def _filter_button(
        self,
        text,
        active,
    ):
        button = QPushButton(
            text
        )
        button.setCheckable(
            False
        )

        if active:
            self._style_filter_button(
                button,
                True,
            )
        else:
            self._style_filter_button(
                button,
                False,
            )

        return button

    @staticmethod
    def _style_filter_button(
        button,
        active,
    ):
        if active:
            button.setStyleSheet(
                """
                QPushButton {
                    color: white;
                    background: #0A84FF;
                    border: 1px solid #2B95FF;
                    border-radius: 7px;
                    padding: 8px 12px;
                    font-size: 9px;
                    font-weight: 800;
                }
                """
            )
        else:
            button.setStyleSheet(
                """
                QPushButton {
                    color: #C8D4E3;
                    background: #121C27;
                    border: 1px solid #283647;
                    border-radius: 7px;
                    padding: 8px 12px;
                    font-size: 9px;
                    font-weight: 700;
                }

                QPushButton:hover {
                    background: #182535;
                }
                """
            )

    def _set_filter(
        self,
        mode,
    ):
        self.filter_mode = mode

        self._style_filter_button(
            self.all_button,
            mode == "all",
        )
        self._style_filter_button(
            self.active_button,
            mode == "active",
        )
        self._style_filter_button(
            self.completed_button,
            mode == "completed",
        )

        self._apply_filters()

    def _apply_filters(
        self,
        *_,
    ):
        if not hasattr(
            self,
            "filter_mode",
        ):
            self.filter_mode = "all"

        query = (
            self.search.text()
            .strip()
            .lower()
        )

        status_filter = (
            self.status_combo.currentText()
        )

        instrument_filter = (
            self.instrument_combo.currentText()
        )

        filtered = []

        for trade in self.all_trades:

            status = str(
                trade.get(
                    "status",
                    "LIVE",
                )
            )

            terminal = is_terminal_status(
                status
            )

            if (
                self.filter_mode
                == "active"
                and terminal
            ):
                continue

            if (
                self.filter_mode
                == "completed"
                and not terminal
            ):
                continue

            if (
                status_filter
                != "By Status"
                and status != status_filter
            ):
                continue

            instrument = str(
                trade.get(
                    "instrument",
                    trade.get(
                        "index",
                        "",
                    ),
                )
            )

            if (
                instrument_filter
                != "By Instrument"
                and instrument != instrument_filter
            ):
                continue

            if query:
                haystack = " ".join(
                    [
                        instrument,
                        status,
                        str(
                            trade.get(
                                "type",
                                "",
                            )
                        ),
                        str(
                            trade.get(
                                "strike",
                                "",
                            )
                        ),
                        str(
                            trade.get(
                                "ai_score",
                                "",
                            )
                        ),
                    ]
                ).lower()

                if query not in haystack:
                    continue

            filtered.append(
                trade
            )

        self.filtered_trades = filtered
        self._render_rows()

    # ======================================================
    # Data / render
    # ======================================================

    def update_trades(
        self,
        trades,
    ):
        self.all_trades = [
            dict(t)
            for t in (
                trades or []
            )
            if isinstance(
                t,
                dict,
            )
        ]

        self._update_summary()
        self._apply_filters()

    def _clear_content(
        self,
    ):
        while (
            self.content_layout.count()
            > 0
        ):
            item = (
                self.content_layout.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _section_header(
        self,
        title,
        count,
        color,
        right_text="",
    ):
        row = QHBoxLayout()

        label = QLabel(
            f"{title} ({count})"
        )
        label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 10px;
                font-weight: 850;
            }}
            """
        )

        row.addWidget(
            label
        )
        row.addStretch()

        if right_text:
            total = QLabel(
                right_text
            )
            total.setStyleSheet(
                """
                QLabel {
                    color: #75859A;
                    font-size: 9px;
                }
                """
            )
            row.addWidget(
                total
            )

        return row

    def _column_header(
        self,
    ):
        frame = QFrame()
        frame.setStyleSheet(
            """
            QFrame {
                background: #0F1720;
                border: 1px solid #1D2A38;
                border-radius: 8px;
            }
            """
        )

        layout = QGridLayout(
            frame
        )
        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )
        layout.setHorizontalSpacing(
            12
        )

        headers = [
            "STATUS",
            "INSTRUMENT",
            "TYPE",
            "STRIKE",
            "ENTRY\nPREMIUM",
            "1-LOT\nCAPITAL",
            "LIVE\nPRICE",
            "QTY\nLOTS",
            "STOP\nLOSS",
            "TARGET 1",
            "TARGET 2",
            "P&L /\nPOINT",
            "TOTAL P&L",
            "AI SCORE /\nPROB.",
            "ACTIONS",
        ]

        widths = [
            100,
            75,
            35,
            60,
            80,
            95,
            82,
            42,
            75,
            75,
            75,
            75,
            85,
            90,
            34,
        ]

        for index, (
            header,
            width,
        ) in enumerate(
            zip(
                headers,
                widths,
            )
        ):
            label = QLabel(
                header
            )
            label.setStyleSheet(
                """
                QLabel {
                    color: #6F8094;
                    font-size: 8px;
                    font-weight: 800;
                }
                """
            )
            layout.addWidget(
                label,
                0,
                index,
            )
            layout.setColumnMinimumWidth(
                index,
                width,
            )

        return frame

    def _render_rows(
        self,
    ):
        self._clear_content()

        active = [
            t
            for t in self.filtered_trades
            if not is_terminal_status(
                t.get(
                    "status"
                )
            )
        ]

        completed = [
            t
            for t in self.filtered_trades
            if is_terminal_status(
                t.get(
                    "status"
                )
            )
        ]

        if (
            not active
            and not completed
        ):
            empty = QFrame()
            empty.setStyleSheet(
                """
                QFrame {
                    background: #101923;
                    border: 1px solid #1F2C3A;
                    border-radius: 12px;
                }
                """
            )

            empty_layout = QVBoxLayout(
                empty
            )
            empty_layout.setContentsMargins(
                20,
                24,
                20,
                24,
            )

            empty_label = QLabel(
                "No trades match the current filters."
            )
            empty_label.setAlignment(
                Qt.AlignCenter
            )
            empty_label.setStyleSheet(
                """
                QLabel {
                    color: #75869B;
                    font-size: 12px;
                    font-weight: 600;
                }
                """
            )

            empty_layout.addWidget(
                empty_label
            )

            self.content_layout.addWidget(
                empty
            )
            self.content_layout.addStretch()
            return

        if active:
            self.content_layout.addLayout(
                self._section_header(
                    "ACTIVE TRADES",
                    len(active),
                    "#25E88F",
                )
            )

            self.content_layout.addWidget(
                self._column_header()
            )

            for trade in active:
                self.content_layout.addWidget(
                    TradeRow(
                        trade,
                        completed=False,
                    )
                )

        if completed:
            if active:
                self.content_layout.addSpacing(
                    6
                )

            completed_pnl = sum(
                number(
                    trade.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                for trade in completed
            )

            self.content_layout.addLayout(
                self._section_header(
                    "COMPLETED TRADES",
                    len(completed),
                    "#58B7FF",
                    (
                        f"Total P&L (Completed): "
                        f"{money(completed_pnl)}"
                    ),
                )
            )

            self.content_layout.addWidget(
                self._column_header()
            )

            for trade in completed:
                self.content_layout.addWidget(
                    TradeRow(
                        trade,
                        completed=True,
                    )
                )

        self.content_layout.addStretch()

    def _update_summary(
        self,
    ):
        active = [
            t
            for t in self.all_trades
            if not is_terminal_status(
                t.get(
                    "status"
                )
            )
        ]

        completed = [
            t
            for t in self.all_trades
            if is_terminal_status(
                t.get(
                    "status"
                )
            )
        ]

        total_pnl = sum(
            number(
                t.get(
                    "total_pnl",
                    0,
                ),
                0,
            )
            for t in self.all_trades
        )

        one_lot_capital = sum(
            number(
                t.get(
                    "capital_required_1_lot",
                    number(
                        t.get(
                            "fixed_entry",
                            t.get(
                                "entry",
                                0,
                            ),
                        ),
                        0,
                    )
                    * number(
                        t.get(
                            "lot_size",
                            t.get(
                                "quantity",
                                1,
                            ),
                        ),
                        1,
                    ),
                ),
                0,
            )
            for t in self.all_trades
        )

        self.active_card.value_label.setText(
            str(
                len(active)
            )
        )

        self.history_card.value_label.setText(
            str(
                len(completed)
            )
        )

        self.capital_card.value_label.setText(
            money(
                one_lot_capital
            )
        )

        self.pnl_card.value_label.setText(
            (
                f"+{money(abs(total_pnl))}"
                if total_pnl >= 0
                else f"-{money(abs(total_pnl))}"
            )
        )

        self.pnl_card.value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {
                    "#25E88F"
                    if total_pnl >= 0
                    else "#FF5F68"
                };
                font-size: 17px;
                font-weight: 850;
            }}
            """
        )

        # Bottom metrics.
        total_count = (
            len(
                self.all_trades
            )
        )

        wins = sum(
            1
            for t in completed
            if "TARGET" in str(
                t.get("status")
            )
        )

        losses = sum(
            1
            for t in completed
            if "STOP LOSS" in str(
                t.get("status")
            )
        )

        resolved = (
            wins + losses
        )

        win_rate = (
            (
                wins
                / resolved
                * 100
            )
            if resolved
            else 0
        )

        best = max(
            (
                number(
                    t.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                for t in completed
            ),
            default=0,
        )

        worst = min(
            (
                number(
                    t.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                for t in completed
            ),
            default=0,
        )

        avg = (
            sum(
                number(
                    t.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                for t in completed
            )
            / len(completed)
            if completed
            else 0
        )

        gross_profit = sum(
            number(
                t.get(
                    "total_pnl",
                    0,
                ),
                0,
            )
            for t in completed
            if number(
                t.get(
                    "total_pnl",
                    0,
                ),
                0,
            ) > 0
        )

        gross_loss = abs(
            sum(
                number(
                    t.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                for t in completed
                if number(
                    t.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                ) < 0
            )
        )

        profit_factor = (
            gross_profit / gross_loss
            if gross_loss
            else 0
        )

        self.total_card.value_label.setText(
            str(
                total_count
            )
        )

        self.win_card.value_label.setText(
            f"{win_rate:.2f}%"
        )

        self.win_card.subtitle_label.setText(
            f"{wins} wins / {losses} losses"
        )

        self.best_card.value_label.setText(
            money(best)
        )
        self.best_card.subtitle_label.setText(
            "Target hit"
            if best > 0
            else "—"
        )

        self.worst_card.value_label.setText(
            money(worst)
        )
        self.worst_card.subtitle_label.setText(
            "Stop loss hit"
            if worst < 0
            else "—"
        )

        self.avg_card.value_label.setText(
            money(avg)
        )

        self.factor_card.value_label.setText(
            (
                f"{profit_factor:.2f}"
                if completed
                else "—"
            )
        )

    def _export_visible(
        self,
    ):
        """
        Lightweight export hook.

        The tracking data remains available through self.filtered_trades.
        Main application integrations can replace this with QFileDialog
        export without changing the tracking data model.
        """
        self.subtitle.setText(
            f"{len(self.filtered_trades)} visible trades"
            " • Use the current tracker store for export."
        )