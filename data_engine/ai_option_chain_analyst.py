# ============================================================
# TradingAI - AI OPTION CHAIN ANALYST
# ============================================================

import json
import os
import time
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


load_dotenv()


# ============================================================
# STRUCTURED RESPONSE
# ============================================================

class OptionChainAnalysis(BaseModel):

    option_bias: str = Field(
        description="BULLISH, BEARISH, or NEUTRAL"
    )

    confidence: str = Field(
        description="Confidence percentage"
    )

    positioning: str = Field(
        description="Summary of option positioning"
    )

    support: str = Field(
        description="Important put-side support"
    )

    resistance: str = Field(
        description="Important call-side resistance"
    )

    volatility: str = Field(
        description="IV and volatility interpretation"
    )

    interpretation: str = Field(
        description="Overall option-chain interpretation"
    )

    risk: str = Field(
        description="Main option-chain risks"
    )

    watch: list[str] = Field(
        description="2 to 4 things to monitor"
    )


# ============================================================
# AI OPTION CHAIN ANALYST
# ============================================================

class AIOptionChainAnalyst:

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
    # BUILD OPTION SUMMARY
    # ========================================================

    @staticmethod
    def build_summary(
        df,
    ):

        if df is None or df.empty:

            raise ValueError(
                "Option-chain dataframe is empty."
            )

        df = df.copy()

        # ----------------------------------------------------
        # NORMALIZE DATETIME
        # ----------------------------------------------------

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

        df["expiry"] = pd.to_datetime(
            df["expiry"],
            errors="coerce",
        )

        # ----------------------------------------------------
        # NORMALIZE NUMERIC FIELDS
        # ----------------------------------------------------

        numeric_columns = [
            "strike",
            "last_price",
            "volume",
            "oi",
            "oi_change",
            "iv",
            "bid_price",
            "ask_price",
            "bid_quantity",
            "ask_quantity",
            "total_buy_quantity",
            "total_sell_quantity",
            "underlying_value",
        ]

        for column in numeric_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

        # ----------------------------------------------------
        # VALID ROWS
        # ----------------------------------------------------

        df = df.dropna(
            subset=[
                "timestamp",
                "strike",
                "option_type",
            ]
        )

        if df.empty:

            raise ValueError(
                "No valid option-chain rows remain."
            )

        # ----------------------------------------------------
        # LATEST SNAPSHOT
        # ----------------------------------------------------

        latest_timestamp = (
            df["timestamp"].max()
        )

        latest = (
            df[
                df["timestamp"]
                == latest_timestamp
            ]
            .copy()
            .reset_index(drop=True)
        )

        if latest.empty:

            raise ValueError(
                "Latest option snapshot is empty."
            )

        # ----------------------------------------------------
        # UNDERLYING VALUE
        # ----------------------------------------------------

        underlying = None

        if "underlying_value" in latest.columns:

            values = (
                latest["underlying_value"]
                .dropna()
            )

            if not values.empty:

                underlying = float(
                    values.iloc[0]
                )

        # ----------------------------------------------------
        # EXPIRY
        # ----------------------------------------------------

        expiry = None

        if "expiry" in latest.columns:

            values = (
                latest["expiry"]
                .dropna()
            )

            if not values.empty:

                expiry = str(
                    values.iloc[0].date()
                )

        # ----------------------------------------------------
        # OPTION TYPES
        # ----------------------------------------------------

        latest["option_type"] = (
            latest["option_type"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        ce = latest[
            latest["option_type"] == "CE"
        ].copy()

        pe = latest[
            latest["option_type"] == "PE"
        ].copy()

        # ----------------------------------------------------
        # ATM STRIKE
        # ----------------------------------------------------

        atm_strike = None

        if (
            underlying is not None
            and not latest.empty
        ):

            distance = (
                latest["strike"]
                .sub(underlying)
                .abs()
            )

            nearest_index = (
                distance.idxmin()
            )

            atm_strike = float(
                latest.loc[
                    nearest_index,
                    "strike",
                ]
            )

        # ----------------------------------------------------
        # OI
        # ----------------------------------------------------

        ce_oi = (
            float(ce["oi"].sum())
            if "oi" in ce.columns
            else 0.0
        )

        pe_oi = (
            float(pe["oi"].sum())
            if "oi" in pe.columns
            else 0.0
        )

        put_call_oi_ratio = (
            pe_oi / ce_oi
            if ce_oi > 0
            else 0.0
        )

        # ----------------------------------------------------
        # VOLUME
        # ----------------------------------------------------

        ce_volume = (
            float(ce["volume"].sum())
            if "volume" in ce.columns
            else 0.0
        )

        pe_volume = (
            float(pe["volume"].sum())
            if "volume" in pe.columns
            else 0.0
        )

        put_call_volume_ratio = (
            pe_volume / ce_volume
            if ce_volume > 0
            else 0.0
        )

        # ----------------------------------------------------
        # ATM IV
        # ----------------------------------------------------

        atm_ce_iv = None
        atm_pe_iv = None

        if atm_strike is not None:

            atm_ce = ce[
                ce["strike"] == atm_strike
            ].copy()

            atm_pe = pe[
                pe["strike"] == atm_strike
            ].copy()

            if (
                not atm_ce.empty
                and "iv" in atm_ce.columns
            ):

                values = (
                    atm_ce["iv"]
                    .dropna()
                )

                if not values.empty:

                    atm_ce_iv = float(
                        values.iloc[0]
                    )

            if (
                not atm_pe.empty
                and "iv" in atm_pe.columns
            ):

                values = (
                    atm_pe["iv"]
                    .dropna()
                )

                if not values.empty:

                    atm_pe_iv = float(
                        values.iloc[0]
                    )

        # ----------------------------------------------------
        # IV SKEW
        # ----------------------------------------------------

        atm_iv_skew = None

        if (
            atm_ce_iv is not None
            and atm_pe_iv is not None
        ):

            atm_iv_skew = (
                atm_pe_iv
                - atm_ce_iv
            )

        # ----------------------------------------------------
        # MAX OI STRIKES
        # ----------------------------------------------------

        max_ce_oi_strike = None
        max_pe_oi_strike = None

        if (
            not ce.empty
            and "oi" in ce.columns
        ):

            valid = ce.dropna(
                subset=["oi", "strike"]
            )

            if not valid.empty:

                idx = valid["oi"].idxmax()

                max_ce_oi_strike = float(
                    valid.loc[
                        idx,
                        "strike",
                    ]
                )

        if (
            not pe.empty
            and "oi" in pe.columns
        ):

            valid = pe.dropna(
                subset=["oi", "strike"]
            )

            if not valid.empty:

                idx = valid["oi"].idxmax()

                max_pe_oi_strike = float(
                    valid.loc[
                        idx,
                        "strike",
                    ]
                )

        # ----------------------------------------------------
        # TOP CE OI
        # ----------------------------------------------------

        top_ce_oi = []

        if (
            not ce.empty
            and "oi" in ce.columns
        ):

            top = (
                ce.dropna(
                    subset=[
                        "strike",
                        "oi",
                    ]
                )
                .nlargest(
                    5,
                    "oi",
                )
            )

            top_ce_oi = [
                {
                    "strike": float(
                        row["strike"]
                    ),
                    "oi": float(
                        row["oi"]
                    ),
                }
                for _, row in top.iterrows()
            ]

        # ----------------------------------------------------
        # TOP PE OI
        # ----------------------------------------------------

        top_pe_oi = []

        if (
            not pe.empty
            and "oi" in pe.columns
        ):

            top = (
                pe.dropna(
                    subset=[
                        "strike",
                        "oi",
                    ]
                )
                .nlargest(
                    5,
                    "oi",
                )
            )

            top_pe_oi = [
                {
                    "strike": float(
                        row["strike"]
                    ),
                    "oi": float(
                        row["oi"]
                    ),
                }
                for _, row in top.iterrows()
            ]

        # ----------------------------------------------------
        # TOP CE VOLUME
        # ----------------------------------------------------

        top_ce_volume = []

        if (
            not ce.empty
            and "volume" in ce.columns
        ):

            top = (
                ce.dropna(
                    subset=[
                        "strike",
                        "volume",
                    ]
                )
                .nlargest(
                    5,
                    "volume",
                )
            )

            top_ce_volume = [
                {
                    "strike": float(
                        row["strike"]
                    ),
                    "volume": float(
                        row["volume"]
                    ),
                }
                for _, row in top.iterrows()
            ]

        # ----------------------------------------------------
        # TOP PE VOLUME
        # ----------------------------------------------------

        top_pe_volume = []

        if (
            not pe.empty
            and "volume" in pe.columns
        ):

            top = (
                pe.dropna(
                    subset=[
                        "strike",
                        "volume",
                    ]
                )
                .nlargest(
                    5,
                    "volume",
                )
            )

            top_pe_volume = [
                {
                    "strike": float(
                        row["strike"]
                    ),
                    "volume": float(
                        row["volume"]
                    ),
                }
                for _, row in top.iterrows()
            ]

        # ----------------------------------------------------
        # SUPPORT / RESISTANCE
        # ----------------------------------------------------

        support = (
            max_pe_oi_strike
        )

        resistance = (
            max_ce_oi_strike
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        symbol = "NIFTY"

        if "symbol" in latest.columns:

            values = (
                latest["symbol"]
                .dropna()
            )

            if not values.empty:

                symbol = str(
                    values.iloc[0]
                )

        return {

            "timestamp": str(
                latest_timestamp
            ),

            "symbol": symbol,

            "expiry": expiry,

            "underlying": underlying,

            "atm_strike": atm_strike,

            "ce_total_oi": ce_oi,

            "pe_total_oi": pe_oi,

            "put_call_oi_ratio":
                put_call_oi_ratio,

            "ce_total_volume":
                ce_volume,

            "pe_total_volume":
                pe_volume,

            "put_call_volume_ratio":
                put_call_volume_ratio,

            "atm_ce_iv": atm_ce_iv,

            "atm_pe_iv": atm_pe_iv,

            "atm_iv_skew":
                atm_iv_skew,

            "max_ce_oi_strike":
                max_ce_oi_strike,

            "max_pe_oi_strike":
                max_pe_oi_strike,

            "support": support,

            "resistance": resistance,

            "top_ce_oi": top_ce_oi,

            "top_pe_oi": top_pe_oi,

            "top_ce_volume":
                top_ce_volume,

            "top_pe_volume":
                top_pe_volume,
        }

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        chain_data: dict[str, Any],
    ):

        data = json.dumps(
            chain_data,
            indent=2,
            default=str,
        )

        return f"""
You are TradingAI's AI Option Chain Analyst.

Analyze ONLY the supplied option-chain data.

RULES:
- Do not invent data.
- Do not invent news.
- Do not guarantee profits.
- Do not provide personalized financial advice.
- Do not claim certainty.
- Use the actual strike, OI, volume, PCR and IV values supplied.
- Distinguish option positioning from directional certainty.
- Do not assume support/resistance is guaranteed.
- Keep the analysis concise and complete.

OPTION-CHAIN DATA:

{data}

Return:

option_bias:
Exactly one of BULLISH, BEARISH, NEUTRAL.

confidence:
A percentage based only on the strength and consistency
of the supplied option-chain evidence.

positioning:
Explain CE/PE OI, PCR and major positioning.

support:
Identify the strongest put-side support using the supplied data.

resistance:
Identify the strongest call-side resistance using the supplied data.

volatility:
Interpret ATM CE IV, ATM PE IV and IV skew.

interpretation:
Explain the overall option-chain structure.

risk:
Explain uncertainty or conflicting positioning.

watch:
Provide 2 to 4 things to monitor next.

Return every field.
Do not add unsupported information.
"""

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(
        self,
        chain_data: dict[str, Any],
    ):

        if not isinstance(
            chain_data,
            dict,
        ):

            raise TypeError(
                "chain_data must be a dictionary."
            )

        prompt = self._build_prompt(
            chain_data
        )

        response = None
        last_error = None

        for attempt in range(3):

            try:

                print(
                    f"[AI-OPTION] Gemini request "
                    f"{attempt + 1}/3..."
                )

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            max_output_tokens=1200,
                            response_mime_type="application/json",
                            response_schema=OptionChainAnalysis,
                        ),
                    )
                )

                break

            except Exception as exc:

                last_error = exc

                print(
                    f"[AI-OPTION] Attempt "
                    f"{attempt + 1}/3 failed: "
                    f"{exc}"
                )

                if attempt < 2:

                    time.sleep(3)

        if response is None:

            raise RuntimeError(
                "Gemini option-chain analysis failed: "
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

        analysis = None

        if isinstance(
            parsed,
            OptionChainAnalysis,
        ):

            analysis = parsed

        elif isinstance(
            parsed,
            dict,
        ):

            analysis = OptionChainAnalysis(
                **parsed
            )

        # ----------------------------------------------------
        # JSON TEXT FALLBACK
        # ----------------------------------------------------

        if analysis is None:

            text = getattr(
                response,
                "text",
                None,
            )

            if not text:

                raise RuntimeError(
                    "Gemini returned empty option-chain analysis."
                )

            try:

                payload = json.loads(
                    text
                )

                analysis = OptionChainAnalysis(
                    **payload
                )

            except Exception as exc:

                raise RuntimeError(
                    f"Invalid option-chain response: {exc}"
                ) from exc

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        analysis.option_bias = (
            analysis.option_bias
            .strip()
            .upper()
        )

        if analysis.option_bias not in (
            "BULLISH",
            "BEARISH",
            "NEUTRAL",
        ):

            raise RuntimeError(
                f"Invalid option bias: "
                f"{analysis.option_bias}"
            )

        if not analysis.watch:

            analysis.watch = [
                "PCR changes",
                "Major CE OI",
                "Major PE OI",
                "ATM IV changes",
            ]

        return self._format(
            analysis
        )

    # ========================================================
    # FORMAT
    # ========================================================

    @staticmethod
    def _format(
        analysis: OptionChainAnalysis,
    ):

        watch_items = "\n".join(
            f"- {str(item).strip()}"
            for item in analysis.watch[:4]
        )

        return (
            "OPTION BIAS:\n"
            f"{analysis.option_bias}\n\n"

            "CONFIDENCE:\n"
            f"{analysis.confidence}\n\n"

            "POSITIONING:\n"
            f"{analysis.positioning}\n\n"

            "SUPPORT:\n"
            f"{analysis.support}\n\n"

            "RESISTANCE:\n"
            f"{analysis.resistance}\n\n"

            "VOLATILITY:\n"
            f"{analysis.volatility}\n\n"

            "INTERPRETATION:\n"
            f"{analysis.interpretation}\n\n"

            "RISK:\n"
            f"{analysis.risk}\n\n"

            "WATCH:\n"
            f"{watch_items}"
        )

    # ========================================================
    # ANALYZE DATAFRAME
    # ========================================================

    def analyze_dataframe(
        self,
        df,
    ):

        summary = self.build_summary(
            df
        )

        return self.analyze(
            summary
        )