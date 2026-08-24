import json
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QComboBox,
    QLineEdit,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QDialogButtonBox,
    QMessageBox,
    QDateEdit,
)
from PySide6.QtCore import Qt, QDate

from ui import theme
from ui.trade_store import JOURNAL_FILE

# =========================================================
# SAFE THEME COLORS
# =========================================================

TEXT_PRIMARY = getattr(
    theme,
    "TEXT_PRIMARY",
    "#F5F7FA"
)

TEXT_SECONDARY = getattr(
    theme,
    "TEXT_SECONDARY",
    "#A7B0BE"
)


# =========================================================
# STORAGE
# =========================================================

JOURNAL_FILE = os.path.join(
    os.path.dirname(
        os.path.dirname(__file__)
    ),
    "trade_journal.json"
)


# =========================================================
# ADD / EDIT TRADE DIALOG
# =========================================================

class TradeDialog(QDialog):

    def __init__(self, trade=None, parent=None):

        super().__init__(parent)

        self.trade = trade or {}

        self.setWindowTitle(
            "Edit Trade"
            if trade
            else "Add Trade"
        )

        self.setMinimumWidth(420)

        self.build_ui()

        if trade:
            self.load_trade(trade)

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(14)

        title = QLabel(
            "Edit Trade"
            if self.trade
            else "Add Manual Trade"
        )

        title.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
        """)

        layout.addWidget(title)

        subtitle = QLabel(
            "Record a completed or open trade manually."
        )

        subtitle.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 11px;
            """
        )

        layout.addWidget(subtitle)

        form = QFormLayout()

        form.setSpacing(10)

        # -------------------------------------------------
        # DATE
        # -------------------------------------------------

        self.date = QDateEdit()

        self.date.setCalendarPopup(True)

        self.date.setDate(
            QDate.currentDate()
        )

        # -------------------------------------------------
        # INSTRUMENT
        # -------------------------------------------------

        self.instrument = QLineEdit()

        self.instrument.setPlaceholderText(
            "Example: 24600 PE"
        )

        # -------------------------------------------------
        # TYPE
        # -------------------------------------------------

        self.type_combo = QComboBox()

        self.type_combo.addItems([
            "CE",
            "PE",
            "FUT",
            "EQUITY"
        ])

        # -------------------------------------------------
        # ENTRY
        # -------------------------------------------------

        self.entry = QDoubleSpinBox()

        self.entry.setRange(
            0,
            10000000
        )

        self.entry.setDecimals(2)

        self.entry.setSingleStep(0.05)

        self.entry.setPrefix("₹ ")

        # -------------------------------------------------
        # EXIT
        # -------------------------------------------------

        self.exit = QDoubleSpinBox()

        self.exit.setRange(
            0,
            10000000
        )

        self.exit.setDecimals(2)

        self.exit.setSingleStep(0.05)

        self.exit.setPrefix("₹ ")

        # -------------------------------------------------
        # QUANTITY
        # -------------------------------------------------

        self.quantity = QSpinBox()

        self.quantity.setRange(
            1,
            1000000
        )

        self.quantity.setSingleStep(25)

        self.quantity.setValue(25)

        # -------------------------------------------------
        # AI SCORE
        # -------------------------------------------------

        self.ai_score = QSpinBox()

        self.ai_score.setRange(
            0,
            100
        )

        self.ai_score.setValue(0)

        # -------------------------------------------------
        # CONFIDENCE
        # -------------------------------------------------

        self.confidence = QSpinBox()

        self.confidence.setRange(
            0,
            100
        )

        self.confidence.setSuffix("%")

        self.confidence.setValue(0)

        # -------------------------------------------------
        # FORM
        # -------------------------------------------------

        form.addRow(
            "Date",
            self.date
        )

        form.addRow(
            "Instrument",
            self.instrument
        )

        form.addRow(
            "Type",
            self.type_combo
        )

        form.addRow(
            "Entry",
            self.entry
        )

        form.addRow(
            "Exit",
            self.exit
        )

        form.addRow(
            "Quantity",
            self.quantity
        )

        form.addRow(
            "AI Score",
            self.ai_score
        )

        form.addRow(
            "Confidence",
            self.confidence
        )

        layout.addLayout(form)

        # -------------------------------------------------
        # P&L PREVIEW
        # -------------------------------------------------

        self.pnl_preview = QLabel(
            "Estimated P&L: ₹0.00"
        )

        self.pnl_preview.setStyleSheet("""
            font-size: 15px;
            font-weight: 700;
        """)

        layout.addWidget(
            self.pnl_preview
        )

        self.entry.valueChanged.connect(
            self.update_pnl_preview
        )

        self.exit.valueChanged.connect(
            self.update_pnl_preview
        )

        self.quantity.valueChanged.connect(
            self.update_pnl_preview
        )

        # -------------------------------------------------
        # BUTTONS
        # -------------------------------------------------

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self.validate_and_accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(buttons)

        self.setStyleSheet(f"""

            QDialog {{
                background: {theme.BACKGROUND};
                color: {TEXT_PRIMARY};
            }}

            QLabel {{
                color: {TEXT_PRIMARY};
            }}

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox,
            QDateEdit {{
                background: {theme.SURFACE};
                color: {TEXT_PRIMARY};
                border: 1px solid {theme.BORDER};
                border-radius: 7px;
                padding: 7px;
            }}

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus,
            QDateEdit:focus {{
                border: 1px solid #2388ff;
            }}

            QPushButton {{
                background: #1683ff;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 8px 18px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: #2990ff;
            }}
        """)

    # =====================================================
    # LOAD TRADE
    # =====================================================

    def load_trade(self, trade):

        try:

            date = QDate.fromString(
                trade.get("date", ""),
                "yyyy-MM-dd"
            )

            if date.isValid():

                self.date.setDate(date)

            self.instrument.setText(
                trade.get(
                    "instrument",
                    ""
                )
            )

            trade_type = trade.get(
                "type",
                "CE"
            )

            index = self.type_combo.findText(
                trade_type
            )

            if index >= 0:

                self.type_combo.setCurrentIndex(
                    index
                )

            self.entry.setValue(
                float(
                    trade.get(
                        "entry",
                        0
                    )
                )
            )

            self.exit.setValue(
                float(
                    trade.get(
                        "exit",
                        0
                    )
                )
            )

            self.quantity.setValue(
                int(
                    trade.get(
                        "quantity",
                        25
                    )
                )
            )

            self.ai_score.setValue(
                int(
                    trade.get(
                        "ai_score",
                        0
                    )
                )
            )

            self.confidence.setValue(
                int(
                    trade.get(
                        "confidence",
                        0
                    )
                )
            )

            self.update_pnl_preview()

        except Exception:
            pass

    # =====================================================
    # P&L
    # =====================================================

    def calculate_pnl(self):

        entry = self.entry.value()

        exit_price = self.exit.value()

        quantity = self.quantity.value()

        return (
            exit_price - entry
        ) * quantity

    # =====================================================
    # P&L PREVIEW
    # =====================================================

    def update_pnl_preview(self):

        pnl = self.calculate_pnl()

        self.pnl_preview.setText(
            f"Estimated P&L: ₹{pnl:,.2f}"
        )

        if pnl > 0:

            self.pnl_preview.setStyleSheet("""
                color: #22c55e;
                font-size: 15px;
                font-weight: 700;
            """)

        elif pnl < 0:

            self.pnl_preview.setStyleSheet("""
                color: #ef4444;
                font-size: 15px;
                font-weight: 700;
            """)

        else:

            self.pnl_preview.setStyleSheet("""
                color: white;
                font-size: 15px;
                font-weight: 700;
            """)

    # =====================================================
    # VALIDATE
    # =====================================================

    def validate_and_accept(self):

        if not self.instrument.text().strip():

            QMessageBox.warning(
                self,
                "Missing Instrument",
                "Please enter an instrument."
            )

            return

        if self.entry.value() <= 0:

            QMessageBox.warning(
                self,
                "Invalid Entry",
                "Entry price must be greater than zero."
            )

            return

        if self.exit.value() <= 0:

            QMessageBox.warning(
                self,
                "Invalid Exit",
                "Exit price must be greater than zero."
            )

            return

        self.accept()

    # =====================================================
    # RETURN TRADE
    # =====================================================

    def get_trade(self):

        pnl = self.calculate_pnl()

        if pnl > 0:

            result = "WIN"

        elif pnl < 0:

            result = "LOSS"

        else:

            result = "BREAKEVEN"

        return {

            "date":
                self.date.date().toString(
                    "yyyy-MM-dd"
                ),

            "instrument":
                self.instrument.text().strip(),

            "type":
                self.type_combo.currentText(),

            "entry":
                round(
                    self.entry.value(),
                    2
                ),

            "exit":
                round(
                    self.exit.value(),
                    2
                ),

            "quantity":
                self.quantity.value(),

            "pnl":
                round(
                    pnl,
                    2
                ),

            "result":
                result,

            "ai_score":
                self.ai_score.value(),

            "confidence":
                self.confidence.value(),
        }


