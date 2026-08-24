from __future__ import annotations

import pandas as pd

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
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


def date_part(value):
    if not value:
        return "—"
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return "—"
        return parsed.strftime("%d-%b-%Y")
    except Exception:
        return "—"


def time_part(value):
    if not value:
        return "—"
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return "—"
        return parsed.strftime("%H:%M:%S")
    except Exception:
        text = str(value)
        return text.split("T", 1)[-1][:8]


def is_terminal_status(status):
    return str(status or "").upper() in TERMINAL_STATUSES


def terminal_color(status):
    status = str(status or "").upper()
    if "TARGET" in status:
        return "#24E38A"
    if "STOP LOSS" in status:
        return "#FF5D68"
    if status == "DAY ENDED":
        return "#F5C84B"
    return "#7B8EA6"


class TradeTrackingPage(QWidget):
    """
    TradingAI Pro Trade Tracking page.

    Public integration contract intentionally kept small:
      - update_trades(trades)
      - action_clicked Signal(dict)

    The page uses QTableWidget rather than hundreds of nested widgets, which
    makes repeated live updates much cheaper and keeps column alignment stable.
    """

    action_clicked = Signal(dict)

    def __init__(self):
        super().__init__()

        self.all_trades = []
        self.filtered_trades = []
        self.filter_mode = "all"

        self.setObjectName("TradeTrackingPage")

        self.setStyleSheet(
            """
            QWidget#TradeTrackingPage {
                background: #080D14;
                color: #EAF1F8;
            }

            QLabel {
                background: transparent;
                border: none;
            }

            QFrame#metricCard,
            QFrame#toolbarCard,
            QFrame#sectionCard {
                background: #0D1622;
                border: 1px solid #1D2B3A;
                border-radius: 12px;
            }

            QLineEdit,
            QComboBox {
                color: #E7EEF7;
                background: #0B141F;
                border: 1px solid #243547;
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 10px;
            }

            QLineEdit:focus,
            QComboBox:hover {
                border: 1px solid #2B8DFF;
            }

            QComboBox QAbstractItemView {
                color: #EAF2FA;
                background: #0C1621;
                border: 1px solid #243547;
                selection-background-color: #0A84FF;
                selection-color: white;
                padding: 4px;
                outline: none;
            }

            QPushButton {
                color: #DCE7F2;
                background: #101C29;
                border: 1px solid #26384B;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 10px;
                font-weight: 700;
            }

            QPushButton:hover {
                background: #17283A;
                border: 1px solid #2B8DFF;
            }

            QPushButton#activeFilter {
                color: white;
                background: #087EF5;
                border: 1px solid #2E9BFF;
            }

            QTableWidget {
                background: transparent;
                color: #DDE8F4;
                border: 0px;
                gridline-color: #172535;
                font-size: 10px;
                selection-background-color: #12263A;
                selection-color: #F4F8FC;
                alternate-background-color: #0D1722;
            }

            QTableWidget::item {
                padding: 7px 6px;
                border-bottom: 1px solid #172535;
            }

            QTableWidget::item:selected {
                background: #12263A;
            }

            QHeaderView::section {
                background: #0A121C;
                color: #71849A;
                border: none;
                border-bottom: 1px solid #1A2A3A;
                padding: 8px 6px;
                font-size: 9px;
                font-weight: 800;
            }

            QScrollBar:vertical {
                background: #080D14;
                width: 10px;
            }

            QScrollBar::handle:vertical {
                background: #26384B;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        # ---------------------------------------------------------
        # HEADER
        # ---------------------------------------------------------

        header = QHBoxLayout()
        header.setSpacing(8)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        title = QLabel("Trade Tracking")
        title.setStyleSheet(
            """
            QLabel {
                color: #F7FAFF;
                font-size: 25px;
                font-weight: 850;
            }
            """
        )

        self.subtitle = QLabel(
            "Live AI trade monitoring • Fixed entry • Live premium • Lot size"
        )
        self.subtitle.setStyleSheet(
            """
            QLabel {
                color: #73869A;
                font-size: 10px;
            }
            """
        )

        title_box.addWidget(title)
        title_box.addWidget(self.subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.market_live = QLabel("●  MARKET LIVE")
        self.market_live.setStyleSheet(
            """
            QLabel {
                color: #28E58D;
                font-size: 10px;
                font-weight: 800;
                padding: 6px 9px;
            }
            """
        )

        header.addWidget(self.market_live)

        self.refresh_label = QLabel("Auto refresh")
        self.refresh_label.setStyleSheet(
            """
            QLabel {
                color: #8192A5;
                font-size: 9px;
            }
            """
        )

        header.addWidget(self.refresh_label)

        root.addLayout(header)

        # ---------------------------------------------------------
        # SUMMARY CARDS
        # ---------------------------------------------------------

        summary = QHBoxLayout()
        summary.setSpacing(10)

        self.active_card = self._metric_card(
            "ACTIVE TRADES",
            "0",
            "Open positions running",
            "#24E38A",
        )
        self.completed_card = self._metric_card(
            "COMPLETED TRADES",
            "0",
            "Closed positions",
            "#4D9EFF",
        )
        self.capital_card = self._metric_card(
            "1-LOT CAPITAL",
            "₹0.00",
            "Per tracked allocation",
            "#A875FF",
        )
        self.pnl_card = self._metric_card(
            "TOTAL P&L",
            "₹0.00",
            "Overall profit / loss",
            "#FF5D68",
        )
        self.win_card = self._metric_card(
            "WIN RATE",
            "0.00%",
            "0 wins / 0 losses",
            "#24E38A",
        )

        for card in (
            self.active_card,
            self.completed_card,
            self.capital_card,
            self.pnl_card,
            self.win_card,
        ):
            summary.addWidget(card, 1)

        root.addLayout(summary)

        # ---------------------------------------------------------
        # TOOLBAR
        # ---------------------------------------------------------

        toolbar = QFrame()
        toolbar.setObjectName("toolbarCard")

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 8, 10, 8)
        toolbar_layout.setSpacing(8)

        self.all_button = self._filter_button("All Trades")
        self.active_button = self._filter_button("Active")
        self.completed_button = self._filter_button("Completed")

        self.all_button.clicked.connect(
            lambda: self._set_filter("all")
        )
        self.active_button.clicked.connect(
            lambda: self._set_filter("active")
        )
        self.completed_button.clicked.connect(
            lambda: self._set_filter("completed")
        )

        toolbar_layout.addWidget(self.all_button)
        toolbar_layout.addWidget(self.active_button)
        toolbar_layout.addWidget(self.completed_button)

        self.status_combo = QComboBox()
        self.status_combo.addItems(
            [
                "All Status",
                "LIVE",
                "TARGET 1 HIT",
                "TARGET 2 HIT",
                "STOP LOSS HIT",
                "DAY ENDED",
            ]
        )
        self.status_combo.currentIndexChanged.connect(self._apply_filters)

        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems(
            [
                "All Instruments",
                "NIFTY 50",
                "BANK NIFTY",
                "FINNIFTY",
            ]
        )
        self.instrument_combo.currentIndexChanged.connect(
            self._apply_filters
        )

        self.type_combo = QComboBox()
        self.type_combo.addItems(
            ["All Types", "CE", "PE"]
        )
        self.type_combo.currentIndexChanged.connect(
            self._apply_filters
        )

        toolbar_layout.addWidget(self.status_combo)
        toolbar_layout.addWidget(self.instrument_combo)
        toolbar_layout.addWidget(self.type_combo)
        toolbar_layout.addSpacing(5)

        toolbar_layout.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search by instrument, strike, status..."
        )
        self.search.setMinimumWidth(260)
        self.search.textChanged.connect(self._apply_filters)

        toolbar_layout.addWidget(self.search)

        self.export_button = QPushButton("⇩  Export")
        self.export_button.clicked.connect(self._export_visible)
        toolbar_layout.addWidget(self.export_button)

        root.addWidget(toolbar)

        # ---------------------------------------------------------
        # CONTENT
        # ---------------------------------------------------------

        self.scroll = QTableWidget()
        self.scroll.setColumnCount(16)
        self.scroll.setHorizontalHeaderLabels(
            [
                "STATUS",
                "INSTRUMENT",
                "TYPE",
                "STRIKE",
                "START\nDATE / TIME",
                "END\nDATE / TIME",
                "ENTRY\nPREMIUM",
                "1-LOT\nCAPITAL",
                "LIVE\nPRICE",
                "QTY\nLOTS",
                "STOP\nLOSS",
                "TARGET 1",
                "TARGET 2",
                "TOTAL P&L",
                "AI SCORE /\nPROB.",
                "ACTIONS",
            ]
        )
        self.scroll.setAlternatingRowColors(True)
        self.scroll.verticalHeader().setVisible(False)
        self.scroll.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.scroll.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.scroll.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.scroll.setFocusPolicy(Qt.NoFocus)
        self.scroll.setShowGrid(False)

        header = self.scroll.horizontalHeader()
        header.setStretchLastSection(False)

        widths = [
            108, 95, 45, 64, 104, 104, 88, 100,
            88, 52, 82, 82, 82, 92, 105, 48,
        ]

        for i, width in enumerate(widths):
            header.setMinimumSectionSize(width)
            header.resizeSection(i, width)

        root.addWidget(self.scroll, 1)

        # ---------------------------------------------------------
        # BOTTOM PERFORMANCE
        # ---------------------------------------------------------

        performance = QHBoxLayout()
        performance.setSpacing(10)

        self.total_card = self._bottom_card(
            "TOTAL TRADES",
            "0",
            "All time",
        )
        self.best_card = self._bottom_card(
            "BEST TRADE",
            "₹0.00",
            "—",
            "#24E38A",
        )
        self.worst_card = self._bottom_card(
            "WORST TRADE",
            "₹0.00",
            "—",
            "#FF5D68",
        )
        self.avg_card = self._bottom_card(
            "AVG P&L / TRADE",
            "₹0.00",
            "Completed only",
        )
        self.factor_card = self._bottom_card(
            "PROFIT FACTOR",
            "—",
            "Gross profit / gross loss",
            "#A875FF",
        )

        for card in (
            self.total_card,
            self.best_card,
            self.worst_card,
            self.avg_card,
            self.factor_card,
        ):
            performance.addWidget(card, 1)

        root.addLayout(performance)

        footer = QLabel(
            "Data updates automatically • All prices are live • Times in IST"
        )
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            """
            QLabel {
                color: #536579;
                font-size: 9px;
                padding-top: 2px;
            }
            """
        )

        root.addWidget(footer)

    # =========================================================
    # UI HELPERS
    # =========================================================

    def _metric_card(
        self,
        title,
        value,
        subtitle,
        accent,
    ):
        card = QFrame()
        card.setObjectName("metricCard")
        card.setStyleSheet(
            f"""
            QFrame#metricCard {{
                background: #0D1622;
                border: 1px solid #1D2B3A;
                border-left: 3px solid {accent};
                border-radius: 12px;
            }}
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            QLabel {
                color: #71849A;
                font-size: 8px;
                font-weight: 800;
            }
            """
        )

        value_label = QLabel(value)
        value_label.setStyleSheet(
            """
            QLabel {
                color: #F3F7FC;
                font-size: 20px;
                font-weight: 850;
            }
            """
        )

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(
            """
            QLabel {
                color: #617287;
                font-size: 8px;
            }
            """
        )

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(subtitle_label)

        card.value_label = value_label
        card.subtitle_label = subtitle_label
        card.accent = accent

        return card

    def _bottom_card(
        self,
        title,
        value,
        subtitle,
        accent="#4D9EFF",
    ):
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background: #0D1622;
                border: 1px solid #1D2B3A;
                border-radius: 11px;
            }}
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(3)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            QLabel {
                color: #71849A;
                font-size: 8px;
                font-weight: 800;
            }
            """
        )

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {accent if accent else "#F3F7FC"};
                font-size: 19px;
                font-weight: 850;
            }}
            """
        )

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(
            """
            QLabel {
                color: #617287;
                font-size: 8px;
            }
            """
        )

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(subtitle_label)

        card.value_label = value_label
        card.subtitle_label = subtitle_label
        return card

    def _filter_button(self, text):
        button = QPushButton(text)
        button.setObjectName("activeFilter" if text == "All Trades" else "")
        return button

    def _set_filter(self, mode):
        self.filter_mode = mode

        for button, active in (
            (self.all_button, mode == "all"),
            (self.active_button, mode == "active"),
            (self.completed_button, mode == "completed"),
        ):
            button.setObjectName(
                "activeFilter" if active else ""
            )
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

        self._apply_filters()

    # =========================================================
    # DATA / FILTERING
    # =========================================================

    def update_trades(self, trades):
        self.all_trades = [
            dict(trade)
            for trade in (trades or [])
            if isinstance(trade, dict)
        ]

        self._update_summary()
        self._apply_filters()

    def _apply_filters(self, *_):
        query = self.search.text().strip().lower()
        status_filter = self.status_combo.currentText()
        instrument_filter = self.instrument_combo.currentText()
        type_filter = self.type_combo.currentText()

        mode = getattr(
            self,
            "filter_mode",
            "all",
        )

        filtered = []

        for trade in self.all_trades:
            status = str(
                trade.get("status", "LIVE")
            ).upper()

            completed = is_terminal_status(status)

            if mode == "active" and completed:
                continue

            if mode == "completed" and not completed:
                continue

            if (
                status_filter != "All Status"
                and status != status_filter
            ):
                continue

            instrument = str(
                trade.get(
                    "instrument",
                    trade.get("index", ""),
                )
            )

            if (
                instrument_filter != "All Instruments"
                and instrument != instrument_filter
            ):
                continue

            option_type = str(
                trade.get("type", "")
            ).upper()

            if (
                type_filter != "All Types"
                and option_type != type_filter
            ):
                continue

            if query:
                haystack = " ".join(
                    [
                        instrument,
                        option_type,
                        str(trade.get("strike", "")),
                        status,
                        str(trade.get("ai_score", "")),
                        str(trade.get("probability", "")),
                    ]
                ).lower()

                if query not in haystack:
                    continue

            filtered.append(trade)

        self.filtered_trades = filtered
        self._render_table()

    # =========================================================
    # TABLE
    # =========================================================

    def _render_table(self):
        """
        One table is intentionally used for the page.

        Rows are prefixed with a section marker row so the UI remains compact
        and column-perfect while being much cheaper to update than a widget
        hierarchy for every cell.
        """

        active = [
            trade
            for trade in self.filtered_trades
            if not is_terminal_status(
                trade.get("status")
            )
        ]

        completed = [
            trade
            for trade in self.filtered_trades
            if is_terminal_status(
                trade.get("status")
            )
        ]

        display_rows = []

        if active:
            display_rows.append(
                ("section", "ACTIVE TRADES")
            )
            display_rows.extend(
                ("trade", trade)
                for trade in active
            )

        if completed:
            display_rows.append(
                ("section", "COMPLETED TRADES")
            )
            display_rows.extend(
                ("trade", trade)
                for trade in completed
            )

        self.scroll.setRowCount(
            len(display_rows)
        )

        if not display_rows:
            self._show_empty()
            return

        # Clear all existing row cells.
        self.scroll.clearContents()

        for row_index, (
            kind,
            payload,
        ) in enumerate(display_rows):

            if kind == "section":
                self._set_section_row(
                    row_index,
                    payload,
                )
                continue

            self._set_trade_row(
                row_index,
                payload,
            )

        self.scroll.resizeRowsToContents()

    def _set_section_row(
        self,
        row,
        title,
    ):
        self.scroll.setSpan(
            row,
            0,
            1,
            self.scroll.columnCount(),
        )

        item = QTableWidgetItem(
            title
        )
        item.setFlags(
            Qt.ItemIsEnabled
        )
        item.setForeground(
            QColor(
                "#24E38A"
                if "ACTIVE" in title
                else "#58B7FF"
            )
        )
        item.setBackground(
            QColor("#0A121C")
        )
        font = item.font()
        font.setPointSize(9)
        font.setBold(True)
        item.setFont(font)

        self.scroll.setItem(
            row,
            0,
            item,
        )

    def _set_trade_row(
        self,
        row,
        trade,
    ):
        instrument = str(
            trade.get(
                "instrument",
                trade.get("index", "NIFTY 50"),
            )
        )

        option_type = str(
            trade.get("type", "")
        ).upper()

        strike_value = trade.get("strike")
        try:
            strike = (
                f"{float(strike_value):.0f}"
            )
        except Exception:
            strike = str(strike_value or "—")

        entry = number(
            trade.get(
                "fixed_entry",
                trade.get("entry"),
            ),
            0.0,
        )

        capital = number(
            trade.get(
                "capital_required_1_lot",
                entry
                * number(
                    trade.get(
                        "lot_size",
                        trade.get(
                            "quantity",
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

        quantity = int(
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

        total_pnl = number(
            trade.get(
                "total_pnl",
                (live - entry) * quantity,
            ),
            (live - entry) * quantity,
        )

        status = str(
            trade.get(
                "status",
                "LIVE",
            )
        ).upper()

        score = trade.get(
            "ai_score",
            "—",
        )

        probability = trade.get(
            "probability",
            "—",
        )

        values = [
            status,
            instrument,
            option_type,
            strike,
            f"{date_part(trade.get('started_at'))}\n"
            f"{time_part(trade.get('started_at'))}",
            f"{date_part(trade.get('ended_at'))}\n"
            f"{time_part(trade.get('ended_at'))}",
            money(entry),
            money(capital),
            money(live),
            str(quantity),
            money(
                trade.get(
                    "fixed_sl",
                    trade.get("sl"),
                )
            ),
            money(
                trade.get(
                    "fixed_target1",
                    trade.get("target1"),
                )
            ),
            money(
                trade.get(
                    "fixed_target2",
                    trade.get("target2"),
                )
            ),
            money(total_pnl),
            f"{score} / {probability}%",
            "⋮",
        ]

        for col, value in enumerate(values):
            item = QTableWidgetItem(
                str(value)
            )
            item.setTextAlignment(
                Qt.AlignCenter
            )

            if col == 0:
                item.setForeground(
                    QColor(
                        terminal_color(status)
                    )
                )
            elif col == 2:
                item.setForeground(
                    QColor(
                        "#38D99B"
                        if option_type == "CE"
                        else "#FF7C85"
                    )
                )
            elif col == 8:
                item.setForeground(
                    QColor(
                        "#24E38A"
                        if live >= entry
                        else "#FF5D68"
                    )
                )
            elif col == 13:
                item.setForeground(
                    QColor(
                        "#24E38A"
                        if total_pnl >= 0
                        else "#FF5D68"
                    )
                )
            elif col == 14:
                item.setForeground(
                    QColor("#F4CB44")
                )

            if col == 15:
                item.setTextAlignment(
                    Qt.AlignCenter
                )

            self.scroll.setItem(
                row,
                col,
                item,
            )

    def _show_empty(self):
        self.scroll.setRowCount(1)
        self.scroll.clearContents()
        self.scroll.setSpan(
            0,
            0,
            1,
            self.scroll.columnCount(),
        )

        item = QTableWidgetItem(
            "No trades match the current filters."
        )
        item.setTextAlignment(
            Qt.AlignCenter
        )
        item.setForeground(
            QColor("#71849A")
        )
        self.scroll.setItem(
            0,
            0,
            item,
        )

    # =========================================================
    # SUMMARY
    # =========================================================

    def _update_summary(self):
        active = [
            trade
            for trade in self.all_trades
            if not is_terminal_status(
                trade.get("status")
            )
        ]

        completed = [
            trade
            for trade in self.all_trades
            if is_terminal_status(
                trade.get("status")
            )
        ]

        all_pnl = [
            number(
                trade.get("total_pnl", 0),
                0.0,
            )
            for trade in self.all_trades
        ]

        total_pnl = sum(all_pnl)

        capital_total = 0.0
        for trade in self.all_trades:
            entry = number(
                trade.get(
                    "fixed_entry",
                    trade.get("entry"),
                ),
                0.0,
            )
            lot_size = number(
                trade.get(
                    "lot_size",
                    trade.get(
                        "quantity",
                        LOT_SIZES.get(
                            str(
                                trade.get(
                                    "instrument",
                                    "NIFTY 50",
                                )
                            ),
                            1,
                        ),
                    ),
                ),
                1,
            )
            capital_total += number(
                trade.get(
                    "capital_required_1_lot"
                ),
                entry * lot_size,
            )

        wins = sum(
            1
            for trade in completed
            if "TARGET" in str(
                trade.get("status", "")
            ).upper()
        )

        losses = sum(
            1
            for trade in completed
            if "STOP LOSS" in str(
                trade.get("status", "")
            ).upper()
        )

        resolved = wins + losses
        win_rate = (
            wins / resolved * 100
            if resolved
            else 0.0
        )

        self.active_card.value_label.setText(
            str(len(active))
        )
        self.completed_card.value_label.setText(
            str(len(completed))
        )
        self.capital_card.value_label.setText(
            money(capital_total)
        )
        self.pnl_card.value_label.setText(
            money(total_pnl)
        )
        self.pnl_card.value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {
                    "#24E38A"
                    if total_pnl >= 0
                    else "#FF5D68"
                };
                font-size: 20px;
                font-weight: 850;
            }}
            """
        )

        self.win_card.value_label.setText(
            f"{win_rate:.2f}%"
        )
        self.win_card.subtitle_label.setText(
            f"{wins} wins / {losses} losses"
        )

        total_count = len(self.all_trades)

        best = max(
            (
                number(
                    trade.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                for trade in completed
            ),
            default=0.0,
        )

        worst = min(
            (
                number(
                    trade.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                for trade in completed
            ),
            default=0.0,
        )

        avg = (
            sum(
                number(
                    trade.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                for trade in completed
            )
            / len(completed)
            if completed
            else 0.0
        )

        gross_profit = sum(
            number(
                trade.get(
                    "total_pnl",
                    0,
                ),
                0,
            )
            for trade in completed
            if number(
                trade.get(
                    "total_pnl",
                    0,
                ),
                0,
            )
            > 0
        )

        gross_loss = abs(
            sum(
                number(
                    trade.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                for trade in completed
                if number(
                    trade.get(
                        "total_pnl",
                        0,
                    ),
                    0,
                )
                < 0
            )
        )

        profit_factor = (
            gross_profit / gross_loss
            if gross_loss
            else 0.0
        )

        self.total_card.value_label.setText(
            str(total_count)
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
            f"{profit_factor:.2f}"
            if completed
            else "—"
        )

    def _export_visible(self):
        self.subtitle.setText(
            f"{len(self.filtered_trades)} visible trades • "
            "export hook ready"
        )