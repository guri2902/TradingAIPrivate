# ============================================================
# TradingAI - AI TRADE EXPLANATION
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

class TradeExplanation(BaseModel):

    trade_bias: str = Field(
        description="BULLISH, BEARISH, or NEUTRAL"
    )

    confidence: str = Field(
        description="Confidence percentage"
    )

    why: list[str] = Field(
        description="2 to 5 reasons supporting the current setup"
    )

    supporting_models: str = Field(
        description="How the Direction, Regime, and Volatility models contribute"
    )

    option_context: str = Field(
        description="How the option chain supports or conflicts with the setup"
    )

    weakness: str = Field(
        description="Main weakness or conflicting evidence"
    )

    invalidation: str = Field(
        description="What market condition would weaken or invalidate the setup"
    )

    suitability: str = Field(
        description="FAVORABLE, CAUTION, or AVOID"
    )


# ============================================================
# AI TRADE EXPLANATION
# ============================================================

class AITradeExplanation:

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
        trade_data: dict[str, Any],
    ):

        data = json.dumps(
            trade_data,
            indent=2,
            default=str,
        )

        return f"""
You are TradingAI's Trade Explanation Analyst.

Explain the supplied TradingAI setup using ONLY the supplied data.

RULES:
- Do not invent market data.
- Do not invent news.
- Do not guarantee profits.
- Do not provide personalized financial advice.
- Treat model outputs as probabilistic.
- Do not turn CAUTION into FAVORABLE.
- Do not invent entry, stop-loss, or target levels that are not supplied.
- Clearly identify supporting and conflicting evidence.
- Be concise and practical.

TRADE DATA:

{data}

Return:

trade_bias:
Exactly BULLISH, BEARISH, or NEUTRAL.

confidence:
Use the supplied confidence.

why:
Give 2 to 5 specific reasons supporting the setup.

supporting_models:
Explain the Direction, Regime, and Volatility model contribution.

option_context:
Explain whether the option-chain information supports,
conflicts with, or is neutral to the quantitative setup.

weakness:
State the main weakness or conflicting evidence.

invalidation:
State only conditions directly supported by the supplied
data that would weaken the setup.

suitability:
Use ONLY the supplied trade_suitability:
FAVORABLE, CAUTION, or AVOID.

Return every field.
"""

    # ========================================================
    # ANALYZE
    # ========================================================

    def explain(
        self,
        trade_data: dict[str, Any],
    ):

        if not isinstance(
            trade_data,
            dict,
        ):

            raise TypeError(
                "trade_data must be a dictionary."
            )

        prompt = self._build_prompt(
            trade_data
        )

        response = None
        last_error = None

        for attempt in range(3):

            try:

                print(
                    f"[AI-TRADE] Gemini request "
                    f"{attempt + 1}/3..."
                )

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            max_output_tokens=1200,
                            response_mime_type="application/json",
                            response_schema=TradeExplanation,
                        ),
                    )
                )

                break

            except Exception as exc:

                last_error = exc

                print(
                    f"[AI-TRADE] Attempt "
                    f"{attempt + 1}/3 failed: "
                    f"{exc}"
                )

                if attempt < 2:
                    time.sleep(3)

        if response is None:

            raise RuntimeError(
                "Gemini trade explanation failed: "
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

        explanation = None

        if isinstance(
            parsed,
            TradeExplanation,
        ):

            explanation = parsed

        elif isinstance(
            parsed,
            dict,
        ):

            explanation = TradeExplanation(
                **parsed
            )

        # ----------------------------------------------------
        # JSON FALLBACK
        # ----------------------------------------------------

        if explanation is None:

            text = getattr(
                response,
                "text",
                None,
            )

            if not text:

                raise RuntimeError(
                    "Gemini returned empty trade explanation."
                )

            try:

                payload = json.loads(
                    text
                )

                explanation = TradeExplanation(
                    **payload
                )

            except Exception as exc:

                raise RuntimeError(
                    f"Invalid trade explanation response: {exc}"
                ) from exc

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        explanation.trade_bias = (
            explanation.trade_bias
            .strip()
            .upper()
        )

        explanation.suitability = (
            explanation.suitability
            .strip()
            .upper()
        )

        if explanation.trade_bias not in (
            "BULLISH",
            "BEARISH",
            "NEUTRAL",
        ):

            raise RuntimeError(
                f"Invalid trade bias: "
                f"{explanation.trade_bias}"
            )

        if explanation.suitability not in (
            "FAVORABLE",
            "CAUTION",
            "AVOID",
        ):

            raise RuntimeError(
                f"Invalid suitability: "
                f"{explanation.suitability}"
            )

        return self._format(
            explanation
        )

    # ========================================================
    # FORMAT
    # ========================================================

    @staticmethod
    def _format(
        explanation: TradeExplanation,
    ):

        why = "\n".join(
            f"- {item}"
            for item in explanation.why[:5]
        )

        return (
            "TRADE BIAS:\n"
            f"{explanation.trade_bias}\n\n"

            "CONFIDENCE:\n"
            f"{explanation.confidence}\n\n"

            "WHY:\n"
            f"{why}\n\n"

            "SUPPORTING MODELS:\n"
            f"{explanation.supporting_models}\n\n"

            "OPTION CONTEXT:\n"
            f"{explanation.option_context}\n\n"

            "WEAKNESS:\n"
            f"{explanation.weakness}\n\n"

            "INVALIDATION:\n"
            f"{explanation.invalidation}\n\n"

            "SUITABILITY:\n"
            f"{explanation.suitability}"
        )

    # ========================================================
    # EXPLAIN FROM COMBINED SCORE
    # ========================================================

    def explain_result(
        self,
        result,
        option_data=None,
    ):

        if result is None:

            raise ValueError(
                "Trade result is empty."
            )

        if hasattr(
            result,
            "to_dict",
        ):

            trade_data = result.to_dict()

        else:

            trade_data = dict(result)

        if option_data is not None:

            if hasattr(
                option_data,
                "to_dict",
            ):

                option_data = (
                    option_data.to_dict()
                )

            trade_data[
                "option_chain"
            ] = option_data

        return self.explain(
            trade_data
        )