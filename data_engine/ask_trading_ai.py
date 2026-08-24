# ============================================================
# TradingAI - ASK TRADINGAI
# ============================================================

import os
import json
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from data_engine.combined_ai_score import CombinedAIScore
from data_engine.ai_option_chain_analyst import AIOptionChainAnalyst


load_dotenv()


class AskTradingAI:

    def __init__(
        self,
        model="gemini-3.5-flash-lite",
    ):

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.model = model

        self.client = genai.Client(
            api_key=api_key
        )

        self.combined_ai = CombinedAIScore()
        self.combined_ai.load()

        self.option_analyst = (
            AIOptionChainAnalyst(
                model=model
            )
        )

    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    def build_context(
        self,
        market_features,
        option_history,
    ):

        # ----------------------------------------------------
        # Combined AI
        # ----------------------------------------------------

        combined = self.combined_ai.predict(
            market_features.tail(1)
        )

        combined_row = (
            combined.iloc[0].to_dict()
        )

        # ----------------------------------------------------
        # Option chain
        # ----------------------------------------------------

        option_summary = (
            self.option_analyst.build_summary(
                option_history
            )
        )

        return {
            "quant": combined_row,
            "option_chain": option_summary,
        }

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        question: str,
        context: dict[str, Any],
    ):

        context_json = json.dumps(
            context,
            indent=2,
            default=str,
        )

        return f"""
You are Ask TradingAI.

You answer questions using ONLY the supplied TradingAI data.

RULES:
- Do not invent market data.
- Do not invent news.
- Do not claim certainty.
- Do not guarantee profits.
- Do not provide personalized financial advice.
- Clearly distinguish model output from interpretation.
- If the supplied data cannot answer the question, say so.
- Be concise but useful.

USER QUESTION:

{question}

TRADINGAI DATA:

{context_json}

Answer the user's question directly.

When useful, mention the relevant:
- Direction model
- Market regime
- Volatility
- Combined AI score
- Option-chain positioning
- Support/resistance
- PCR
- IV / IV skew

Do not expose internal implementation details unless asked.
"""

    # ========================================================
    # ASK
    # ========================================================

    def ask(
        self,
        question: str,
        context: dict[str, Any],
    ):

        if not isinstance(
            question,
            str
        ) or not question.strip():

            raise ValueError(
                "Question cannot be empty."
            )

        prompt = self._build_prompt(
            question.strip(),
            context,
        )

        response = (
            self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1000,
                ),
            )
        )

        if response is None:

            raise RuntimeError(
                "Gemini returned no response."
            )

        text = getattr(
            response,
            "text",
            None
        )

        if not text:

            raise RuntimeError(
                "Gemini returned an empty answer."
            )

        return text.strip()