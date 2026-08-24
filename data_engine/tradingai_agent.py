from __future__ import annotations

from typing import Any, Dict


class TradingAITools:
    """
    Controlled deterministic tools available to the Step 7 agent.

    Tools only read the already-generated TradingAI result. They do not
    change trades, probabilities, risk, or engine state.
    """

    def __init__(self, result: Dict[str, Any]):
        self.result = (
            result
            if isinstance(result, dict)
            else {}
        )

    def get_top_trade(self) -> Dict[str, Any]:
        trades = self.result.get("trades") or []
        return trades[0] if trades else {}

    def get_trade_candidates(self):
        return self.result.get("trades") or []

    def get_risk(self) -> Dict[str, Any]:
        trade = self.get_top_trade()
        return trade.get("risk") or {}

    def get_unified_context(self) -> Dict[str, Any]:
        trade = self.get_top_trade()
        return trade.get("unified_components") or {}

    def get_reasons(self):
        trade = self.get_top_trade()
        return list(
            trade.get("reasons") or []
        )

    def get_warnings(self):
        trade = self.get_top_trade()
        return list(
            trade.get("warnings") or []
        )

    def compare_candidates(self):
        trades = self.get_trade_candidates()

        if not trades:
            return []

        best_score = float(
            trades[0].get(
                "ai_score",
                0,
            )
            or 0
        )

        comparison = []

        for trade in trades[1:]:
            score = float(
                trade.get(
                    "ai_score",
                    0,
                )
                or 0
            )

            comparison.append(
                {
                    "strike": trade.get("strike"),
                    "type": trade.get("type"),
                    "score": trade.get("ai_score"),
                    "probability": trade.get(
                        "probability"
                    ),
                    "score_difference": round(
                        best_score - score,
                        2,
                    ),
                }
            )

        return comparison


class TradingAIAgent:
    """
    Small controlled agent layer.

    The agent selects deterministic tools, collects their outputs, and
    provides that evidence to the Gemini explanation layer.
    """

    TOOL_NAMES = (
        "get_top_trade",
        "get_trade_candidates",
        "get_risk",
        "get_unified_context",
        "get_reasons",
        "get_warnings",
        "compare_candidates",
    )

    def __init__(self, result: Dict[str, Any]):
        self.tools = TradingAITools(result)

    def inspect_trade(self) -> Dict[str, Any]:

        return {
            "top_trade": self.tools.get_top_trade(),
            "risk": self.tools.get_risk(),
            "unified_context":
                self.tools.get_unified_context(),
            "reasons":
                self.tools.get_reasons(),
            "warnings":
                self.tools.get_warnings(),
            "candidate_comparison":
                self.tools.compare_candidates(),
        }