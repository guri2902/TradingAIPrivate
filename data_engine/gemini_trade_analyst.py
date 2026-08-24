from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests

from data_engine.tradingai_agent import TradingAIAgent


class GeminiTradeAnalyst:
    """
    Gemini explanation layer for Step 7.

    It explains the deterministic TradingAI result. It does not create,
    modify, rank, or risk-manage trades.
    """

    DEFAULT_MODEL = "gemini-3.5-flash-lite"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
    ):
        self.api_key = (
            api_key or os.getenv("GEMINI_API_KEY")
        )
        self.model = (
            model
            or os.getenv(
                "GEMINI_MODEL",
                self.DEFAULT_MODEL,
            )
        )
        self.timeout = int(timeout)

    @property
    def available(self) -> bool:
        return bool(
            self.api_key
            and self.api_key.strip()
        )

    def explain_trade_result(
        self,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(result, dict):
            return {
                "available": False,
                "error": "Invalid trade result.",
                "text": "",
            }

        if not self.available:
            return {
                "available": False,
                "error": "GEMINI_API_KEY is not configured.",
                "text": "",
            }

        # Step 7 agent layer: collect evidence through controlled,
        # read-only TradingAI tools before Gemini sees the data.
        agent = TradingAIAgent(result)
        agent_evidence = agent.inspect_trade()

        safe_result = self._build_safe_payload(result)
        safe_result["agent_evidence"] = agent_evidence

        prompt = self._build_prompt(safe_result)

        url = (
            "https://generativelanguage.googleapis.com"
            f"/v1beta/models/{self.model}:generateContent"
        )

        try:
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": prompt}
                            ],
                        }
                    ]
                },
                timeout=self.timeout,
            )

            if not response.ok:
                return {
                    "available": False,
                    "error": (
                        f"Gemini API HTTP "
                        f"{response.status_code}: "
                        f"{self._response_error(response)}"
                    ),
                    "text": "",
                }

            data = response.json()
            text = self._extract_text(data)

            if not text:
                return {
                    "available": False,
                    "error": "Gemini returned an empty response.",
                    "text": "",
                }

            return {
                "available": True,
                "error": None,
                "text": text,
                "model": self.model,
            }

        except requests.RequestException as exc:
            return {
                "available": False,
                "error": f"Gemini request failed: {exc}",
                "text": "",
            }

        except (ValueError, TypeError, KeyError) as exc:
            return {
                "available": False,
                "error": (
                    f"Gemini response parsing failed: {exc}"
                ),
                "text": "",
            }

    @staticmethod
    def _build_safe_payload(
        result: Dict[str, Any],
    ) -> Dict[str, Any]:

        trades = []

        for trade in result.get("trades") or []:
            if not isinstance(trade, dict):
                continue

            risk = trade.get("risk") or {}
            unified = trade.get("unified_components") or {}

            trades.append(
                {
                    "strike": trade.get("strike"),
                    "type": trade.get("type"),
                    "recommendation": trade.get("recommendation"),
                    "ai_score": trade.get("ai_score"),
                    "probability": trade.get("probability"),
                    "premium": trade.get("premium"),
                    "reasons": list(
                        trade.get("reasons") or []
                    ),
                    "warnings": list(
                        trade.get("warnings") or []
                    ),
                    "risk": {
                        "entry": risk.get("entry"),
                        "sl": risk.get("sl"),
                        "target1": risk.get("target1"),
                        "target2": risk.get("target2"),
                        "target3": risk.get("target3"),
                        "rr": risk.get("rr"),
                        "position_size": risk.get("position_size"),
                        "max_loss": risk.get("max_loss"),
                    },
                    "unified_components": {
                        "ml_score": unified.get("ml_score"),
                        "ml_direction_probability": unified.get(
                            "ml_direction_probability"
                        ),
                        "ml_signal": unified.get("ml_signal"),
                        "ml_regime": unified.get("ml_regime"),
                        "futures_score": unified.get("futures_score"),
                    },
                }
            )

        return {
            "selected_index": result.get("selected_index"),
            "expiry": result.get("expiry"),
            "trades": trades,
        }

    @staticmethod
    def _build_prompt(
        payload: Dict[str, Any],
    ) -> str:

        data = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

        return f"""
You are the explanation layer inside a trading application.

TradingAI already generated and ranked the trades below.
Do NOT invent a new trade and do NOT modify any supplied number.

You must not change:
- AI score
- probability
- entry
- stop loss
- targets
- risk/reward
- position size
- ranking

Use the controlled TradingAI agent evidence supplied in the payload.
The agent tools are read-only and authoritative for the supplied data.
Explain the existing top-ranked trade and compare it with the other
generated candidates.

Use exactly these headings:

WHY THIS TRADE
WHY THIS STRIKE
WHY IT IS BETTER
SUPPORTING EVIDENCE
CONFLICTS / RISKS
WHAT WOULD INVALIDATE IT
FINAL AI ASSESSMENT

Use concise bullet points.

Rules:
1. Every numeric value must come from the supplied data.
2. Never call the probability statistically calibrated.
3. If ML is UNAVAILABLE, say ML is unavailable.
4. Mention conflicting evidence instead of hiding it.
5. Do not promise profit or certainty.
6. Treat risk values as fixed.
7. Explain the engine output; never replace the engine output.

TRADINGAI DATA:
{data}
""".strip()

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        texts = []

        for candidate in data.get("candidates") or []:
            content = candidate.get("content") or {}

            for part in content.get("parts") or []:
                text = part.get("text")

                if text:
                    texts.append(str(text).strip())

        return "\n".join(
            item for item in texts if item
        ).strip()

    @staticmethod
    def _response_error(response) -> str:
        try:
            data = response.json()
            error = data.get("error") or {}
            message = error.get("message")

            if message:
                return str(message)

            return json.dumps(
                data,
                ensure_ascii=False,
            )

        except Exception:
            return response.text or "Unknown Gemini error"