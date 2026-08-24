# ============================================================
# TradingAI - AI JOURNAL REVIEW
# ============================================================

import json
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


load_dotenv()


# ============================================================
# STRUCTURED RESPONSE
# ============================================================

class JournalReview(BaseModel):

    overall_assessment: str

    performance_summary: str

    strengths: list[str] = Field(
        description="3 to 5 strengths"
    )

    weaknesses: list[str] = Field(
        description="3 to 5 weaknesses"
    )

    recurring_patterns: list[str] = Field(
        description="2 to 5 recurring patterns"
    )

    risk_management: str

    model_performance: str

    improvement_actions: list[str] = Field(
        description="3 to 5 concrete improvement actions"
    )

    priority_focus: str


# ============================================================
# AI JOURNAL REVIEW
# ============================================================

class AIJournalReview:

    def __init__(
        self,
        model="gemini-3.5-flash-lite",
        journal_path="trade_journal.json",
    ):

        self.model = model

        self.base_dir = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

        self.journal_path = (
            self.base_dir
            / journal_path
        )

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:

            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(
            api_key=api_key
        )

    # ========================================================
    # LOAD JOURNAL
    # ========================================================

    def load_trades(self):

        if not self.journal_path.exists():

            raise FileNotFoundError(
                f"Trade journal not found: "
                f"{self.journal_path}"
            )

        try:

            with open(
                self.journal_path,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                f"Invalid trade journal JSON: {exc}"
            ) from exc

        if not isinstance(
            data,
            list,
        ):

            raise RuntimeError(
                "Trade journal must contain a list of trades."
            )

        return [
            trade
            for trade in data
            if isinstance(
                trade,
                dict,
            )
        ]

    # ========================================================
    # SUMMARY
    # ========================================================

    @staticmethod
    def build_summary(
        trades,
    ):

        if not trades:

            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "breakevens": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "average_pnl": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "average_ai_score": 0.0,
                "average_confidence": 0.0,
            }

        normalized = []

        for trade in trades:

            pnl = float(
                trade.get(
                    "pnl",
                    0,
                )
                or 0
            )

            result = str(
                trade.get(
                    "result",
                    "",
                )
            ).upper()

            ai_score = float(
                trade.get(
                    "ai_score",
                    0,
                )
                or 0
            )

            confidence = float(
                trade.get(
                    "confidence",
                    0,
                )
                or 0
            )

            normalized.append(
                {
                    "date": trade.get(
                        "date"
                    ),
                    "instrument": trade.get(
                        "instrument"
                    ),
                    "type": trade.get(
                        "type"
                    ),
                    "entry": trade.get(
                        "entry"
                    ),
                    "exit": trade.get(
                        "exit"
                    ),
                    "quantity": trade.get(
                        "quantity"
                    ),
                    "pnl": pnl,
                    "result": result,
                    "ai_score": ai_score,
                    "confidence": confidence,
                }
            )

        total = len(
            normalized
        )

        wins = sum(
            1
            for trade in normalized
            if trade["result"] == "WIN"
        )

        losses = sum(
            1
            for trade in normalized
            if trade["result"] == "LOSS"
        )

        breakevens = sum(
            1
            for trade in normalized
            if trade["result"] == "BREAKEVEN"
        )

        pnls = [
            trade["pnl"]
            for trade in normalized
        ]

        scores = [
            trade["ai_score"]
            for trade in normalized
        ]

        confidences = [
            trade["confidence"]
            for trade in normalized
        ]

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "breakevens": breakevens,
            "win_rate": (
                wins / total * 100
                if total
                else 0.0
            ),
            "total_pnl": sum(
                pnls
            ),
            "average_pnl": (
                sum(pnls) / total
                if total
                else 0.0
            ),
            "best_trade": max(
                pnls
            ),
            "worst_trade": min(
                pnls
            ),
            "average_ai_score": (
                sum(scores) / len(scores)
                if scores
                else 0.0
            ),
            "average_confidence": (
                sum(confidences)
                / len(confidences)
                if confidences
                else 0.0
            ),
        }

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        trades,
        summary,
    ):

        journal_json = json.dumps(
            trades,
            indent=2,
            default=str,
        )

        summary_json = json.dumps(
            summary,
            indent=2,
        )

        return f"""
You are TradingAI's AI Journal Review Analyst.

Review the supplied historical trading journal.

IMPORTANT RULES:
- Use ONLY the supplied trade data.
- Do not invent missing information.
- Do not invent market conditions.
- Do not provide personalized financial advice.
- Do not guarantee future performance.
- Do not assume a losing trade was caused by one specific factor
  unless the journal data supports that conclusion.
- Distinguish observed patterns from interpretation.
- Focus on repeatable behavior and measurable performance.

JOURNAL SUMMARY:

{summary_json}

TRADE RECORDS:

{journal_json}

Return a structured review with:

overall_assessment:
A concise assessment of the journal's overall performance.

performance_summary:
Summarize trades, win rate, P&L, and average trade.

strengths:
3 to 5 strengths supported by the journal.

weaknesses:
3 to 5 weaknesses supported by the journal.

recurring_patterns:
2 to 5 patterns visible in the trades.
Examples include repeated losses in a trade type,
low-confidence trades, or poor results at certain AI scores.
Only mention patterns supported by the records.

risk_management:
Evaluate available evidence about entry, exit,
quantity, and losses. Do not invent stop-loss behavior
that is not recorded.

model_performance:
Compare AI score/confidence values with actual outcomes
where the journal data allows it.

improvement_actions:
3 to 5 concrete actions based on observed weaknesses.

priority_focus:
State the single most important area to improve next.

Keep the analysis concise and evidence-based.
Return every field.
"""

    # ========================================================
    # REVIEW
    # ========================================================

    def review(
        self,
        trades=None,
    ):

        if trades is None:

            trades = self.load_trades()

        if not trades:

            raise RuntimeError(
                "Trade journal contains no trades."
            )

        summary = self.build_summary(
            trades
        )

        prompt = self._build_prompt(
            trades,
            summary,
        )

        response = None
        last_error = None

        for attempt in range(3):

            try:

                print(
                    f"[AI-JOURNAL] Gemini request "
                    f"{attempt + 1}/3..."
                )

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            max_output_tokens=1600,
                            response_mime_type="application/json",
                            response_schema=JournalReview,
                        ),
                    )
                )

                break

            except Exception as exc:

                last_error = exc

                print(
                    f"[AI-JOURNAL] Attempt "
                    f"{attempt + 1}/3 failed: "
                    f"{exc}"
                )

                if attempt < 2:

                    time.sleep(3)

        if response is None:

            raise RuntimeError(
                "Gemini journal review failed: "
                f"{last_error}"
            )

        # ----------------------------------------------------
        # STRUCTURED RESPONSE
        # ----------------------------------------------------

        parsed = getattr(
            response,
            "parsed",
            None,
        )

        review = None

        if isinstance(
            parsed,
            JournalReview,
        ):

            review = parsed

        elif isinstance(
            parsed,
            dict,
        ):

            review = JournalReview(
                **parsed
            )

        # ----------------------------------------------------
        # JSON FALLBACK
        # ----------------------------------------------------

        if review is None:

            text = getattr(
                response,
                "text",
                None,
            )

            if not text:

                raise RuntimeError(
                    "Gemini returned empty journal review."
                )

            try:

                payload = json.loads(
                    text
                )

                review = JournalReview(
                    **payload
                )

            except Exception as exc:

                raise RuntimeError(
                    f"Invalid journal review response: "
                    f"{exc}"
                ) from exc

        return self._format(
            review,
            summary,
        )

    # ========================================================
    # FORMAT
    # ========================================================

    @staticmethod
    def _format(
        review,
        summary,
    ):

        strengths = "\n".join(
            f"- {item}"
            for item in review.strengths[:5]
        )

        weaknesses = "\n".join(
            f"- {item}"
            for item in review.weaknesses[:5]
        )

        patterns = "\n".join(
            f"- {item}"
            for item in review.recurring_patterns[:5]
        )

        actions = "\n".join(
            f"- {item}"
            for item in review.improvement_actions[:5]
        )

        return (
            "OVERALL ASSESSMENT:\n"
            f"{review.overall_assessment}\n\n"

            "PERFORMANCE SUMMARY:\n"
            f"{review.performance_summary}\n\n"

            "STRENGTHS:\n"
            f"{strengths}\n\n"

            "WEAKNESSES:\n"
            f"{weaknesses}\n\n"

            "RECURRING PATTERNS:\n"
            f"{patterns}\n\n"

            "RISK MANAGEMENT:\n"
            f"{review.risk_management}\n\n"

            "MODEL PERFORMANCE:\n"
            f"{review.model_performance}\n\n"

            "IMPROVEMENT ACTIONS:\n"
            f"{actions}\n\n"

            "PRIORITY FOCUS:\n"
            f"{review.priority_focus}"
        )