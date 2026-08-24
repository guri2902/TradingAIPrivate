# ============================================================
# TradingAI - PREMARKET AGENT
# ============================================================

import json
import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from data_engine.unified_data import UnifiedMarketData
from data_engine.feature_engineering import FeatureEngineering
from data_engine.combined_ai_score import CombinedAIScore
from data_engine.ai_option_chain_analyst import AIOptionChainAnalyst


load_dotenv()


# ============================================================
# STRUCTURED RESPONSE
# ============================================================

class PremarketBrief(BaseModel):

    market_bias: str

    confidence: str

    market_summary: str

    quant_view: str

    option_view: str

    key_support: str

    key_resistance: str

    volatility_view: str

    risks: list[str] = Field(
        description="2 to 4 premarket risks"
    )

    watchlist: list[str] = Field(
        description="3 to 5 things to monitor"
    )

    session_plan: str


# ============================================================
# PREMARKET AGENT
# ============================================================

class PremarketAgent:

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

        self.unified = UnifiedMarketData()
        self.features = FeatureEngineering()
        self.combined = CombinedAIScore()

        self.combined.load()

        self.option_analyst = (
            AIOptionChainAnalyst(
                model=model
            )
        )

    # ========================================================
    # LOAD MARKET CONTEXT
    # ========================================================

    def build_context(
        self,
        symbol="RELIANCE",
        option_path=(
            "market_data/processed/"
            "nifty_option_history.parquet"
        ),
    ):

        # ----------------------------------------------------
        # MARKET DATA
        # ----------------------------------------------------

        market_df = (
            self.unified.get_stock_history(
                symbol=symbol,
                source="eod2",
            )
        )

        if (
            market_df is None
            or market_df.empty
        ):

            raise RuntimeError(
                "Historical market data is empty."
            )

        feature_df = (
            self.features.build_features(
                market_df.copy()
            )
        )

        latest_market = (
            feature_df.tail(1)
        )

        # ----------------------------------------------------
        # QUANT SCORE
        # ----------------------------------------------------

        quant = self.combined.predict(
            latest_market
        )

        if quant is None or quant.empty:

            raise RuntimeError(
                "Combined AI score is empty."
            )

        quant_data = (
            quant.iloc[0].to_dict()
        )

        # ----------------------------------------------------
        # OPTION DATA
        # ----------------------------------------------------

        option_file = Path(
            option_path
        )

        option_data = {}

        if option_file.exists():

            option_df = pd.read_parquet(
                option_file
            )

            if not option_df.empty:

                option_data = (
                    self.option_analyst.build_summary(
                        option_df
                    )
                )

        # ----------------------------------------------------
        # RECENT MARKET DATA
        # ----------------------------------------------------

        recent_columns = [
            c
            for c in [
                "timestamp",
                "close",
                "open",
                "high",
                "low",
                "volume",
                "return",
                "momentum_5",
                "momentum_10",
                "momentum_20",
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

        return {
            "symbol": symbol,
            "latest_timestamp": str(
                latest_market[
                    "timestamp"
                ].iloc[0]
            )
            if "timestamp"
            in latest_market.columns
            else None,
            "quant": quant_data,
            "option_chain": option_data,
            "recent_market": recent,
        }

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        context,
    ):

        data = json.dumps(
            context,
            indent=2,
            default=str,
        )

        return f"""
You are TradingAI's Premarket Agent.

Generate a premarket briefing using ONLY the supplied data.

RULES:
- Do not invent news.
- Do not invent overnight events.
- Do not invent price levels.
- Do not guarantee profits.
- Do not provide personalized financial advice.
- Clearly separate model evidence from interpretation.
- Use only supplied support/resistance levels.
- Treat model outputs as probabilistic.

TRADINGAI PREMARKET DATA:

{data}

Return:

market_bias:
Exactly BULLISH, BEARISH, or NEUTRAL.

confidence:
Use the supplied confidence.

market_summary:
Give a concise overview.

quant_view:
Explain Direction, Regime, Volatility, and Combined Score.

option_view:
Explain the option-chain positioning.

key_support:
Use the supplied strongest support.

key_resistance:
Use the supplied strongest resistance.

volatility_view:
Explain the current volatility environment.

risks:
Give 2 to 4 evidence-based risks.

watchlist:
Give 3 to 5 specific things to monitor during the session.

session_plan:
Describe the objective market conditions to monitor.
Do not provide a personalized trade instruction.

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
                    f"[PREMARKET] Gemini request "
                    f"{attempt + 1}/3..."
                )

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            max_output_tokens=1600,
                            response_mime_type="application/json",
                            response_schema=PremarketBrief,
                        ),
                    )
                )

                break

            except Exception as exc:

                last_error = exc

                print(
                    f"[PREMARKET] Attempt "
                    f"{attempt + 1}/3 failed: "
                    f"{exc}"
                )

                if attempt < 2:
                    time.sleep(3)

        if response is None:

            raise RuntimeError(
                "Premarket Agent failed: "
                f"{last_error}"
            )

        parsed = getattr(
            response,
            "parsed",
            None
        )

        brief = None

        if isinstance(
            parsed,
            PremarketBrief
        ):

            brief = parsed

        elif isinstance(
            parsed,
            dict
        ):

            brief = PremarketBrief(
                **parsed
            )

        if brief is None:

            text = getattr(
                response,
                "text",
                None
            )

            if not text:

                raise RuntimeError(
                    "Premarket Agent returned empty response."
                )

            try:

                brief = PremarketBrief(
                    **json.loads(text)
                )

            except Exception as exc:

                raise RuntimeError(
                    f"Invalid premarket response: {exc}"
                ) from exc

        return self._format(
            brief
        )

    # ========================================================
    # FORMAT
    # ========================================================

    @staticmethod
    def _format(
        brief: PremarketBrief,
    ):

        risks = "\n".join(
            f"- {x}"
            for x in brief.risks[:4]
        )

        watchlist = "\n".join(
            f"- {x}"
            for x in brief.watchlist[:5]
        )

        return (
            "MARKET BIAS:\n"
            f"{brief.market_bias}\n\n"

            "CONFIDENCE:\n"
            f"{brief.confidence}\n\n"

            "MARKET SUMMARY:\n"
            f"{brief.market_summary}\n\n"

            "QUANT VIEW:\n"
            f"{brief.quant_view}\n\n"

            "OPTION VIEW:\n"
            f"{brief.option_view}\n\n"

            "KEY SUPPORT:\n"
            f"{brief.key_support}\n\n"

            "KEY RESISTANCE:\n"
            f"{brief.key_resistance}\n\n"

            "VOLATILITY VIEW:\n"
            f"{brief.volatility_view}\n\n"

            "RISKS:\n"
            f"{risks}\n\n"

            "WATCHLIST:\n"
            f"{watchlist}\n\n"

            "SESSION PLAN:\n"
            f"{brief.session_plan}"
        )