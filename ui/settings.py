from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Signal, Qt

from config.settings_manager import (
    load_settings,
    save_settings,
)


class Settings(QWidget):

    settings_saved = Signal()

    def __init__(self):
        super().__init__()

        self.settings = load_settings()

        self.setObjectName("settingsPage")

        self.build_ui()
        self.load_values()

        self.apply_styles()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(
            30,
            24,
            30,
            24
        )

        root.setSpacing(18)

        # =================================================
        # HEADER
        # =================================================

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        title = QLabel("Settings")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Configure TradingAI Pro"
        )
        subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.save_button = QPushButton(
            "Save Changes"
        )

        self.save_button.setObjectName(
            "saveButton"
        )

        self.save_button.setFixedHeight(36)
        self.save_button.setMinimumWidth(120)

        self.save_button.clicked.connect(
            self.save
        )

        header.addWidget(
            self.save_button
        )

        root.addLayout(header)

        # =================================================
        # SCROLL
        # =================================================

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        scroll.setObjectName(
            "settingsScroll"
        )

        content = QWidget()
        content.setObjectName(
            "settingsContent"
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            20
        )

        content_layout.setSpacing(12)

        # =================================================
        # GENERAL
        # =================================================

        general = self.create_section(
            "General",
            "Application behaviour and appearance"
        )

        general_layout = general["layout"]

        self.start_page = QComboBox()

        self.start_page.addItems([
            "Dashboard",
            "AI Scanner",
            "Market",
            "Option Chain",
            "Trade Journal",
            "Settings",
        ])

        general_layout.addLayout(
            self.create_row(
                "Start Page",
                self.start_page
            )
        )

        self.auto_refresh = QSpinBox()

        self.auto_refresh.setRange(
            5,
            3600
        )

        self.auto_refresh.setSuffix(
            " sec"
        )

        general_layout.addLayout(
            self.create_row(
                "Auto Refresh",
                self.auto_refresh
            )
        )

        self.dark_interface = QCheckBox(
            "Dark interface"
        )

        general_layout.addWidget(
            self.dark_interface
        )

        content_layout.addWidget(
            general["frame"]
        )

        # =================================================
        # MARKET
        # =================================================

        market = self.create_section(
            "Market",
            "Default market and index configuration"
        )

        market_layout = market["layout"]

        self.default_index = QComboBox()

        self.default_index.addItems([
            "NIFTY 50",
            "BANK NIFTY",
            "FINNIFTY",
            "MIDCAP NIFTY",
        ])

        market_layout.addLayout(
            self.create_row(
                "Default Index",
                self.default_index
            )
        )

        self.option_expiry = QComboBox()

        self.option_expiry.addItems([
            "Nearest Expiry",
            "Next Expiry",
            "Weekly",
            "Monthly",
        ])

        market_layout.addLayout(
            self.create_row(
                "Option Expiry",
                self.option_expiry
            )
        )

        content_layout.addWidget(
            market["frame"]
        )

        # =================================================
        # AI
        # =================================================

        ai = self.create_section(
            "AI Analysis",
            "Control how TradingAI evaluates opportunities"
        )

        ai_layout = ai["layout"]

        self.minimum_confidence = QSpinBox()

        self.minimum_confidence.setRange(
            0,
            100
        )

        self.minimum_confidence.setSuffix(
            "%"
        )

        ai_layout.addLayout(
            self.create_row(
                "Minimum Confidence",
                self.minimum_confidence
            )
        )

        self.minimum_probability = QSpinBox()

        self.minimum_probability.setRange(
            0,
            100
        )

        self.minimum_probability.setSuffix(
            "%"
        )

        ai_layout.addLayout(
            self.create_row(
                "Minimum Probability",
                self.minimum_probability
            )
        )

        self.enable_ai_recommendations = QCheckBox(
            "Enable AI trade recommendations"
        )

        ai_layout.addWidget(
            self.enable_ai_recommendations
        )

        content_layout.addWidget(
            ai["frame"]
        )

        # =================================================
        # RISK
        # =================================================

        risk = self.create_section(
            "Risk Management",
            "Define your trading risk limits"
        )

        risk_layout = risk["layout"]

        self.trading_capital = QDoubleSpinBox()

        self.trading_capital.setRange(
            0,
            100000000
        )

        self.trading_capital.setDecimals(
            2
        )

        self.trading_capital.setPrefix(
            "₹ "
        )

        risk_layout.addLayout(
            self.create_row(
                "Trading Capital",
                self.trading_capital
            )
        )

        self.risk_per_trade = QDoubleSpinBox()

        self.risk_per_trade.setRange(
            0,
            100
        )

        self.risk_per_trade.setDecimals(
            2
        )

        self.risk_per_trade.setSuffix(
            "%"
        )

        risk_layout.addLayout(
            self.create_row(
                "Risk Per Trade",
                self.risk_per_trade
            )
        )

        self.daily_loss_limit = QDoubleSpinBox()

        self.daily_loss_limit.setRange(
            0,
            100000000
        )

        self.daily_loss_limit.setDecimals(
            2
        )

        self.daily_loss_limit.setPrefix(
            "₹ "
        )

        risk_layout.addLayout(
            self.create_row(
                "Daily Loss Limit",
                self.daily_loss_limit
            )
        )

        self.daily_profit_target = QDoubleSpinBox()

        self.daily_profit_target.setRange(
            0,
            100000000
        )

        self.daily_profit_target.setDecimals(
            2
        )

        self.daily_profit_target.setPrefix(
            "₹ "
        )

        risk_layout.addLayout(
            self.create_row(
                "Daily Profit Target",
                self.daily_profit_target
            )
        )

        content_layout.addWidget(
            risk["frame"]
        )

        # Keep content compact
        content_layout.addStretch()

        scroll.setWidget(
            content
        )

        root.addWidget(
            scroll,
            1
        )

    # =====================================================
    # SECTION
    # =====================================================

    def create_section(
        self,
        title_text,
        subtitle_text
    ):

        frame = QFrame()

        frame.setObjectName(
            "settingsSection"
        )

        outer = QVBoxLayout(frame)

        outer.setContentsMargins(
            16,
            14,
            16,
            14
        )

        outer.setSpacing(8)

        # Header
        header = QVBoxLayout()
        header.setSpacing(2)

        title = QLabel(
            title_text
        )

        title.setObjectName(
            "sectionTitle"
        )

        subtitle = QLabel(
            subtitle_text
        )

        subtitle.setObjectName(
            "sectionSubtitle"
        )

        header.addWidget(title)
        header.addWidget(subtitle)

        outer.addLayout(header)

        # Divider
        divider = QFrame()

        divider.setFrameShape(
            QFrame.HLine
        )

        divider.setObjectName(
            "sectionDivider"
        )

        outer.addWidget(
            divider
        )

        # Content
        content = QWidget()

        layout = QVBoxLayout(
            content
        )

        layout.setContentsMargins(
            0,
            3,
            0,
            0
        )

        layout.setSpacing(7)

        outer.addWidget(
            content
        )

        return {
            "frame": frame,
            "layout": layout,
        }

    # =====================================================
    # ROW
    # =====================================================

    def create_row(
        self,
        label_text,
        widget
    ):

        row = QHBoxLayout()

        row.setContentsMargins(
            0,
            0,
            0,
            0
        )

        row.setSpacing(20)

        label = QLabel(
            label_text
        )

        label.setObjectName(
            "settingLabel"
        )

        label.setFixedWidth(
            170
        )

        row.addWidget(
            label
        )

        row.addStretch()

        # Don't let controls stretch across entire screen
        widget.setFixedWidth(
            240
        )

        row.addWidget(
            widget
        )

        return row

    # =====================================================
    # STYLES
    # =====================================================

    def apply_styles(self):

        self.setStyleSheet("""
            /* =========================================
               PAGE
               ========================================= */

            QWidget#settingsPage {
                background: #0d0f12;
                color: #eef2f7;
            }

            /* =========================================
               HEADER
               ========================================= */

            QLabel#pageTitle {
                color: #f4f6f8;
                font-size: 22px;
                font-weight: 700;
            }

            QLabel#pageSubtitle {
                color: #7f8998;
                font-size: 11px;
            }

            QPushButton#saveButton {
                background: #1683ff;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 0 16px;
                font-size: 11px;
                font-weight: 600;
            }

            QPushButton#saveButton:hover {
                background: #2690ff;
            }

            QPushButton#saveButton:pressed {
                background: #0f70df;
            }

            /* =========================================
               SCROLL
               ========================================= */

            QScrollArea#settingsScroll {
                background: transparent;
                border: none;
            }

            QScrollArea#settingsScroll QWidget {
                background: transparent;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px 0 4px 0;
            }

            QScrollBar::handle:vertical {
                background: #303640;
                border-radius: 4px;
                min-height: 40px;
            }

            QScrollBar::handle:vertical:hover {
                background: #424a57;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            /* =========================================
               SECTIONS
               ========================================= */

            QFrame#settingsSection {
                background: #15181e;
                border: 1px solid #252a32;
                border-radius: 10px;
            }

            QLabel#sectionTitle {
                color: #f0f3f7;
                font-size: 14px;
                font-weight: 600;
            }

            QLabel#sectionSubtitle {
                color: #727c8c;
                font-size: 10px;
            }

            QFrame#sectionDivider {
                color: #252a32;
                background: #252a32;
                max-height: 1px;
            }

            QLabel#settingLabel {
                color: #c8ced8;
                font-size: 11px;
            }

            /* =========================================
               COMBO BOX
               ========================================= */

            QComboBox {
                background: #101318;
                color: #e9edf2;
                border: 1px solid #2a3039;
                border-radius: 6px;
                padding: 0 10px;
                min-height: 32px;
                font-size: 11px;
            }

            QComboBox:hover {
                border: 1px solid #3a424e;
            }

            QComboBox:focus {
                border: 1px solid #1683ff;
            }

            QComboBox::drop-down {
                width: 28px;
                border: none;
            }

            QComboBox QAbstractItemView {
                background: #171a20;
                color: #e9edf2;
                border: 1px solid #303641;
                selection-background-color: #1d6fc1;
                selection-color: white;
                padding: 4px;
            }

            /* =========================================
               SPIN BOX
               ========================================= */

            QSpinBox,
            QDoubleSpinBox {
                background: #101318;
                color: #e9edf2;
                border: 1px solid #2a3039;
                border-radius: 6px;
                padding: 0 9px;
                min-height: 32px;
                font-size: 11px;
            }

            QSpinBox:hover,
            QDoubleSpinBox:hover {
                border: 1px solid #3a424e;
            }

            QSpinBox:focus,
            QDoubleSpinBox:focus {
                border: 1px solid #1683ff;
            }

            QSpinBox::up-button,
            QSpinBox::down-button,
            QDoubleSpinBox::up-button,
            QDoubleSpinBox::down-button {
                background: transparent;
                border: none;
                width: 18px;
            }

            /* =========================================
               CHECKBOX
               ========================================= */

            QCheckBox {
                color: #c8ced8;
                font-size: 11px;
                spacing: 8px;
                padding: 4px 0;
            }

            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border-radius: 4px;
                border: 1px solid #3a414c;
                background: #101318;
            }

            QCheckBox::indicator:hover {
                border: 1px solid #1683ff;
            }

            QCheckBox::indicator:checked {
                background: #1683ff;
                border: 1px solid #1683ff;
            }
        """)

    # =====================================================
    # LOAD
    # =====================================================

    def load_values(self):

        settings = self.settings

        self.set_combo(
            self.start_page,
            settings["start_page"]
        )

        self.auto_refresh.setValue(
            settings["auto_refresh"]
        )

        self.dark_interface.setChecked(
            settings["dark_interface"]
        )

        self.set_combo(
            self.default_index,
            settings["default_index"]
        )

        self.set_combo(
            self.option_expiry,
            settings["option_expiry"]
        )

        self.minimum_confidence.setValue(
            settings["minimum_confidence"]
        )

        self.minimum_probability.setValue(
            settings["minimum_probability"]
        )

        self.enable_ai_recommendations.setChecked(
            settings["enable_ai_recommendations"]
        )

        self.trading_capital.setValue(
            settings["trading_capital"]
        )

        self.risk_per_trade.setValue(
            settings["risk_per_trade"]
        )

        self.daily_loss_limit.setValue(
            settings["daily_loss_limit"]
        )

        self.daily_profit_target.setValue(
            settings["daily_profit_target"]
        )

    # =====================================================
    # SAVE
    # =====================================================

    def save(self):

        settings = {

            "start_page":
                self.start_page.currentText(),

            "auto_refresh":
                self.auto_refresh.value(),

            "dark_interface":
                self.dark_interface.isChecked(),

            "default_index":
                self.default_index.currentText(),

            "option_expiry":
                self.option_expiry.currentText(),

            "minimum_confidence":
                self.minimum_confidence.value(),

            "minimum_probability":
                self.minimum_probability.value(),

            "enable_ai_recommendations":
                self.enable_ai_recommendations.isChecked(),

            "trading_capital":
                self.trading_capital.value(),

            "risk_per_trade":
                self.risk_per_trade.value(),

            "daily_loss_limit":
                self.daily_loss_limit.value(),

            "daily_profit_target":
                self.daily_profit_target.value(),
        }

        if save_settings(settings):

            self.settings = settings

            self.save_button.setText(
                "Saved ✓"
            )

            self.settings_saved.emit()

        else:

            self.save_button.setText(
                "Save Failed"
            )

    # =====================================================
    # COMBO HELPER
    # =====================================================

    @staticmethod
    def set_combo(
        combo,
        value
    ):

        index = combo.findText(
            str(value)
        )

        if index >= 0:
            combo.setCurrentIndex(
                index
            )