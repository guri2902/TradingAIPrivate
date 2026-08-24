# ============================================================
# TradingAI - POSTMARKET ANALYST
# ============================================================

import json
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from data_engine.unified_data import UnifiedMarketData
from data_engine.feature_engineering import FeatureEngineering
from data_engine.combined_ai_score import CombinedAIScore
from data_engine.ai_option_chain_analyst import AIOptionChainAnalyst
from data_engine.ai_journal_review import AIJournalReview


load_dotenv()


# ============================================================
# STRUCTURED RESPONSE
# ============================================================

class PostmarketReport(BaseModel):

    market_recap: str

    session_bias: str

    quant_performance: str

    option_chain_recap: str

    what_went_right: list[str] = Field(
        description="2 to 5 positive observations"
    )

    what_went_wrong: list[str] = Field(
        description="2 to 5 negative observations"
    )

    risk_review: str

    next_session_watch: list[str] = Field(
        description="3 to 5 things to monitor next session"
    )

    overall_assessment: str


# ============================================================
# POSTMARKET ANALYST
# ============================================================

class PostmarketAnalyst:

    def __init__(
        self,
        model="gemini-3.5-flash-lite",
        journal_path="trade_journal.json",
    ):

        self.model = model

        self.base_dir = (
            Path(__file__).resolve().parent.parent
        )

        self.journal_path = (
            self.base_dir / journal_path
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

        self.unified = UnifiedMarketData()
        self.features = FeatureEngineering()

        self.combined = CombinedAIScore()
        self.combined.load()

        self.option_analyst = AIOptionChainAnalyst(
            model=model
        )

    # ========================================================
    # LOAD JOURNAL
    # ========================================================

    def load_journal(self):

        if not self.journal_path.exists():
            return []

        try:

            with open(
                self.journal_path,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if isinstance(data, list):
                return [
                    x for x in data
                    if isinstance(x, dict)
                ]

        except Exception as exc:

            print(
                f"[POSTMARKET] Journal load error: {exc}"
            )

        return []

    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    def build_context(
        self,
        symbol="RELIANCE",
        option_path=(
            "market_data/processed/"
            "nifty_option_history.parquet"
        ),
    ):

        market_df = (
            self.unified.get_stock_history(
                symbol=symbol,
                source="eod2",
            )
        )

        if market_df is None or market_df.empty:
            raise RuntimeError(
                "Market data is empty."
            )

        feature_df = (
            self.features.build_features(
                market_df.copy()
            )
        )

        # ----------------------------------------------------
        # Latest session
        # ----------------------------------------------------

        latest = feature_df.tail(1)

        latest_row = (
            latest.iloc[0].to_dict()
        )

        # ----------------------------------------------------
        # Recent market
        # ----------------------------------------------------

        recent_columns = [
            c
            for c in [
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "return",
                "momentum_5",
                "momentum_10",
                "rsi_14",
                "macd",
                "macd_signal",
                "volatility_10",
                "volatility_20",
            ]
            if c in feature_df.columns
        ]

        recent = (
            feature_df[
                recent_columns
            ]
            .tail(20)
            .to_dict(
                orient="records"
            )
        )

        # ----------------------------------------------------
        # Quant
        # ----------------------------------------------------

        quant = self.combined.predict(
            latest
        )

        if quant is None or quant.empty:
            raise RuntimeError(
                "Combined AI score is empty."
            )

        quant_row = (
            quant.iloc[0].to_dict()
        )

        # ----------------------------------------------------
        # Option chain
        # ----------------------------------------------------

        option_summary = {}

        option_file = Path(
            option_path
        )

        if option_file.exists():

            option_df = pd.read_parquet(
                option_file
            )

            if not option_df.empty:

                option_summary = (
                    self.option_analyst.build_summary(
                        option_df
                    )
                )

        # ----------------------------------------------------
        # Journal
        # ----------------------------------------------------

        journal = self.load_journal()

        return {
            "symbol": symbol,
            "latest_market": latest_row,
            "recent_market": recent,
            "quant": quant_row,
            "option_chain": option_summary,
            "journal": journal,
        }

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        context: dict[str, Any],
    ):

        data = json.dumps(
            context,
            indent=2,
            default=str,
        )

        return f"""
You are TradingAI's Postmarket Analyst.

Review the completed trading session using ONLY the supplied data.

RULES:
- Do not invent news or market events.
- Do not invent missing trades.
- Do not guarantee performance.
- Do not provide personalized financial advice.
- Distinguish observed facts from interpretation.
- Do not claim a model was correct unless the supplied data supports it.
- Keep the report concise and evidence-based.

SESSION DATA:

{data}

Return:

market_recap:
Summarize what happened during the session based on available data.

session_bias:
State BULLISH, BEARISH, or NEUTRAL based on the supplied quantitative evidence.

quant_performance:
Discuss Direction, Regime, Volatility and Combined AI Score.
Only discuss outcome accuracy if it can actually be inferred.

option_chain_recap:
Summarize current option-chain positioning, support, resistance,
PCR and IV information.

what_went_right:
2 to 5 positive observations supported by the data.

what_went_wrong:
2 to 5 negative observations or weaknesses supported by the data.

risk_review:
Explain the main risks, uncertainty, weak signals, or data limitations.

next_session_watch:
3 to 5 specific things to monitor next session.

overall_assessment:
Give a concise overall conclusion.

Return every field.
"""

    # ========================================================
    # RUN
    # ========================================================

    def run(
        self,
        symbol="RELIANCE",
    ):

        context = self.build_context(
            symbol=symbol
        )

        prompt = self._build_prompt(
            context
        )

        response = None
        last_error = None

        for attempt in range(3):

            try:

                print(
                    f"[POSTMARKET] Gemini request "
                    f"{attempt + 1}/3..."
                )

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            max_output_tokens=1600,
                            response_mime_type="application/json",
                            response_schema=PostmarketReport,
                        ),
                    )
                )

                break

            except Exception as exc:

                last_error = exc

                print(
                    f"[POSTMARKET] Attempt "
                    f"{attempt + 1}/3 failed: {exc}"
                )

                if attempt < 2:
                    time.sleep(3)

        if response is None:

            raise RuntimeError(
                "Postmarket Analyst failed: "
                f"{last_error}"
            )

        parsed = getattr(
            response,
            "parsed",
            None
        )

        report = None

        if isinstance(
            parsed,
            PostmarketReport
        ):

            report = parsed

        elif isinstance(
            parsed,
            dict
        ):

            report = PostmarketReport(
                **parsed
            )

        if report is None:

            text = getattr(
                response,
                "text",
                None
            )

            if not text:
                raise RuntimeError(
                    "Gemini returned empty postmarket report."
                )

            try:

                report = PostmarketReport(
                    **json.loads(text)
                )

            except Exception as exc:

                raise RuntimeError(
                    f"Invalid postmarket response: {exc}"
                ) from exc

        report.session_bias = (
            report.session_bias
            .strip()
            .upper()
        )

        if report.session_bias not in (
            "BULLISH",
            "BEARISH",
            "NEUTRAL",
        ):

            raise RuntimeError(
                f"Invalid session bias: "
                f"{report.session_bias}"
            )

        return self._format(
            report
        )

    # ========================================================
    # FORMAT
    # ========================================================

    @staticmethod
    def _format(
        report: PostmarketReport,
    ):

        right = "\n".join(
            f"- {x}"
            for x in report.what_went_right[:5]
        )

        wrong = "\n".join(
            f"- {x}"
            for x in report.what_went_wrong[:5]
        )

        watch = "\n".join(
            f"- {x}"
            for x in report.next_session_watch[:5]
        )

        return (
            "MARKET RECAP:\n"
            f"{report.market_recap}\n\n"

            "SESSION BIAS:\n"
            f"{report.session_bias}\n\n"

            "QUANT PERFORMANCE:\n"
            f"{report.quant_performance}\n\n"

            "OPTION CHAIN RECAP:\n"
            f"{report.option_chain_recap}\n\n"

            "WHAT WENT RIGHT:\n"
            f"{right}\n\n"

            "WHAT WENT WRONG:\n"
            f"{wrong}\n\n"

            "RISK REVIEW:\n"
            f"{report.risk_review}\n\n"

            "NEXT SESSION WATCH:\n"
            f"{watch}\n\n"

            "OVERALL ASSESSMENT:\n"
            f"{report.overall_assessment}"
        )