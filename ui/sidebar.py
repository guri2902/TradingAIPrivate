from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
)

from PySide6.QtCore import Signal

from ui import theme


class Sidebar(QWidget):

    # =========================================================
    # SIGNALS
    # =========================================================

    page_changed = Signal(str)

    generate_trade_clicked = Signal()

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self):

        super().__init__()

        self.setFixedWidth(
            210
        )

        self.setObjectName(
            "sidebar"
        )

        # =====================================================
        # STYLE
        # =====================================================

        self.setStyleSheet(
            f"""
            QWidget#sidebar {{
                background:
                    {theme.SURFACE};

                border-right:
                    1px solid
                    {theme.BORDER};
            }}

            QLabel {{
                color:#8B94A7;
                background:transparent;
                border:none;
            }}

            QPushButton {{
                color:#C9D1E1;
                background:transparent;

                border:none;
                border-radius:9px;

                text-align:left;

                padding-left:14px;
                padding-right:12px;

                font-size:13px;

                min-height:36px;
            }}

            QPushButton:hover {{
                background:{theme.CARD};
                color:white;
            }}

            QPushButton#activeButton {{
                background:{theme.CARD};
                color:white;
                font-weight:600;
            }}

            QPushButton#generateButton {{
                background:#0A84FF;
                color:white;

                border-radius:9px;

                font-size:13px;
                font-weight:600;

                padding:10px 14px;
            }}

            QPushButton#generateButton:hover {{
                background:#0077ED;
            }}
            """
        )

        # =====================================================
        # LAYOUT
        # =====================================================

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            10,
            12,
            10,
            12
        )

        layout.setSpacing(
            4
        )

        # =====================================================
        # BRAND
        # =====================================================

        brand = QLabel(
            "• TradingAI"
        )

        brand.setStyleSheet(
            """
            QLabel {
                color:white;
                font-size:17px;
                font-weight:700;
                padding-left:10px;
                padding-top:4px;
            }
            """
        )

        layout.addWidget(
            brand
        )

        subtitle = QLabel(
            "PRO TERMINAL"
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                color:#687286;
                font-size:8px;
                padding-left:10px;
                padding-bottom:20px;
            }
            """
        )

        layout.addWidget(
            subtitle
        )

        # =====================================================
        # WORKSPACE
        # =====================================================

        self.add_section(
            layout,
            "WORKSPACE"
        )

        self.dashboard_btn = QPushButton(
            "⌂   Dashboard"
        )

        self.scanner_btn = QPushButton(
            "✦   AI Scanner"
        )

        self.ai_trade_analysis_btn = QPushButton(
            "◉   AI Trade Analysis"
        )

        self.market_btn = QPushButton(
            "◈   Market"
        )

        self.option_btn = QPushButton(
            "▣   Option Chain"
        )

        self.tracking_btn = QPushButton(
            "◉   Tracking Trades (0)"
        )

        for button in (
            self.dashboard_btn,
            self.scanner_btn,
            self.ai_trade_analysis_btn,
            self.market_btn,
            self.option_btn,
            self.tracking_btn
        ):

            layout.addWidget(
                button
            )

        # =====================================================
        # RESEARCH
        # =====================================================

        self.add_section(
            layout,
            "RESEARCH"
        )

        self.journal_btn = QPushButton(
            "□   Trade Journal"
        )

        self.backtest_btn = QPushButton(
            "◷   Backtest"
        )

        layout.addWidget(
            self.journal_btn
        )

        layout.addWidget(
            self.backtest_btn
        )

        # =====================================================
        # RISK
        # =====================================================

        self.add_section(
            layout,
            "RISK"
        )

        self.risk_manager_btn = QPushButton(
            "⚠   Risk Manager"
        )

        layout.addWidget(
            self.risk_manager_btn
        )

        # =====================================================
        # SYSTEM
        # =====================================================

        self.add_section(
            layout,
            "SYSTEM"
        )

        self.settings_btn = QPushButton(
            "⚙   Settings"
        )

        layout.addWidget(
            self.settings_btn
        )

        layout.addStretch()

        # =====================================================
        # CONNECTION
        # =====================================================

        status_frame = QFrame()

        status_layout = QVBoxLayout(
            status_frame
        )

        status_layout.setContentsMargins(
            10,
            0,
            10,
            8
        )

        status = QLabel(
            "•  Connected"
        )

        status.setStyleSheet(
            """
            QLabel {
                color:#AEB8C8;
                font-size:10px;
            }
            """
        )

        status_layout.addWidget(
            status
        )

        layout.addWidget(
            status_frame
        )

        # =====================================================
        # GENERATE
        # =====================================================

        self.generate_btn = QPushButton(
            "✦  Generate AI Trade"
        )

        self.generate_btn.setObjectName(
            "generateButton"
        )

        self.generate_btn.setMinimumHeight(
            40
        )

        layout.addWidget(
            self.generate_btn
        )

        # =====================================================
        # PAGE MAP
        # =====================================================

        self.page_buttons = {

            "dashboard":
                self.dashboard_btn,

            "scanner":
                self.scanner_btn,

            "market":
                self.market_btn,

            "option_chain":
                self.option_btn,

            "tracking":
                self.tracking_btn,

            "journal":
                self.journal_btn,

            "backtest":
                self.backtest_btn,

            "risk_manager":
                self.risk_manager_btn,

            "settings":
                self.settings_btn,
        }

        # =====================================================
        # CONNECTIONS
        # =====================================================

        self.dashboard_btn.clicked.connect(
            lambda:
            self.navigate(
                "dashboard"
            )
        )

        self.scanner_btn.clicked.connect(
            lambda:
            self.navigate(
                "scanner"
            )
        )

        self.ai_trade_analysis_btn.clicked.connect(
            lambda:
            self.navigate(
                "ai_trade_analysis"
            )
        )

        self.market_btn.clicked.connect(
            lambda:
            self.navigate(
                "market"
            )
        )

        self.option_btn.clicked.connect(
            lambda:
            self.navigate(
                "option_chain"
            )
        )

        self.tracking_btn.clicked.connect(
            lambda:
            self.navigate(
                "tracking"
            )
        )

        self.journal_btn.clicked.connect(
            lambda:
            self.navigate(
                "journal"
            )
        )

        self.backtest_btn.clicked.connect(
            lambda:
            self.navigate(
                "backtest"
            )
        )

        self.risk_manager_btn.clicked.connect(
            lambda:
            self.navigate(
                "risk_manager"
            )
        )

        self.settings_btn.clicked.connect(
            lambda:
            self.navigate(
                "settings"
            )
        )

        self.generate_btn.clicked.connect(
            self.generate_trade_clicked.emit
        )

        # =====================================================
        # DEFAULT
        # =====================================================

        self.set_active_page(
            "dashboard"
        )

    # =========================================================
    # SECTION
    # =========================================================

    def add_section(
        self,
        layout,
        text
    ):

        label = QLabel(
            text
        )

        label.setStyleSheet(
            """
            QLabel {
                color:#7B8496;
                font-size:9px;
                font-weight:600;

                padding-left:10px;
                padding-top:14px;
                padding-bottom:5px;
            }
            """
        )

        layout.addWidget(
            label
        )

    # =========================================================
    # NAVIGATE
    # =========================================================

    def navigate(
        self,
        page
    ):

        self.set_active_page(
            page
        )

        self.page_changed.emit(
            page
        )

    # =========================================================
    # ACTIVE PAGE
    # =========================================================

    def set_active_page(
        self,
        page
    ):

        for name, button in self.page_buttons.items():

            if name == page:

                button.setObjectName(
                    "activeButton"
                )

            else:

                button.setObjectName(
                    ""
                )

            button.style().unpolish(
                button
            )

            button.style().polish(
                button
            )

            button.update()

    # =========================================================
    # TRACKING COUNT
    # =========================================================

    def set_tracking_count(
        self,
        count
    ):

        count = max(
            0,
            int(count)
        )

        self.tracking_btn.setText(
            f"◉   Tracking Trades ({count})"
        )

        if count > 0:

            self.tracking_btn.setStyleSheet(
                """
                QPushButton {
                    color:#34D399;
                    background:rgba(52,211,153,0.08);
                    border:none;
                    border-radius:9px;

                    text-align:left;

                    padding-left:14px;
                    padding-right:12px;

                    font-size:13px;
                    font-weight:700;

                    min-height:36px;
                }

                QPushButton:hover {
                    background:rgba(52,211,153,0.15);
                }

                QPushButton#activeButton {
                    background:rgba(52,211,153,0.15);
                    color:#34D399;
                }
                """
            )

        else:

            self.tracking_btn.setStyleSheet(
                ""
            )