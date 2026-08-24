from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui import theme
from data_engine.gemini_trade_analyst import GeminiTradeAnalyst


def _number(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _money(value):
    try:
        return f"₹{float(value):,.2f}"
    except Exception:
        return "₹--"


def _card(title, body="", accent=None):
    card = QFrame()
    card.setObjectName("analysisCard")

    color = accent or "#2A3342"

    card.setStyleSheet(
        f"""
        QFrame#analysisCard {{
            background: #151A22;
            border: 1px solid #252E3C;
            border-left: 3px solid {color};
            border-radius: 12px;
        }}
        QLabel {{
            background: transparent;
            border: none;
        }}
        """
    )

    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)

    title_label = QLabel(title)
    title_label.setStyleSheet(
        """
        QLabel {
            color: #8F9AAF;
            font-size: 10px;
            font-weight: 700;
        }
        """
    )

    body_label = QLabel(body)
    body_label.setWordWrap(True)
    body_label.setStyleSheet(
        """
        QLabel {
            color: #EAF0F7;
            font-size: 12px;
            line-height: 1.4;
        }
        """
    )

    layout.addWidget(title_label)
    layout.addWidget(body_label)

    return card, body_label


class GeminiAnalysisWorker(QObject):
    finished = Signal(dict)

    def __init__(self, result):
        super().__init__()
        self.result = result

    def run(self):
        try:
            response = GeminiTradeAnalyst().explain_trade_result(
                self.result
            )
        except Exception as exc:
            response = {
                "available": False,
                "error": str(exc),
                "text": "",
            }

        self.finished.emit(response)



