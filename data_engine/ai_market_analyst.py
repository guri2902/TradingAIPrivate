# ============================================================
# TradingAI - AI MARKET ANALYST
# ============================================================

import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


load_dotenv()


# ============================================================
# STRUCTURED RESPONSE
# ============================================================

class MarketAnalysis(BaseModel):

    market_bias: str = Field(
        description="BULLISH, BEARISH, or NEUTRAL"
    )

    confidence: str = Field(
        description="Confidence percentage, e.g. 58.59%"
    )

    quant_signals: str = Field(
        description="Summary of Direction, Regime, Volatility, and Combined Score"
    )

    market_interpretation: str = Field(
        description="Interpretation of the combined quantitative signals"
    )

    risk: str = Field(
        description="Main uncertainty, conflicting signals, or invalidation risk"
    )

    trade_context: str = Field(
        description="FAVORABLE, CAUTION, or AVOID"
    )

    watch: list[str] = Field(
        description="2 to 4 things to monitor next"
    )


# ============================================================
# AI MARKET ANALYST
# ============================================================

class AIMarketAnalyst:

    def __init__(
        self,
        model="gemini-3.5-flash-lite",
    ):

        self.model = model

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
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        quant_data: dict[str, Any],
    ):

        data = json.dumps(
            quant_data,
            indent=2,
            default=str,
        )

        return f"""
You are TradingAI's Market Analyst.

Analyze ONLY the quantitative information supplied below.

RULES:
- Do not invent market data.
- Do not invent news.
- Do not claim certainty.
- Do not guarantee profits.
- Treat model outputs as probabilistic.
- Do not provide personalized financial advice.
- Do not add unsupported facts.
- Keep the analysis concise and complete.

QUANTITATIVE DATA:

{data}

Return a structured market analysis containing:

market_bias:
Exactly one of BULLISH, BEARISH, NEUTRAL.

confidence:
Use the supplied confidence and express it as a percentage.

quant_signals:
Explain the Direction model, Market Regime model,
Volatility model, and Combined AI Score.

market_interpretation:
Explain what the combined signals indicate.

risk:
Explain uncertainty, conflicting signals, weak confidence,
or what could invalidate the setup.

trade_context:
Use ONLY the supplied trade_suitability:
FAVORABLE, CAUTION, or AVOID.

watch:
Give 2 to 4 concise items to monitor next.

Return every field.
"""

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(
        self,
        quant_data: dict[str, Any],
    ):

        if not isinstance(
            quant_data,
            dict
        ):
            raise TypeError(
                "quant_data must be a dictionary."
            )

        prompt = self._build_prompt(
            quant_data
        )

        response = None
        last_error = None

        # ----------------------------------------------------
        # RETRY TEMPORARY API FAILURES
        # ----------------------------------------------------

        for attempt in range(3):

            try:

                print(
                    f"[AI-MARKET] Gemini request "
                    f"{attempt + 1}/3..."
                )

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            max_output_tokens=1200,
                            response_mime_type="application/json",
                            response_schema=MarketAnalysis,
                        ),
                    )
                )

                break

            except Exception as exc:

                last_error = exc

                print(
                    f"[AI-MARKET] Gemini attempt "
                    f"{attempt + 1}/3 failed: {exc}"
                )

                if attempt < 2:
                    time.sleep(3)

        if response is None:

            raise RuntimeError(
                "Gemini request failed after 3 attempts: "
                f"{last_error}"
            )

        # ----------------------------------------------------
        # STRUCTURED RESPONSE
        # ----------------------------------------------------

        parsed = getattr(
            response,
            "parsed",
            None
        )

        analysis = None

        if isinstance(
            parsed,
            MarketAnalysis
        ):

            analysis = parsed

        elif isinstance(
            parsed,
            dict
        ):

            analysis = MarketAnalysis(
                **parsed
            )

        # ----------------------------------------------------
        # TEXT JSON FALLBACK
        # ----------------------------------------------------

        if analysis is None:

            text = getattr(
                response,
                "text",
                None
            )

            if not text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            try:

                payload = json.loads(
                    text
                )

            except json.JSONDecodeError as exc:

                raise RuntimeError(
                    f"Gemini returned invalid JSON: {exc}"
                ) from exc

            analysis = MarketAnalysis(
                **payload
            )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        market_bias = (
            analysis.market_bias
            .strip()
            .upper()
        )

        if market_bias not in (
            "BULLISH",
            "BEARISH",
            "NEUTRAL",
        ):

            raise RuntimeError(
                f"Invalid market bias: {market_bias}"
            )

        trade_context = (
            analysis.trade_context
            .strip()
            .upper()
        )

        if trade_context not in (
            "FAVORABLE",
            "CAUTION",
            "AVOID",
        ):

            raise RuntimeError(
                f"Invalid trade context: {trade_context}"
            )

        analysis.market_bias = market_bias
        analysis.trade_context = trade_context

        # ----------------------------------------------------
        # FORMAT FOR CONSOLE / UI
        # ----------------------------------------------------

        return self._format_analysis(
            analysis
        )

    # ========================================================
    # FORMAT
    # ========================================================

    @staticmethod
    def _format_analysis(
        analysis: MarketAnalysis,
    ):

        watch_items = "\n".join(
            f"- {str(item).strip()}"
            for item in analysis.watch[:4]
        )

        return (
            "MARKET BIAS:\n"
            f"{analysis.market_bias}\n\n"

            "CONFIDENCE:\n"
            f"{analysis.confidence}\n\n"

            "QUANT SIGNALS:\n"
            f"{analysis.quant_signals}\n\n"

            "MARKET INTERPRETATION:\n"
            f"{analysis.market_interpretation}\n\n"

            "RISK:\n"
            f"{analysis.risk}\n\n"

            "TRADE CONTEXT:\n"
            f"{analysis.trade_context}\n\n"

            "WATCH:\n"
            f"{watch_items}"
        )

    # ========================================================
    # ANALYZE COMBINED SCORE
    # ========================================================

    def analyze_result(
        self,
        result,
    ):

        if result is None:

            raise ValueError(
                "Combined AI result is empty."
            )

        if hasattr(
            result,
            "to_dict"
        ):

            data = result.to_dict()

        else:

            data = dict(result)

        return self.analyze(
            data
        )