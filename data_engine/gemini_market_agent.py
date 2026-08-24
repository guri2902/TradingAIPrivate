# ============================================================
# TradingAI - GEMINI MARKET ANALYST AGENT
# ============================================================

from __future__ import annotations

import json
import os
from typing import Any

from google import genai
from google.genai import types


class GeminiMarketAgent:

    DEFAULT_MODEL = "gemini-3.7-flash"

    SYSTEM_INSTRUCTION = """
You are the explanation and market-analysis layer of TradingAI.

You receive structured market data produced by TradingAI's deterministic
market/data/risk engines.

Your responsibilities:
1. Explain the supplied market state.
2. Identify important technical, options and futures observations.
3. Explain conflicts between data sources.
4. Summarize bullish, bearish and neutral evidence.
5. Produce a cautious scenario assessment.
6. Never invent missing values.
7. Never claim that unavailable ML output exists.
8. Never override deterministic risk controls.
9. Never execute or place a trade.
10. Never fabricate probabilities.

Important:
- Data marked unavailable or stale must remain unavailable or stale.
- The existing Risk Engine is authoritative for risk decisions.
- You are an analyst/explainer, not the final execution authority.

Return only JSON matching the requested schema.
"""

    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string"
            },
            "market_bias": {
                "type": "string",
                "enum": [
                    "BULLISH",
                    "BEARISH",
                    "NEUTRAL",
                    "INSUFFICIENT_DATA",
                ],
            },
            "confidence": {
                "type": "number"
            },
            "technical_view": {
                "type": "string"
            },
            "options_view": {
                "type": "string"
            },
            "futures_view": {
                "type": "string"
            },
            "risk_view": {
                "type": "string"
            },
            "bullish_factors": {
                "type": "array",
                "items": {
                    "type": "string"
                },
            },
            "bearish_factors": {
                "type": "array",
                "items": {
                    "type": "string"
                },
            },
            "watch_levels": {
                "type": "array",
                "items": {
                    "type": "string"
                },
            },
            "warnings": {
                "type": "array",
                "items": {
                    "type": "string"
                },
            },
        },
        "required": [
            "summary",
            "market_bias",
            "confidence",
            "technical_view",
            "options_view",
            "futures_view",
            "risk_view",
            "bullish_factors",
            "bearish_factors",
            "watch_levels",
            "warnings",
        ],
    }

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ):

        self.api_key = (
            api_key
            or os.getenv(
                "GEMINI_API_KEY"
            )
        )

        if not self.api_key:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = (
            model
            or os.getenv(
                "TRADINGAI_GEMINI_MODEL",
                self.DEFAULT_MODEL,
            )
        )

        self.client = genai.Client(
            api_key=self.api_key
        )

    # ========================================================
    # SANITIZE
    # ========================================================

    @staticmethod
    def _json_safe(
        value: Any,
    ):

        if value is None:
            return None

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):

            return value

        if isinstance(
            value,
            dict,
        ):

            return {
                str(k):
                    GeminiMarketAgent._json_safe(v)
                for k, v in value.items()
            }

        if isinstance(
            value,
            (list, tuple),
        ):

            return [
                GeminiMarketAgent._json_safe(v)
                for v in value
            ]

        # pandas / numpy values
        if hasattr(
            value,
            "item",
        ):

            try:
                return value.item()
            except Exception:
                pass

        if hasattr(
            value,
            "isoformat",
        ):

            try:
                return value.isoformat()
            except Exception:
                pass

        return str(value)

    # ========================================================
    # BUILD PROMPT
    # ========================================================

    def _build_prompt(
        self,
        market_state: dict,
    ) -> str:

        safe_state = (
            self._json_safe(
                market_state
            )
        )

        return (
            "Analyze the following TradingAI "
            "market state.\n\n"
            "Do not add information that is not "
            "present in the state.\n\n"
            "TRADINGAI MARKET STATE:\n"
            f"{json.dumps(safe_state, indent=2)}"
        )

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(
        self,
        market_state: dict,
    ) -> dict:

        if not isinstance(
            market_state,
            dict,
        ):

            raise TypeError(
                "market_state must be a dictionary."
            )

        prompt = (
            self._build_prompt(
                market_state
            )
        )

        response = (
            self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        self.SYSTEM_INSTRUCTION
                    ),
                    temperature=0.2,
                    max_output_tokens=1500,
                    response_mime_type=(
                        "application/json"
                    ),
                    response_schema=(
                        self.RESPONSE_SCHEMA
                    ),
                ),
            )
        )

        text = (
            response.text
            if response is not None
            else None
        )

        if not text:

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        try:

            result = json.loads(
                text
            )

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        self._validate_result(
            result
        )

        return result

    # ========================================================
    # VALIDATE
    # ========================================================

    @staticmethod
    def _validate_result(
        result: dict,
    ):

        required = [
            "summary",
            "market_bias",
            "confidence",
            "technical_view",
            "options_view",
            "futures_view",
            "risk_view",
            "bullish_factors",
            "bearish_factors",
            "watch_levels",
            "warnings",
        ]

        missing = [
            key
            for key in required
            if key not in result
        ]

        if missing:

            raise RuntimeError(
                "Gemini response missing fields: "
                f"{missing}"
            )

        confidence = float(
            result["confidence"]
        )

        if not (
            0.0
            <= confidence
            <= 1.0
        ):

            raise RuntimeError(
                "Gemini confidence must be "
                "between 0 and 1."
            )


def create_gemini_market_agent():

    return GeminiMarketAgent()