class TradeSelectionCard(QFrame):
    clicked = Signal(dict)

    def __init__(
        self,
        trade,
        rank,
    ):
        super().__init__()

        self.trade = (
            trade
            if isinstance(
                trade,
                dict,
            )
            else {}
        )

        self.rank = rank

        self.setObjectName(
            "tradeSelectionCard"
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setStyleSheet(
            """
            QFrame#tradeSelectionCard {
                background: #151A22;
                border: 1px solid #293342;
                border-radius: 13px;
            }

            QFrame#tradeSelectionCard:hover {
                background: #192231;
                border: 1px solid #2A8BFF;
            }

            QLabel {
                background: transparent;
                border: none;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )
        layout.setSpacing(9)

        # ------------------------------------------------------
        # Header
        # ------------------------------------------------------

        header = QHBoxLayout()
        header.setSpacing(8)

        rank_label = QLabel(
            f"#{rank}"
        )
        rank_label.setStyleSheet(
            """
            QLabel {
                color: #718099;
                font-size: 10px;
                font-weight: 800;
            }
            """
        )

        strike = self.trade.get(
            "strike",
            "—",
        )

        option_type = str(
            self.trade.get(
                "type",
                "",
            )
        ).upper()

        title = QLabel(
            f"{strike} {option_type}"
        )
        title.setStyleSheet(
            """
            QLabel {
                color: #F7FAFF;
                font-size: 19px;
                font-weight: 800;
            }
            """
        )

        recommendation = QLabel(
            str(
                self.trade.get(
                    "recommendation",
                    "WATCH",
                )
            )
        )
        recommendation.setStyleSheet(
            """
            QLabel {
                color: #39E6A2;
                font-size: 10px;
                font-weight: 800;
            }
            """
        )

        header.addWidget(
            rank_label
        )
        header.addWidget(
            title
        )
        header.addStretch()
        header.addWidget(
            recommendation
        )

        layout.addLayout(
            header
        )

        # ------------------------------------------------------
        # Metrics
        # ------------------------------------------------------

        metrics = QHBoxLayout()
        metrics.setSpacing(16)

        score = QLabel(
            f"AI SCORE\n"
            f"{self.trade.get('ai_score', '—')}/100"
        )

        probability = QLabel(
            f"PROBABILITY\n"
            f"{self.trade.get('probability', '—')}%"
        )

        risk = (
            self.trade.get("risk")
            or {}
        )

        rr = QLabel(
            f"R:R\n"
            f"{risk.get('rr', '—')}"
        )

        premium = QLabel(
            f"PREMIUM\n"
            f"{_money(self.trade.get('premium'))}"
        )

        for label in (
            score,
            probability,
            rr,
            premium,
        ):
            label.setStyleSheet(
                """
                QLabel {
                    color: #C9D3E2;
                    font-size: 12px;
                    font-weight: 700;
                }
                """
            )
            metrics.addWidget(
                label
            )

        metrics.addStretch()

        layout.addLayout(
            metrics
        )

        hint = QLabel(
            "Click to view complete analysis →"
        )
        hint.setStyleSheet(
            """
            QLabel {
                color: #657186;
                font-size: 11px;
            }
            """
        )

        layout.addWidget(
            hint
        )

    def mousePressEvent(
        self,
        event,
    ):
        if (
            event.button()
            == Qt.LeftButton
        ):
            self.clicked.emit(
                dict(self.trade)
            )

        super().mousePressEvent(
            event
        )


class AITradeAnalysisPage(QWidget):
    """
    Step 7 AI Trade Analysis page.

    Default state:
      - shows the five generated trade candidates as selectable cards.

    Selected state:
      - shows detailed deterministic analysis and Gemini analysis
        for the selected candidate only.

    This page never regenerates trades and never changes trade values.
    """

    def __init__(self):
        super().__init__()

        self.current_result = {}
        self.current_trades = []
        self.selected_trade = None

        self.gemini_thread = None
        self.gemini_worker = None

        self.setObjectName(
            "AITradeAnalysisPage"
        )

        self.setStyleSheet(
            """
            QWidget#AITradeAnalysisPage,
            QScrollArea,
            QScrollArea > QWidget,
            QScrollArea > QWidget > QWidget {
                background: #0D1015;
                color: #F5F7FA;
            }

            QLabel {
                background: transparent;
                border: none;
            }

            QPushButton {
                background: #151A22;
                color: #DDE7F5;
                border: 1px solid #293342;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 12px;
                font-weight: 700;
            }

            QPushButton:hover {
                background: #1B2533;
                border: 1px solid #2A8BFF;
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
        root.setSpacing(12)

        # ------------------------------------------------------
        # Header
        # ------------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            "AI Trade Analysis"
        )
        title.setStyleSheet(
            """
            QLabel {
                color: #F7FAFF;
                font-size: 22px;
                font-weight: 800;
            }
            """
        )

        self.subtitle = QLabel(
            "Select one of the generated trades."
        )
        self.subtitle.setStyleSheet(
            """
            QLabel {
                color: #7F899A;
                font-size: 11px;
            }
            """
        )

        header.addWidget(
            title
        )
        header.addStretch()
        header.addWidget(
            self.subtitle
        )

        root.addLayout(
            header
        )

        # ------------------------------------------------------
        # Scroll
        # ------------------------------------------------------

        scroll = QScrollArea()
        scroll.setWidgetResizable(
            True
        )
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: #0D1015;
                border: none;
            }

            QScrollArea > QWidget {
                background: #0D1015;
            }

            QScrollBar:vertical {
                background: #0D1015;
                width: 10px;
            }

            QScrollBar::handle:vertical {
                background: #293342;
                border-radius: 5px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )
        scroll.setFrameShape(
            QFrame.NoFrame
        )
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        content = QWidget()
        content.setAutoFillBackground(True)
        content.setStyleSheet(
            """
            QWidget {
                background: #0D1015;
                color: #F5F7FA;
            }
            """
        )

        self.content_layout = QVBoxLayout(
            content
        )
        self.content_layout.setContentsMargins(
            2,
            2,
            8,
            20,
        )
        self.content_layout.setSpacing(
            12
        )
        self.content_layout.setAlignment(
            Qt.AlignTop
        )

        # ------------------------------------------------------
        # Selector
        # ------------------------------------------------------

        selector = QFrame()
        selector.setStyleSheet(
            """
            QFrame {
                background: #121923;
                border: 1px solid #263242;
                border-radius: 14px;
            }

            QLabel {
                border: none;
                background: transparent;
            }
            """
        )

        selector_layout = QVBoxLayout(
            selector
        )
        selector_layout.setContentsMargins(
            16,
            14,
            16,
            16,
        )
        selector_layout.setSpacing(
            10
        )
        selector_layout.setAlignment(
            Qt.AlignTop
        )

        selector.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Maximum,
        )

        selector_header = QHBoxLayout()

        self.selector_title = QLabel(
            "SELECT A GENERATED TRADE"
        )
        self.selector_title.setStyleSheet(
            """
            QLabel {
                color: #F7FAFF;
                font-size: 17px;
                font-weight: 800;
            }
            """
        )

        self.selector_hint = QLabel(
            "Choose a trade to see its full reasoning."
        )
        self.selector_hint.setStyleSheet(
            """
            QLabel {
                color: #718099;
                font-size: 14px;
            }
            """
        )

        selector_header.addWidget(
            self.selector_title
        )
        selector_header.addStretch()
        selector_header.addWidget(
            self.selector_hint
        )

        selector_layout.addLayout(
            selector_header
        )

        self.trade_selector_grid = QGridLayout()
        self.trade_selector_grid.setHorizontalSpacing(
            12
        )
        self.trade_selector_grid.setVerticalSpacing(
            12
        )
        self.trade_selector_grid.setAlignment(
            Qt.AlignTop
        )

        selector_layout.addLayout(
            self.trade_selector_grid
        )

        self.content_layout.addWidget(
            selector
        )

        self.selector_panel = selector

        # ------------------------------------------------------
        # Details wrapper
        # ------------------------------------------------------

        self.detail_panel = QWidget()
        self.detail_panel.setStyleSheet(
            """
            QWidget {
                background: #0D1015;
                color: #F5F7FA;
            }
            """
        )

        detail_layout = QVBoxLayout(
            self.detail_panel
        )
        detail_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        detail_layout.setSpacing(
            12
        )

        # Back button
        back_row = QHBoxLayout()

        self.back_button = QPushButton(
            "← Back to 5 trades"
        )

        self.back_button.clicked.connect(
            self._return_to_selector
        )

        back_row.addWidget(
            self.back_button
        )
        back_row.addStretch()

        detail_layout.addLayout(
            back_row
        )

        # ------------------------------------------------------
        # Hero
        # ------------------------------------------------------

        hero = QFrame()
        hero.setObjectName(
            "heroCard"
        )
        hero.setStyleSheet(
            """
            QFrame#heroCard {
                background: #121923;
                border: 1px solid #263242;
                border-radius: 14px;
            }
            """
        )

        hero_layout = QVBoxLayout(
            hero
        )
        hero_layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )
        hero_layout.setSpacing(
            5
        )

        self.best_title = QLabel(
            "NO TRADE SELECTED"
        )
        self.best_title.setStyleSheet(
            """
            QLabel {
                background: transparent;
                border: none;
                color: #F7FAFF;
                font-size: 23px;
                font-weight: 800;
                padding: 0px;
                margin: 0px;
            }
            """
        )

        self.best_title.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.best_meta = QLabel(
            "Select one of the five trades."
        )
        self.best_meta.setStyleSheet(
            """
            QLabel {
                background: transparent;
                border: none;
                color: #8F9AAF;
                font-size: 12px;
                padding: 0px;
                margin: 0px;
            }
            """
        )

        self.best_meta.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        hero_layout.addWidget(
            self.best_title
        )
        hero_layout.addWidget(
            self.best_meta
        )

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(
            10
        )
        metrics.setVerticalSpacing(
            10
        )

        self.score_value = (
            self._metric(
                metrics,
                "AI SCORE",
                "—",
                0,
                0,
            )
        )
        self.prob_value = (
            self._metric(
                metrics,
                "PROBABILITY",
                "—",
                0,
                1,
            )
        )
        self.rr_value = (
            self._metric(
                metrics,
                "RISK / REWARD",
                "—",
                0,
                2,
            )
        )
        self.premium_value = (
            self._metric(
                metrics,
                "PREMIUM",
                "—",
                0,
                3,
            )
        )

        hero_layout.addLayout(
            metrics
        )
        detail_layout.addWidget(
            hero
        )

        # ------------------------------------------------------
        # Reasoning
        # ------------------------------------------------------

        reasoning_grid = QGridLayout()
        reasoning_grid.setHorizontalSpacing(
            12
        )
        reasoning_grid.setVerticalSpacing(
            12
        )
        reasoning_grid.setAlignment(
            Qt.AlignTop
        )

        self.why_body = (
            self._add_reason_card(
                reasoning_grid,
                "WHY THIS TRADE",
                0,
                0,
                "#0A84FF",
            )
        )

        self.better_body = (
            self._add_reason_card(
                reasoning_grid,
                "WHY IT IS BETTER",
                0,
                1,
                "#F5C84B",
            )
        )

        self.support_body = (
            self._add_reason_card(
                reasoning_grid,
                "SUPPORTING EVIDENCE",
                0,
                2,
                "#34D399",
            )
        )

        self.conflict_body = (
            self._add_reason_card(
                reasoning_grid,
                "CONFLICTS / WARNINGS",
                1,
                0,
                "#FF5F57",
            )
        )

        # Keep the remaining two cards on row 2 so the detail page
        # uses the same compact 3-column layout.
        self.risk_body = (
            self._add_reason_card(
                reasoning_grid,
                "RISK & TRADE PLAN",
                1,
                1,
                "#34D399",
            )
        )

        self.context_body = (
            self._add_reason_card(
                reasoning_grid,
                "UNIFIED ENGINE CONTEXT",
                1,
                2,
                "#A78BFA",
            )
        )

        detail_layout.addLayout(
            reasoning_grid
        )

        # ------------------------------------------------------
        # Candidates
        # ------------------------------------------------------

        self.candidates_body = (
            self._add_reason_card(
                detail_layout,
                "GENERATED CANDIDATES",
                accent="#6B7280",
            )
        )

        # ------------------------------------------------------
        # Gemini
        # ------------------------------------------------------

        self.analyst_body = (
            self._add_reason_card(
                detail_layout,
                "AI ANALYST / GEMINI",
                accent="#8B5CF6",
            )
        )

        self.gemini_status = QLabel(
            "Gemini will run after a trade is selected."
        )
        self.gemini_status.setWordWrap(
            True
        )
        self.gemini_status.setStyleSheet(
            """
            QLabel {
                color: #8F9AAF;
                font-size: 12px;
                background: transparent;
                border: none;
                padding-top: 4px;
            }
            """
        )

        analyst_parent = (
            self.analyst_body.parentWidget()
        )

        if analyst_parent is not None:
            analyst_layout = (
                analyst_parent.layout()
            )
            if analyst_layout is not None:
                analyst_layout.addWidget(
                    self.gemini_status
                )

        self.content_layout.addWidget(
            self.detail_panel
        )

        scroll.setWidget(
            content
        )

        root.addWidget(
            scroll,
            1
        )

        # Default: selector only.
        self._set_detail_visible(
            False
        )

        self._show_trade_selector()

    # ==========================================================
    # UI HELPERS
    # ==========================================================

    def _metric(
        self,
        grid,
        title,
        value,
        row,
        column,
    ):
        card = QFrame()
        card.setStyleSheet(
            """
            QFrame {
                background: #181F2A;
                border: 1px solid #293342;
                border-radius: 10px;
            }

            QLabel {
                border: none;
                background: transparent;
            }
            """
        )

        layout = QVBoxLayout(
            card
        )
        layout.setContentsMargins(
            11,
            9,
            11,
            9,
        )
        layout.setSpacing(
            3
        )

        title_label = QLabel(
            title
        )
        title_label.setStyleSheet(
            "color:#7F899A; font-size:8px; font-weight:700;"
        )

        value_label = QLabel(
            value
        )
        value_label.setStyleSheet(
            "color:#F5F7FA; font-size:16px; font-weight:800;"
        )

        layout.addWidget(
            title_label
        )
        layout.addWidget(
            value_label
        )

        grid.addWidget(
            card,
            row,
            column,
        )

        return value_label

    def _add_reason_card(
        self,
        target,
        title,
        row=None,
        column=None,
        accent=None,
    ):
        body_text = "--"

        card, body = _card(
            title,
            body_text,
            accent,
        )

        if isinstance(
            target,
            QGridLayout,
        ):
            target.addWidget(
                card,
                row,
                column,
            )
        else:
            target.addWidget(
                card
            )

        return body

    def _set_detail_visible(
        self,
        visible,
    ):
        self.detail_panel.setVisible(
            bool(visible)
        )

        self.selector_panel.setVisible(
            not bool(visible)
        )

    # ==========================================================
    # TRADE SELECTOR
    # ==========================================================

    def _clear_trade_selector(
        self,
    ):
        while (
            self.trade_selector_grid.count()
            > 0
        ):
            item = (
                self.trade_selector_grid.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _show_trade_selector(
        self,
    ):
        self._set_detail_visible(
            False
        )

        self._clear_trade_selector()

        trades = (
            self.current_trades
            if isinstance(
                self.current_trades,
                list,
            )
            else []
        )

        trades = trades[:5]

        if not trades:
            self.selector_title.setText(
                "NO GENERATED TRADES"
            )
            self.selector_hint.setText(
                "Generate AI Trade on the Dashboard first."
            )
            self.subtitle.setText(
                "No generated opportunities"
            )
            return

        self.selector_title.setText(
            "SELECT A GENERATED TRADE"
        )

        self.selector_hint.setText(
            "Click a trade to open its detailed analysis."
        )

        self.subtitle.setText(
            f"{len(trades)} generated opportunities"
        )

        for index, trade in enumerate(
            trades,
            start=1,
        ):
            card = TradeSelectionCard(
                trade,
                index,
            )

            card.clicked.connect(
                self._trade_selected
            )

            row = (
                (index - 1)
                // 3
            )

            column = (
                (index - 1)
                % 3
            )

            self.trade_selector_grid.addWidget(
                card,
                row,
                column,
            )


    def _trade_selected(
        self,
        trade,
    ):
        self.selected_trade = dict(
            trade
        )

        self._render_trade(
            self.selected_trade
        )

        self._set_detail_visible(
            True
        )

        self._start_gemini_analysis()

    def _return_to_selector(
        self,
    ):
        self.selected_trade = None

        if (
            self.gemini_thread is not None
            and self.gemini_thread.isRunning()
        ):
            self.gemini_thread.quit()

        self.gemini_status.setText(
            "Gemini will run after a trade is selected."
        )

        self._show_trade_selector()

    # ==========================================================
    # DATA
    # ==========================================================

    def set_result(
        self,
        result,
    ):
        self.current_result = (
            result
            if isinstance(
                result,
                dict,
            )
            else {}
        )

        self.current_trades = (
            self.current_result.get(
                "trades"
            )
            or []
        )

        # IMPORTANT:
        # Generating a trade only populates the 5-card selector.
        # No detailed analysis or Gemini call happens here.
        self.selected_trade = None

        self._show_trade_selector()

    # ==========================================================
    # RENDER SELECTED TRADE
    # ==========================================================

    def _render_trade(
        self,
        selected_trade,
    ):
        result = self.current_result
        trades = self.current_trades
        best = (
            selected_trade
            if isinstance(
                selected_trade,
                dict,
            )
            else {}
        )

        if not best:
            return

        trade_type = str(
            best.get(
                "type",
                "",
            )
        ).upper()

        strike = best.get(
            "strike",
            "—",
        )

        recommendation = best.get(
            "recommendation",
            "WATCH",
        )

        self.best_title.setText(
            f"{strike} {trade_type}  •  "
            f"{recommendation}"
        )

        self.best_meta.setText(
            f"{result.get('selected_index', 'NIFTY 50')}  •  "
            f"Expiry: {result.get('expiry', '—')}"
        )

        self.score_value.setText(
            f"{best.get('ai_score', '—')}/100"
        )

        self.prob_value.setText(
            f"{best.get('probability', '—')}%"
        )

        risk = (
            best.get("risk")
            or {}
        )

        self.rr_value.setText(
            str(
                risk.get(
                    "rr",
                    "—",
                )
            )
        )

        self.premium_value.setText(
            _money(
                best.get(
                    "premium"
                )
            )
        )

        # ------------------------------------------------------
        # Why this trade
        # ------------------------------------------------------

        reasons = (
            best.get(
                "reasons"
            )
            or []
        )

        self.why_body.setText(
            self._bullets(
                reasons
                if reasons
                else [
                    "No explicit ranker reasons were returned."
                ]
            )
        )

        # ------------------------------------------------------
        # Why it is better
        # ------------------------------------------------------

        comparisons = []

        selected_score = _number(
            best.get(
                "ai_score"
            ),
            0,
        )

        for candidate in trades:
            if candidate is best:
                continue

            candidate_score = _number(
                candidate.get(
                    "ai_score"
                ),
                0,
            )

            difference = (
                selected_score
                - candidate_score
            )

            comparisons.append(
                f"{candidate.get('strike', '—')} "
                f"{str(candidate.get('type', '')).upper()}: "
                f"{candidate.get('ai_score', '—')}/100 "
                f"({difference:+.0f} vs selected)"
            )

        if comparisons:
            better_text = (
                "This selected trade is being compared "
                "against the other generated candidates.\n\n"
                + self._bullets(
                    comparisons
                )
            )
        else:
            better_text = (
                "No alternate candidates are available."
            )

        self.better_body.setText(
            better_text
        )

        # ------------------------------------------------------
        # Supporting evidence
        # ------------------------------------------------------

        unified = (
            best.get(
                "unified_components"
            )
            or {}
        )

        support = list(
            reasons
        )

        futures_score = unified.get(
            "futures_score"
        )

        ml_score = unified.get(
            "ml_score"
        )

        if futures_score is not None:
            support.append(
                f"Futures component: "
                f"{futures_score:+g}"
            )

        if ml_score is not None:
            ml_status = unified.get(
                "ml_signal",
                "UNAVAILABLE",
            )

            support.append(
                f"ML component: "
                f"{ml_score:+g} "
                f"({ml_status})"
            )

        self.support_body.setText(
            self._bullets(
                support
                if support
                else [
                    "No additional evidence."
                ]
            )
        )

        # ------------------------------------------------------
        # Warnings
        # ------------------------------------------------------

        warnings = (
            best.get(
                "warnings"
            )
            or []
        )

        if warnings:
            warning_lines = [
                "Explicit ranking warnings:"
            ]
            warning_lines.extend(
                warnings
            )
        else:
            warning_lines = [
                "No explicit ranking warnings.",
            ]

            recommendation_text = str(
                best.get(
                    "recommendation",
                    "WATCH",
                )
            )

            probability_value = _number(
                best.get(
                    "probability"
                ),
                0,
            )

            if recommendation_text:
                warning_lines.append(
                    f"Recommendation status: "
                    f"{recommendation_text}"
                )

            if probability_value < 70:
                warning_lines.append(
                    f"Probability is moderate at "
                    f"{probability_value:.1f}%."
                )

            if (
                unified.get(
                    "ml_signal"
                )
                in (
                    None,
                    "",
                    "UNAVAILABLE",
                )
            ):
                warning_lines.append(
                    "ML direction signal is currently unavailable."
                )

        self.conflict_body.setText(
            self._bullets(
                warning_lines
            )
        )

        # ------------------------------------------------------
        # Risk
        # ------------------------------------------------------

        risk_lines = [
            f"Entry: "
            f"{_money(risk.get('entry'))}",
            f"Stop Loss: "
            f"{_money(risk.get('sl'))}",
            f"Target 1: "
            f"{_money(risk.get('target1'))}",
            f"Target 2: "
            f"{_money(risk.get('target2'))}",
            f"Target 3: "
            f"{_money(risk.get('target3'))}",
            f"Position size: "
            f"{risk.get('position_size', '—')}",
            f"Maximum loss: "
            f"{_money(risk.get('max_loss'))}",
        ]

        self.risk_body.setText(
            self._bullets(
                risk_lines
            )
        )

        # ------------------------------------------------------
        # Unified context
        # ------------------------------------------------------

        context_lines = [
            f"ML score: "
            f"{unified.get('ml_score', '—')}",
            f"ML signal: "
            f"{unified.get('ml_signal', '—')}",
            f"ML regime: "
            f"{unified.get('ml_regime', '—')}",
            (
                "ML direction probability: "
                f"{unified.get('ml_direction_probability', '—')}"
            ),
            f"Futures score: "
            f"{unified.get('futures_score', '—')}",
        ]

        self.context_body.setText(
            self._bullets(
                context_lines
            )
        )

        # ------------------------------------------------------
        # Candidate list
        # ------------------------------------------------------

        candidate_lines = []

        for index, candidate in enumerate(
            trades[:5],
            start=1,
        ):
            candidate_lines.append(
                f"{index}. "
                f"{candidate.get('strike', '—')} "
                f"{str(candidate.get('type', '')).upper()} | "
                f"Score "
                f"{candidate.get('ai_score', '—')} | "
                f"Probability "
                f"{candidate.get('probability', '—')}% | "
                f"{candidate.get('recommendation', 'WATCH')}"
            )

        self.candidates_body.setText(
            self._bullets(
                candidate_lines
            )
        )

        # ------------------------------------------------------
        # Gemini placeholder
        # ------------------------------------------------------

        self.analyst_body.setText(
            "Deterministic TradingAI analysis is available above.\n\n"
            "Gemini / Agents will use this exact selected trade "
            "to explain why it was selected, what supports it, "
            "why it compares favorably to the other candidates, "
            "what conflicts with it, and what would invalidate it."
        )

        self.gemini_status.setText(
            "Starting Gemini analysis..."
        )

        self.subtitle.setText(
            f"Selected: {strike} {trade_type}"
        )

    # ==========================================================
    # GEMINI ANALYSIS
    # ==========================================================

    def _start_gemini_analysis(
        self,
    ):
        if not self.selected_trade:
            return

        if (
            self.gemini_thread is not None
            and self.gemini_thread.isRunning()
        ):
            self.gemini_thread.quit()

        gemini_result = dict(
            self.current_result
        )

        gemini_result["trades"] = [
            dict(
                self.selected_trade
            )
        ]

        gemini_result[
            "selected_trade"
        ] = dict(
            self.selected_trade
        )

        self.gemini_status.setText(
            "Gemini analysis: running..."
        )

        self.gemini_thread = QThread(
            self
        )

        self.gemini_worker = (
            GeminiAnalysisWorker(
                gemini_result
            )
        )

        self.gemini_worker.moveToThread(
            self.gemini_thread
        )

        self.gemini_thread.started.connect(
            self.gemini_worker.run
        )

        self.gemini_worker.finished.connect(
            self._gemini_finished
        )

        self.gemini_worker.finished.connect(
            self.gemini_thread.quit
        )

        self.gemini_worker.finished.connect(
            self.gemini_worker.deleteLater
        )

        self.gemini_thread.finished.connect(
            self.gemini_thread.deleteLater
        )

        self.gemini_thread.finished.connect(
            self._gemini_thread_finished
        )

        self.gemini_thread.start()

    def _gemini_finished(
        self,
        response,
    ):
        response = (
            response
            if isinstance(
                response,
                dict,
            )
            else {}
        )

        if response.get(
            "available"
        ):
            self.analyst_body.setText(
                response.get(
                    "text"
                )
                or ""
            )

            self.gemini_status.setText(
                "Gemini analysis complete"
            )

        else:
            error = (
                response.get(
                    "error"
                )
                or
                "Gemini unavailable."
            )

            self.analyst_body.setText(
                "Deterministic TradingAI analysis "
                "is available above.\n\n"
                "Gemini analysis is currently "
                "unavailable.\n\n"
                f"Reason: {error}"
            )

            self.gemini_status.setText(
                "Gemini analysis unavailable"
            )

    def _gemini_thread_finished(
        self,
    ):
        self.gemini_thread = None
        self.gemini_worker = None

    @staticmethod
    def _bullets(
        items,
    ):
        return "\n".join(
            f"• {item}"
            for item in items
        )