# ============================================================
# TradingAI - INTRADAY MONITOR
# ============================================================

import json
import os
import time
from datetime import datetime
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


load_dotenv()


# ============================================================
# STRUCTURED ALERT
# ============================================================

class IntradayAlert(BaseModel):

    status: str = Field(
        description="UNCHANGED, CHANGED, or IMPORTANT"
    )

    market_bias: str = Field(
        description="BULLISH, BEARISH, or NEUTRAL"
    )

    change_summary: str

    direction_change: str

    regime_change: str

    volatility_change: str

    option_change: str

    risk: str

    action: str


# ============================================================
# INTRADAY MONITOR
# ============================================================

class IntradayMonitor:

    def __init__(
        self,
        symbol="RELIANCE",
        model="gemini-3.5-flash-lite",
    ):

        self.symbol = symbol
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

        self.previous_state = None

    # ========================================================
    # GET CURRENT STATE
    # ========================================================

    def get_current_state(
        self,
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
                symbol=self.symbol,
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

        latest = feature_df.tail(1)

        # ----------------------------------------------------
        # COMBINED AI
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
        # OPTION DATA
        # ----------------------------------------------------

        option_data = {}

        if os.path.exists(option_path):

            option_df = pd.read_parquet(
                option_path
            )

            if not option_df.empty:

                option_data = (
                    self.option_analyst.build_summary(
                        option_df
                    )
                )

        # ----------------------------------------------------
        # CURRENT STATE
        # ----------------------------------------------------

        state = {
            "timestamp": datetime.now().isoformat(),
            "symbol": self.symbol,
            "price": float(
                latest["close"].iloc[0]
            ),
            "direction_prediction":
                quant_row[
                    "direction_prediction"
                ],
            "up_probability":
                float(
                    quant_row[
                        "up_probability"
                    ]
                ),
            "down_probability":
                float(
                    quant_row[
                        "down_probability"
                    ]
                ),
            "regime_prediction":
                quant_row[
                    "regime_prediction"
                ],
            "bear_probability":
                float(
                    quant_row[
                        "bear_probability"
                    ]
                ),
            "sideways_probability":
                float(
                    quant_row[
                        "sideways_probability"
                    ]
                ),
            "bull_probability":
                float(
                    quant_row[
                        "bull_probability"
                    ]
                ),
            "predicted_volatility":
                float(
                    quant_row[
                        "predicted_volatility"
                    ]
                ),
            "volatility_regime":
                quant_row[
                    "volatility_regime"
                ],
            "combined_score":
                float(
                    quant_row[
                        "combined_score"
                    ]
                ),
            "confidence":
                float(
                    quant_row[
                        "confidence"
                    ]
                ),
            "signal":
                quant_row[
                    "signal"
                ],
            "strength":
                quant_row[
                    "strength"
                ],
            "trade_suitability":
                quant_row[
                    "trade_suitability"
                ],
            "option_chain":
                option_data,
        }

        return state

    # ========================================================
    # DETECT CHANGES
    # ========================================================

    @staticmethod
    def detect_changes(
        previous,
        current,
    ):

        if previous is None:
            return {
                "status": "IMPORTANT",
                "direction_change":
                    "Initial state",
                "regime_change":
                    "Initial state",
                "volatility_change":
                    "Initial state",
                "option_change":
                    "Initial state",
                "score_change": 0.0,
            }

        changes = {
            "direction_change": "UNCHANGED",
            "regime_change": "UNCHANGED",
            "volatility_change": "UNCHANGED",
            "option_change": "UNCHANGED",
            "score_change": (
                current["combined_score"]
                - previous["combined_score"]
            ),
        }

        # ----------------------------------------------------
        # DIRECTION
        # ----------------------------------------------------

        if (
            current["direction_prediction"]
            != previous[
                "direction_prediction"
            ]
        ):

            changes[
                "direction_change"
            ] = (
                f"{previous['direction_prediction']} "
                f"→ "
                f"{current['direction_prediction']}"
            )

        elif abs(
            current["up_probability"]
            - previous["up_probability"]
        ) >= 0.10:

            changes[
                "direction_change"
            ] = (
                "Probability changed materially"
            )

        # ----------------------------------------------------
        # REGIME
        # ----------------------------------------------------

        if (
            current["regime_prediction"]
            != previous[
                "regime_prediction"
            ]
        ):

            changes[
                "regime_change"
            ] = (
                f"{previous['regime_prediction']} "
                f"→ "
                f"{current['regime_prediction']}"
            )

        # ----------------------------------------------------
        # VOLATILITY
        # ----------------------------------------------------

        if (
            current["volatility_regime"]
            != previous[
                "volatility_regime"
            ]
        ):

            changes[
                "volatility_change"
            ] = (
                f"{previous['volatility_regime']} "
                f"→ "
                f"{current['volatility_regime']}"
            )

        elif abs(
            current["predicted_volatility"]
            - previous["predicted_volatility"]
        ) >= 0.05:

            changes[
                "volatility_change"
            ] = (
                "Predicted volatility changed materially"
            )

        # ----------------------------------------------------
        # OPTION CHAIN
        # ----------------------------------------------------

        current_options = (
            current.get(
                "option_chain"
            ) or {}
        )

        previous_options = (
            previous.get(
                "option_chain"
            ) or {}
        )

        if current_options and previous_options:

            current_pcr = float(
                current_options.get(
                    "put_call_oi_ratio",
                    0.0
                ) or 0.0
            )

            previous_pcr = float(
                previous_options.get(
                    "put_call_oi_ratio",
                    0.0
                ) or 0.0
            )

            current_support = (
                current_options.get(
                    "support"
                )
            )

            previous_support = (
                previous_options.get(
                    "support"
                )
            )

            current_resistance = (
                current_options.get(
                    "resistance"
                )
            )

            previous_resistance = (
                previous_options.get(
                    "resistance"
                )
            )

            if abs(
                current_pcr
                - previous_pcr
            ) >= 0.10:

                changes[
                    "option_change"
                ] = (
                    "PCR changed materially"
                )

            if (
                current_support
                != previous_support
            ):

                changes[
                    "option_change"
                ] = (
                    "Support changed"
                )

            if (
                current_resistance
                != previous_resistance
            ):

                changes[
                    "option_change"
                ] = (
                    "Resistance changed"
                )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        meaningful = any(
            value != "UNCHANGED"
            for key, value in changes.items()
            if key.endswith("_change")
        )

        large_score_change = (
            abs(
                changes["score_change"]
            ) >= 0.15
        )

        if large_score_change:
            changes["status"] = "IMPORTANT"

        elif meaningful:
            changes["status"] = "CHANGED"

        else:
            changes["status"] = "UNCHANGED"

        return changes

    # ========================================================
    # AI ALERT
    # ========================================================

    def generate_alert(
        self,
        previous,
        current,
        changes,
    ):

        payload = {
            "previous": previous,
            "current": current,
            "changes": changes,
        }

        prompt = f"""
You are TradingAI's Intraday Monitor.

Compare the previous market state with the current state.

Use ONLY the supplied data.

RULES:
- Do not invent data.
- Do not invent news.
- Do not guarantee profits.
- Do not give personalized financial advice.
- Only call a change important when the supplied data supports it.
- Be concise.

DATA:

{json.dumps(payload, indent=2, default=str)}

Return:

status:
UNCHANGED, CHANGED, or IMPORTANT.

market_bias:
BULLISH, BEARISH, or NEUTRAL.

change_summary:
Summarize the important changes.

direction_change:
Explain Direction changes.

regime_change:
Explain Regime changes.

volatility_change:
Explain Volatility changes.

option_change:
Explain Option-chain changes.

risk:
Explain the main current risk.

action:
State what should be monitored next.
Do not give personalized trade instructions.
"""

        response = None
        last_error = None

        for attempt in range(3):

            try:

                print(
                    f"[INTRADAY] Gemini request "
                    f"{attempt + 1}/3..."
                )

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            max_output_tokens=1200,
                            response_mime_type="application/json",
                            response_schema=IntradayAlert,
                        ),
                    )
                )

                break

            except Exception as exc:

                last_error = exc

                print(
                    f"[INTRADAY] Attempt "
                    f"{attempt + 1}/3 failed: "
                    f"{exc}"
                )

                if attempt < 2:
                    time.sleep(3)

        if response is None:

            raise RuntimeError(
                f"Intraday Gemini request failed: "
                f"{last_error}"
            )

        parsed = getattr(
            response,
            "parsed",
            None
        )

        alert = None

        if isinstance(
            parsed,
            IntradayAlert
        ):

            alert = parsed

        elif isinstance(
            parsed,
            dict
        ):

            alert = IntradayAlert(
                **parsed
            )

        if alert is None:

            text = getattr(
                response,
                "text",
                None
            )

            if not text:

                raise RuntimeError(
                    "Gemini returned empty intraday alert."
                )

            try:

                alert = IntradayAlert(
                    **json.loads(text)
                )

            except Exception as exc:

                raise RuntimeError(
                    f"Invalid intraday alert: {exc}"
                ) from exc

        return self._format_alert(
            alert
        )

    # ========================================================
    # FORMAT
    # ========================================================

    @staticmethod
    def _format_alert(
        alert: IntradayAlert,
    ):

        return (
            "STATUS:\n"
            f"{alert.status}\n\n"

            "MARKET BIAS:\n"
            f"{alert.market_bias}\n\n"

            "CHANGE SUMMARY:\n"
            f"{alert.change_summary}\n\n"

            "DIRECTION CHANGE:\n"
            f"{alert.direction_change}\n\n"

            "REGIME CHANGE:\n"
            f"{alert.regime_change}\n\n"

            "VOLATILITY CHANGE:\n"
            f"{alert.volatility_change}\n\n"

            "OPTION CHANGE:\n"
            f"{alert.option_change}\n\n"

            "RISK:\n"
            f"{alert.risk}\n\n"

            "ACTION:\n"
            f"{alert.action}"
        )

    # ========================================================
    # CHECK ONCE
    # ========================================================

    def check_once(self):

        current = (
            self.get_current_state()
        )

        changes = (
            self.detect_changes(
                self.previous_state,
                current,
            )
        )

        result = self.generate_alert(
            self.previous_state,
            current,
            changes,
        )

        self.previous_state = current

        return result

    # ========================================================
    # MONITOR LOOP
    # ========================================================

    def monitor(
        self,
        interval_seconds=300,
        max_cycles=None,
    ):

        cycles = 0

        print("=" * 70)
        print("TradingAI - INTRADAY MONITOR")
        print("=" * 70)

        while True:

            try:

                print(
                    "\n"
                    + "=" * 70
                )

                print(
                    "INTRADAY CHECK:",
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )

                print(
                    "=" * 70
                )

                result = (
                    self.check_once()
                )

                print()
                print(result)

            except KeyboardInterrupt:

                print(
                    "\n[INTRADAY] Monitor stopped."
                )

                break

            except Exception as exc:

                print(
                    f"[INTRADAY] Error: {exc}"
                )

            cycles += 1

            if (
                max_cycles is not None
                and cycles >= max_cycles
            ):
                break

            time.sleep(
                interval_seconds
            )