# =========================================================
# TRADE JOURNAL
# =========================================================

class TradeJournal(QWidget):

    def __init__(self):

        super().__init__()

        self.setObjectName(
            "tradeJournal"
        )

        self.trades = []

        self.build_ui()

        self.load_trades()

        self.refresh_table()

    # =====================================================
    # BUILD UI
    # =====================================================

    def build_ui(self):

        main = QVBoxLayout(self)

        main.setContentsMargins(
            28,
            22,
            28,
            22
        )

        main.setSpacing(16)

        # =================================================
        # HEADER
        # =================================================

        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title_box.setSpacing(4)

        title = QLabel(
            "Trade Journal"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "Track, review and analyse your trading performance"
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        title_box.addWidget(title)

        title_box.addWidget(subtitle)

        header.addLayout(title_box)

        header.addStretch()

        # FILTER

        self.filter_combo = QComboBox()

        self.filter_combo.addItems([
            "All Trades",
            "Winning Trades",
            "Losing Trades",
            "Open Trades",
        ])

        self.filter_combo.setFixedWidth(
            140
        )

        self.filter_combo.currentIndexChanged.connect(
            self.refresh_table
        )

        header.addWidget(
            self.filter_combo
        )

        # ADD

        self.add_btn = QPushButton(
            "＋  Add Trade"
        )

        self.add_btn.setFixedSize(
            115,
            36
        )

        self.add_btn.clicked.connect(
            self.add_trade_dialog
        )

        header.addWidget(
            self.add_btn
        )

        # EDIT

        self.edit_btn = QPushButton(
            "✎"
        )

        self.edit_btn.setToolTip(
            "Edit selected trade"
        )

        self.edit_btn.setFixedSize(
            40,
            36
        )

        self.edit_btn.clicked.connect(
            self.edit_selected_trade
        )

        header.addWidget(
            self.edit_btn
        )

        # DELETE

        self.delete_btn = QPushButton(
            "🗑"
        )

        self.delete_btn.setToolTip(
            "Delete selected trade"
        )

        self.delete_btn.setFixedSize(
            40,
            36
        )

        self.delete_btn.clicked.connect(
            self.delete_selected_trade
        )

        header.addWidget(
            self.delete_btn
        )

        # REFRESH

        self.refresh_btn = QPushButton(
            "⟳  Refresh"
        )

        self.refresh_btn.setFixedSize(
            105,
            36
        )

        self.refresh_btn.clicked.connect(
            self.refresh_table
        )

        header.addWidget(
            self.refresh_btn
        )

        main.addLayout(header)

        # =================================================
        # PERFORMANCE CARDS
        # =================================================

        cards = QHBoxLayout()

        cards.setSpacing(12)

        self.net_pnl = self.metric_card(
            "NET P&L",
            "₹0.00",
            "Overall performance"
        )

        self.total_trades = self.metric_card(
            "TOTAL TRADES",
            "0",
            "Executed trades"
        )

        self.win_rate = self.metric_card(
            "WIN RATE",
            "0%",
            "Winning percentage"
        )

        self.max_drawdown = self.metric_card(
            "MAX DRAWDOWN",
            "₹0.00",
            "Largest decline"
        )

        self.profit_factor = self.metric_card(
            "PROFIT FACTOR",
            "0.00",
            "Gross profit / loss"
        )

        cards.addWidget(
            self.net_pnl
        )

        cards.addWidget(
            self.total_trades
        )

        cards.addWidget(
            self.win_rate
        )

        cards.addWidget(
            self.max_drawdown
        )

        cards.addWidget(
            self.profit_factor
        )

        main.addLayout(cards)

        # =================================================
        # TABLE
        # =================================================

        table_panel = QFrame()

        table_panel.setObjectName(
            "panel"
        )

        table_layout = QVBoxLayout(
            table_panel
        )

        table_layout.setContentsMargins(
            14,
            12,
            14,
            14
        )

        table_layout.setSpacing(10)

        table_header = QHBoxLayout()

        table_title = QLabel(
            "Trade History"
        )

        table_title.setObjectName(
            "sectionTitle"
        )

        table_header.addWidget(
            table_title
        )

        table_header.addStretch()

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search trades..."
        )

        self.search.setFixedWidth(
            200
        )

        self.search.textChanged.connect(
            self.refresh_table
        )

        table_header.addWidget(
            self.search
        )

        table_layout.addLayout(
            table_header
        )

        self.table = QTableWidget()

        columns = [
            "DATE",
            "INSTRUMENT",
            "TYPE",
            "ENTRY",
            "EXIT",
            "QTY",
            "P&L",
            "RESULT",
            "AI SCORE",
            "CONFIDENCE",
        ]

        self.table.setColumnCount(
            len(columns)
        )

        self.table.setHorizontalHeaderLabels(
            columns
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.doubleClicked.connect(
            self.edit_selected_trade
        )

        header_view = (
            self.table.horizontalHeader()
        )

        for i in range(
            len(columns)
        ):

            header_view.setSectionResizeMode(
                i,
                QHeaderView.Stretch
            )

        table_layout.addWidget(
            self.table
        )

        main.addWidget(
            table_panel,
            1
        )

        # =================================================
        # ANALYTICS
        # =================================================

        analytics = QHBoxLayout()

        analytics.setSpacing(12)

        # TODAY

        today_panel = self.create_panel(
            "Today's Performance"
        )

        today_layout = (
            today_panel.layout()
        )

        self.today_pnl = self.info_row(
            today_layout,
            "P&L",
            "₹0.00"
        )

        self.today_trades = self.info_row(
            today_layout,
            "Trades",
            "0"
        )

        self.today_winrate = self.info_row(
            today_layout,
            "Win Rate",
            "0%"
        )

        analytics.addWidget(
            today_panel
        )

        # BEST

        best_panel = self.create_panel(
            "Best Trade"
        )

        best_layout = (
            best_panel.layout()
        )

        self.best_trade = self.info_row(
            best_layout,
            "Trade",
            "—"
        )

        self.best_profit = self.info_row(
            best_layout,
            "Profit",
            "₹0.00"
        )

        analytics.addWidget(
            best_panel
        )

        # WORST

        worst_panel = self.create_panel(
            "Worst Trade"
        )

        worst_layout = (
            worst_panel.layout()
        )

        self.worst_trade = self.info_row(
            worst_layout,
            "Trade",
            "—"
        )

        self.worst_loss = self.info_row(
            worst_layout,
            "Loss",
            "₹0.00"
        )

        analytics.addWidget(
            worst_panel
        )

        main.addLayout(
            analytics
        )

        # =================================================
        # STYLE
        # =================================================

        self.setStyleSheet(f"""

            QWidget#tradeJournal {{
                background: {theme.BACKGROUND};
            }}

            QLabel#pageTitle {{
                color: {TEXT_PRIMARY};
                font-size: 24px;
                font-weight: 700;
            }}

            QLabel#pageSubtitle {{
                color: {TEXT_SECONDARY};
                font-size: 12px;
            }}

            QLabel#sectionTitle {{
                color: {TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
            }}

            QFrame#panel {{
                background: {theme.SURFACE};
                border: 1px solid {theme.BORDER};
                border-radius: 10px;
            }}

            QComboBox,
            QLineEdit {{
                background: {theme.SURFACE};
                color: {TEXT_PRIMARY};
                border: 1px solid {theme.BORDER};
                border-radius: 7px;
                padding: 7px 10px;
            }}

            QComboBox:hover,
            QLineEdit:focus {{
                border: 1px solid #2388ff;
            }}

            QPushButton {{
                background: #1683ff;
                color: white;
                border: none;
                border-radius: 7px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: #2990ff;
            }}

            QTableWidget {{
                background: {theme.BACKGROUND};
                color: {TEXT_PRIMARY};
                border: 1px solid {theme.BORDER};
                gridline-color: {theme.BORDER};
                selection-background-color: #18395c;
                selection-color: white;
            }}

            QTableWidget::item {{
                padding: 7px;
            }}

            QHeaderView::section {{
                background: {theme.SURFACE};
                color: {TEXT_SECONDARY};
                border: none;
                border-bottom: 1px solid {theme.BORDER};
                padding: 8px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)

    # =====================================================
    # METRIC CARD
    # =====================================================

    def metric_card(
        self,
        label,
        value,
        description
    ):

        frame = QFrame()

        frame.setObjectName(
            "panel"
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            14,
            12,
            14,
            12
        )

        layout.setSpacing(5)

        label_widget = QLabel(
            label
        )

        label_widget.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 10px;
            font-weight: 600;
            """
        )

        value_widget = QLabel(
            value
        )

        value_widget.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: 700;
        """)

        description_widget = QLabel(
            description
        )

        description_widget.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 10px;
            """
        )

        layout.addWidget(
            label_widget
        )

        layout.addWidget(
            value_widget
        )

        layout.addWidget(
            description_widget
        )

        # Store value label

        frame.value_widget = value_widget

        return frame

    # =====================================================
    # PANEL
    # =====================================================

    def create_panel(
        self,
        title
    ):

        frame = QFrame()

        frame.setObjectName(
            "panel"
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            16,
            14,
            16,
            14
        )

        layout.setSpacing(8)

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            color: {TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 600;
            """
        )

        layout.addWidget(
            title_label
        )

        return frame

    # =====================================================
    # INFO ROW
    # =====================================================

    def info_row(
        self,
        layout,
        label,
        value
    ):

        row = QHBoxLayout()

        label_widget = QLabel(
            label
        )

        label_widget.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 11px;
            """
        )

        value_widget = QLabel(
            value
        )

        value_widget.setStyleSheet("""
            color: white;
            font-size: 12px;
            font-weight: 600;
        """)

        row.addWidget(
            label_widget
        )

        row.addStretch()

        row.addWidget(
            value_widget
        )

        layout.addLayout(
            row
        )

        return value_widget

    # =====================================================
    # STORAGE
    # =====================================================

    def load_trades(self):

        if not os.path.exists(
            JOURNAL_FILE
        ):

            self.trades = []

            return

        try:

            with open(
                JOURNAL_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

            if isinstance(
                data,
                list
            ):

                self.trades = data

            else:

                self.trades = []

        except Exception as e:

            print(
                "Trade journal load error:",
                e
            )

            self.trades = []

    # =====================================================
    # SAVE
    # =====================================================

    def save_trades(self):

        try:

            with open(
                JOURNAL_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.trades,
                    file,
                    indent=4
                )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Save Error",
                f"Could not save trade journal:\n{e}"
            )

    # =====================================================
    # ADD TRADE
    # =====================================================

    def add_trade_dialog(self):

        dialog = TradeDialog(
            parent=self
        )

        if dialog.exec() == QDialog.Accepted:

            trade = dialog.get_trade()

            self.trades.append(
                trade
            )

            self.save_trades()

            self.refresh_table()

    # =====================================================
    # EDIT TRADE
    # =====================================================

    def edit_selected_trade(
        self,
        *_args
    ):

        row = (
            self.table.currentRow()
        )

        if row < 0:

            QMessageBox.information(
                self,
                "Select Trade",
                "Please select a trade first."
            )

            return

        trade_index = (
            self.table.item(
                row,
                0
            ).data(
                Qt.UserRole
            )
        )

        if trade_index is None:

            return

        trade_index = int(
            trade_index
        )

        if trade_index >= len(
            self.trades
        ):

            return

        dialog = TradeDialog(
            self.trades[trade_index],
            self
        )

        if dialog.exec() == QDialog.Accepted:

            self.trades[
                trade_index
            ] = dialog.get_trade()

            self.save_trades()

            self.refresh_table()

    # =====================================================
    # DELETE
    # =====================================================

    def delete_selected_trade(self):

        row = (
            self.table.currentRow()
        )

        if row < 0:

            QMessageBox.information(
                self,
                "Select Trade",
                "Please select a trade first."
            )

            return

        trade_index = (
            self.table.item(
                row,
                0
            ).data(
                Qt.UserRole
            )
        )

        if trade_index is None:

            return

        trade_index = int(
            trade_index
        )

        trade = self.trades[
            trade_index
        ]

        answer = QMessageBox.question(
            self,
            "Delete Trade",
            f"Delete {trade.get('instrument', 'this trade')}?",
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:

            return

        del self.trades[
            trade_index
        ]

        self.save_trades()

        self.refresh_table()

    # =====================================================
    # REFRESH TABLE
    # =====================================================

    def refresh_table(self):

        if not hasattr(
            self,
            "table"
        ):

            return

        search_text = (
            self.search.text()
            .strip()
            .lower()
        )

        filter_value = (
            self.filter_combo.currentText()
        )

        self.table.setRowCount(
            0
        )

        for index, trade in enumerate(
            self.trades
        ):

            result = str(
                trade.get(
                    "result",
                    ""
                )
            ).upper()

            # FILTER

            if filter_value == "Winning Trades":

                if result != "WIN":

                    continue

            elif filter_value == "Losing Trades":

                if result != "LOSS":

                    continue

            elif filter_value == "Open Trades":

                if trade.get(
                    "exit"
                ) in (
                    None,
                    "",
                    0
                ):

                    pass

                else:

                    continue

            # SEARCH

            searchable = " ".join(
                str(
                    value
                )
                for value in trade.values()
            ).lower()

            if search_text and (
                search_text
                not in searchable
            ):

                continue

            row = (
                self.table.rowCount()
            )

            self.table.insertRow(
                row
            )

            values = [

                trade.get(
                    "date",
                    "—"
                ),

                trade.get(
                    "instrument",
                    "—"
                ),

                trade.get(
                    "type",
                    "—"
                ),

                f"₹{float(trade.get('entry', 0)):,.2f}",

                f"₹{float(trade.get('exit', 0)):,.2f}",

                str(
                    trade.get(
                        "quantity",
                        "—"
                    )
                ),

                f"₹{float(trade.get('pnl', 0)):,.2f}",

                trade.get(
                    "result",
                    "—"
                ),

                str(
                    trade.get(
                        "ai_score",
                        "—"
                    )
                ),

                f"{trade.get('confidence', 0)}%",
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

                    item.setData(
                        Qt.UserRole,
                        index
                    )

                self.table.setItem(
                    row,
                    column,
                    item
                )

                # P&L

                if column == 6:

                    pnl = float(
                        trade.get(
                            "pnl",
                            0
                        )
                    )

                    if pnl > 0:

                        item.setForeground(
                            Qt.green
                        )

                    elif pnl < 0:

                        item.setForeground(
                            Qt.red
                        )

                # RESULT

                if column == 7:

                    if result == "WIN":

                        item.setForeground(
                            Qt.green
                        )

                    elif result == "LOSS":

                        item.setForeground(
                            Qt.red
                        )

            self.table.setRowHeight(
                row,
                34
            )

        self.update_statistics()

    # =====================================================
    # STATISTICS
    # =====================================================

    def update_statistics(self):

        if not self.trades:

            self.set_metric(
                self.net_pnl,
                "₹0.00"
            )

            self.set_metric(
                self.total_trades,
                "0"
            )

            self.set_metric(
                self.win_rate,
                "0%"
            )

            self.set_metric(
                self.max_drawdown,
                "₹0.00"
            )

            self.set_metric(
                self.profit_factor,
                "0.00"
            )

            self.today_pnl.setText(
                "₹0.00"
            )

            self.today_trades.setText(
                "0"
            )

            self.today_winrate.setText(
                "0%"
            )

            self.best_trade.setText(
                "—"
            )

            self.best_profit.setText(
                "₹0.00"
            )

            self.worst_trade.setText(
                "—"
            )

            self.worst_loss.setText(
                "₹0.00"
            )

            return

        pnls = [

            float(
                trade.get(
                    "pnl",
                    0
                )
            )

            for trade in self.trades
        ]

        total_pnl = sum(
            pnls
        )

        total = len(
            self.trades
        )

        wins = sum(
            1
            for pnl in pnls
            if pnl > 0
        )

        losses = sum(
            1
            for pnl in pnls
            if pnl < 0
        )

        win_rate = (
            wins / total * 100
            if total
            else 0
        )

        # -------------------------------------------------
        # MAX DRAWDOWN
        # -------------------------------------------------

        equity = 0

        peak = 0

        max_drawdown = 0

        for pnl in pnls:

            equity += pnl

            peak = max(
                peak,
                equity
            )

            drawdown = (
                peak - equity
            )

            max_drawdown = max(
                max_drawdown,
                drawdown
            )

        # -------------------------------------------------
        # PROFIT FACTOR
        # -------------------------------------------------

        gross_profit = sum(
            pnl
            for pnl in pnls
            if pnl > 0
        )

        gross_loss = abs(
            sum(
                pnl
                for pnl in pnls
                if pnl < 0
            )
        )

        if gross_loss > 0:

            profit_factor = (
                gross_profit
                / gross_loss
            )

        elif gross_profit > 0:

            profit_factor = float(
                "inf"
            )

        else:

            profit_factor = 0

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        self.set_metric(
            self.net_pnl,
            f"₹{total_pnl:,.2f}"
        )

        self.set_metric(
            self.total_trades,
            str(total)
        )

        self.set_metric(
            self.win_rate,
            f"{win_rate:.1f}%"
        )

        self.set_metric(
            self.max_drawdown,
            f"₹{max_drawdown:,.2f}"
        )

        if profit_factor == float(
            "inf"
        ):

            pf_text = "∞"

        else:

            pf_text = (
                f"{profit_factor:.2f}"
            )

        self.set_metric(
            self.profit_factor,
            pf_text
        )

        # -------------------------------------------------
        # TODAY
        # -------------------------------------------------

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        today_trades = [

            trade
            for trade in self.trades
            if trade.get(
                "date"
            ) == today
        ]

        today_pnl = sum(
            float(
                trade.get(
                    "pnl",
                    0
                )
            )
            for trade in today_trades
        )

        today_wins = sum(
            1
            for trade in today_trades
            if float(
                trade.get(
                    "pnl",
                    0
                )
            ) > 0
        )

        today_count = len(
            today_trades
        )

        today_winrate = (

            today_wins
            / today_count
            * 100

            if today_count
            else 0
        )

        self.today_pnl.setText(
            f"₹{today_pnl:,.2f}"
        )

        self.today_trades.setText(
            str(today_count)
        )

        self.today_winrate.setText(
            f"{today_winrate:.1f}%"
        )

        # -------------------------------------------------
        # BEST
        # -------------------------------------------------

        best = max(
            self.trades,
            key=lambda x: float(
                x.get(
                    "pnl",
                    0
                )
            )
        )

        best_pnl = float(
            best.get(
                "pnl",
                0
            )
        )

        self.best_trade.setText(
            best.get(
                "instrument",
                "—"
            )
        )

        self.best_profit.setText(
            f"₹{best_pnl:,.2f}"
        )

        # -------------------------------------------------
        # WORST
        # -------------------------------------------------

        worst = min(
            self.trades,
            key=lambda x: float(
                x.get(
                    "pnl",
                    0
                )
            )
        )

        worst_pnl = float(
            worst.get(
                "pnl",
                0
            )
        )

        self.worst_trade.setText(
            worst.get(
                "instrument",
                "—"
            )
        )

        self.worst_loss.setText(
            f"₹{worst_pnl:,.2f}"
        )

    # =====================================================
    # METRIC UPDATE
    # =====================================================

    def set_metric(
        self,
        frame,
        value
    ):

        if hasattr(
            frame,
            "value_widget"
        ):

            frame.value_widget.setText(
                value
            )