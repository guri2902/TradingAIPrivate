from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QProgressBar,
    QDoubleSpinBox,
    QSpinBox,
    QSizePolicy,
)

from PySide6.QtCore import Qt

from ui import theme
from ui.trade_store import (
    today_pnl,
    today_trades,
    today_trade_count,
)

class RiskManager(QWidget):

    def __init__(self):
        super().__init__()

        # =====================================================
        # DEFAULT RISK SETTINGS
        # =====================================================

        self.capital = 22000.0
        self.risk_per_trade = 1.0
        self.daily_loss_limit = 1200.0
        self.daily_profit_target = 700.0

        # Current day values
        self.today_pnl = 0.0

        self.build_ui()
        self.refresh()
        self.capital = 22000.0
        self.risk_per_trade = 1.0
        self.daily_loss_limit = 1200.0
        self.daily_profit_target = 700.0

        self.today_pnl = 0.0
    # =========================================================
    # THEME
    # =========================================================

    def color(self, name, fallback):
        return getattr(theme, name, fallback)

    # =========================================================
    # BUILD UI
    # =========================================================

    def build_ui(self):

        self.setStyleSheet(f"""
            QWidget {{
                background: {self.color("BACKGROUND", "#0f1014")};
                color: {self.color("TEXT", "#e8eaf0")};
                font-family: "Segoe UI";
                font-size: 13px;
            }}

            QLabel {{
                background: transparent;
            }}

            QFrame#panel {{
                background: {self.color("SURFACE", "#17191f")};
                border: 1px solid {self.color("BORDER", "#292d36")};
                border-radius: 12px;
            }}

            QLabel#pageTitle {{
                font-size: 24px;
                font-weight: 700;
                color: {self.color("TEXT_PRIMARY", "#f5f7fa")};
            }}

            QLabel#subtitle {{
                color: {self.color("TEXT_SECONDARY", "#8f96a3")};
                font-size: 12px;
            }}

            QLabel#sectionTitle {{
                font-size: 14px;
                font-weight: 600;
                color: {self.color("TEXT_PRIMARY", "#f5f7fa")};
            }}

            QLabel#metricValue {{
                font-size: 22px;
                font-weight: 700;
                color: {self.color("TEXT_PRIMARY", "#f5f7fa")};
            }}

            QLabel#metricLabel {{
                color: {self.color("TEXT_SECONDARY", "#8f96a3")};
                font-size: 11px;
            }}

            QLabel#success {{
                color: #36d98b;
                font-weight: 600;
            }}

            QLabel#warning {{
                color: #f5b83d;
                font-weight: 600;
            }}

            QLabel#danger {{
                color: #ff5f57;
                font-weight: 600;
            }}

            QProgressBar {{
                background: #20232b;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}

            QProgressBar::chunk {{
                background: #1683ff;
                border-radius: 4px;
            }}

            QPushButton {{
                background: #1683ff;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: #3194ff;
            }}
        """)

        root = QVBoxLayout(self)

        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # =====================================================
        # HEADER
        # =====================================================

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        title = QLabel("Risk Manager")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Monitor capital, exposure and daily trading limits"
        )
        subtitle.setObjectName("subtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.refresh_btn = QPushButton("↻  Refresh")
        self.refresh_btn.clicked.connect(self.refresh)

        header.addWidget(self.refresh_btn)

        root.addLayout(header)

        # =====================================================
        # ACCOUNT OVERVIEW
        # =====================================================

        account_panel = self.create_panel()

        account_layout = QVBoxLayout(account_panel)
        account_layout.setContentsMargins(16, 14, 16, 14)
        account_layout.setSpacing(12)

        account_title = QLabel("ACCOUNT OVERVIEW")
        account_title.setObjectName("sectionTitle")

        account_layout.addWidget(account_title)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)

        self.capital_value = self.metric_card(
            metrics,
            "Trading Capital",
            "₹0.00"
        )

        self.pnl_value = self.metric_card(
            metrics,
            "Today's P&L",
            "₹0.00"
        )

        self.risk_value = self.metric_card(
            metrics,
            "Risk / Trade",
            "₹0.00"
        )

        self.target_value = self.metric_card(
            metrics,
            "Profit Target",
            "₹0.00"
        )

        account_layout.addLayout(metrics)

        root.addWidget(account_panel)

        # =====================================================
        # TWO COLUMN SECTION
        # =====================================================

        columns = QHBoxLayout()
        columns.setSpacing(16)

        # =====================================================
        # RISK STATUS
        # =====================================================

        status_panel = self.create_panel()

        status_layout = QVBoxLayout(status_panel)
        status_layout.setContentsMargins(16, 14, 16, 14)
        status_layout.setSpacing(12)

        status_title = QLabel("RISK STATUS")
        status_title.setObjectName("sectionTitle")

        status_layout.addWidget(status_title)

        self.status_label = QLabel("●  TRADING ALLOWED")
        self.status_label.setObjectName("success")

        self.status_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            padding: 8px 0;
        """)

        status_layout.addWidget(self.status_label)

        self.loss_remaining = QLabel("Loss remaining     ₹1,200.00")
        self.target_remaining = QLabel("Target remaining   ₹700.00")

        status_layout.addWidget(self.loss_remaining)
        status_layout.addWidget(self.target_remaining)

        status_layout.addStretch()

        columns.addWidget(status_panel, 1)

        # =====================================================
        # POSITION RISK
        # =====================================================

        position_panel = self.create_panel()

        position_layout = QVBoxLayout(position_panel)
        position_layout.setContentsMargins(16, 14, 16, 14)
        position_layout.setSpacing(12)

        position_title = QLabel("POSITION RISK")
        position_title.setObjectName("sectionTitle")

        position_layout.addWidget(position_title)

        self.max_risk_label = QLabel("Max Risk / Trade     ₹220.00")
        self.max_position_label = QLabel("Maximum Position   ₹220.00")

        position_layout.addWidget(self.max_risk_label)
        position_layout.addWidget(self.max_position_label)

        qty_row = QHBoxLayout()

        qty_label = QLabel("Suggested Quantity")

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100000)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setMinimumWidth(110)

        qty_row.addWidget(qty_label)
        qty_row.addStretch()
        qty_row.addWidget(self.quantity_spin)

        position_layout.addLayout(qty_row)

        position_layout.addStretch()

        columns.addWidget(position_panel, 1)

        root.addLayout(columns)

        # =====================================================
        # DAILY RISK
        # =====================================================

        daily_panel = self.create_panel()

        daily_layout = QVBoxLayout(daily_panel)
        daily_layout.setContentsMargins(16, 14, 16, 16)
        daily_layout.setSpacing(12)

        daily_title = QLabel("DAILY RISK")
        daily_title.setObjectName("sectionTitle")

        daily_layout.addWidget(daily_title)

        # Loss
        loss_header = QHBoxLayout()

        loss_header.addWidget(QLabel("Daily Loss Limit"))

        self.loss_percent = QLabel("0%")
        self.loss_percent.setAlignment(Qt.AlignRight)

        loss_header.addWidget(self.loss_percent)

        daily_layout.addLayout(loss_header)

        self.loss_progress = QProgressBar()
        self.loss_progress.setRange(0, 100)
        self.loss_progress.setValue(0)
        self.loss_progress.setTextVisible(False)

        daily_layout.addWidget(self.loss_progress)

        # Profit
        profit_header = QHBoxLayout()

        profit_header.addWidget(QLabel("Daily Profit Target"))

        self.profit_percent = QLabel("0%")
        self.profit_percent.setAlignment(Qt.AlignRight)

        profit_header.addWidget(self.profit_percent)

        daily_layout.addLayout(profit_header)

        self.profit_progress = QProgressBar()
        self.profit_progress.setRange(0, 100)
        self.profit_progress.setValue(0)
        self.profit_progress.setTextVisible(False)

        daily_layout.addWidget(self.profit_progress)

        root.addWidget(daily_panel)

        # =====================================================
        # RISK EVENTS
        # =====================================================

        events_panel = self.create_panel()

        events_layout = QVBoxLayout(events_panel)
        events_layout.setContentsMargins(16, 14, 16, 14)
        events_layout.setSpacing(8)

        events_title = QLabel("RISK EVENTS")
        events_title.setObjectName("sectionTitle")

        events_layout.addWidget(events_title)

        self.events = QLabel(
            "No risk events today."
        )

        self.events.setStyleSheet(
            f"color: {self.color('TEXT_SECONDARY', '#8f96a3')};"
        )

        events_layout.addWidget(self.events)

        root.addWidget(events_panel)

        root.addStretch()

    # =========================================================
    # PANEL
    # =========================================================

    def create_panel(self):

        panel = QFrame()
        panel.setObjectName("panel")

        panel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        return panel

    # =========================================================
    # METRIC CARD
    # =========================================================

    def metric_card(self, parent_layout, label, value):

        card = QFrame()
        card.setObjectName("panel")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")

        text_label = QLabel(label)
        text_label.setObjectName("metricLabel")

        layout.addWidget(value_label)
        layout.addWidget(text_label)

        parent_layout.addWidget(card)

        return value_label

    # =========================================================
    # REFRESH
    # =========================================================

    def refresh(self):
         # =====================================================
        # READ REAL JOURNAL DATA
        # =====================================================

        self.today_pnl = today_pnl()

        trades = today_trades()

        trade_count = len(trades)
        # -----------------------------------------------------
        # CALCULATIONS
        # -----------------------------------------------------

        risk_amount = (
            self.capital *
            self.risk_per_trade /
            100
        )

        loss_used = max(
            0.0,
            -self.today_pnl
        )

        profit_used = max(
            0.0,
            self.today_pnl
        )

        loss_remaining = max(
            0.0,
            self.daily_loss_limit - loss_used
        )

        profit_remaining = max(
            0.0,
            self.daily_profit_target - profit_used
        )

        loss_percentage = (
            loss_used /
            self.daily_loss_limit *
            100
            if self.daily_loss_limit > 0
            else 0
        )

        profit_percentage = (
            profit_used /
            self.daily_profit_target *
            100
            if self.daily_profit_target > 0
            else 0
        )

        # -----------------------------------------------------
        # ACCOUNT
        # -----------------------------------------------------

        self.capital_value.setText(
            f"₹{self.capital:,.2f}"
        )

        pnl_prefix = "+" if self.today_pnl > 0 else ""

        self.pnl_value.setText(
            f"{pnl_prefix}₹{self.today_pnl:,.2f}"
        )

        self.risk_value.setText(
            f"₹{risk_amount:,.2f}"
        )

        self.target_value.setText(
            f"₹{self.daily_profit_target:,.2f}"
        )

        # -----------------------------------------------------
        # P&L COLOR
        # -----------------------------------------------------

        if self.today_pnl > 0:

            self.pnl_value.setStyleSheet(
                "color: #36d98b;"
            )

        elif self.today_pnl < 0:

            self.pnl_value.setStyleSheet(
                "color: #ff5f57;"
            )

        else:

            self.pnl_value.setStyleSheet(
                f"color: {self.color('TEXT_PRIMARY', '#f5f7fa')};"
            )

        # -----------------------------------------------------
        # RISK STATUS
        # -----------------------------------------------------

        if loss_remaining <= 0:

            self.status_label.setText(
                "●  TRADING BLOCKED"
            )

            self.status_label.setStyleSheet(
                "color: #ff5f57; font-size: 15px; font-weight: 600;"
            )

        elif profit_used >= self.daily_profit_target:

            self.status_label.setText(
                "●  TARGET REACHED"
            )

            self.status_label.setStyleSheet(
                "color: #36d98b; font-size: 15px; font-weight: 600;"
            )

        else:

            self.status_label.setText(
                "●  TRADING ALLOWED"
            )

            self.status_label.setStyleSheet(
                "color: #36d98b; font-size: 15px; font-weight: 600;"
            )

        # -----------------------------------------------------
        # REMAINING
        # -----------------------------------------------------

        self.loss_remaining.setText(
            f"Loss remaining     ₹{loss_remaining:,.2f}"
        )

        self.target_remaining.setText(
            f"Target remaining   ₹{profit_remaining:,.2f}"
        )

        # -----------------------------------------------------
        # POSITION RISK
        # -----------------------------------------------------

        self.max_risk_label.setText(
            f"Max Risk / Trade     ₹{risk_amount:,.2f}"
        )

        self.max_position_label.setText(
            f"Maximum Position   ₹{risk_amount:,.2f}"
        )

        # -----------------------------------------------------
        # PROGRESS
        # -----------------------------------------------------

        loss_value = min(
            100,
            int(loss_percentage)
        )

        profit_value = min(
            100,
            int(profit_percentage)
        )

        self.loss_progress.setValue(loss_value)
        self.profit_progress.setValue(profit_value)

        self.loss_percent.setText(
            f"{loss_percentage:.1f}%"
        )

        self.profit_percent.setText(
            f"{profit_percentage:.1f}%"
        )

    # =========================================================
    # UPDATE P&L
    # =========================================================

    def set_today_pnl(self, pnl):

        self.today_pnl = float(pnl)

        self.refresh()