# ============================================================
# TradingAI - RISK ENGINE
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class RiskConfig:
    capital: float
    risk_per_trade_pct: float = 1.0
    max_daily_loss_pct: float = 3.0
    max_positions: int = 1
    min_risk_reward: float = 1.5
    max_position_value_pct: float = 100.0


class RiskEngine:
    """Deterministic trade risk calculator and gate.

    It does not predict direction. It only validates a proposed
    trade and calculates risk-aware quantity / R:R / limits.
    """

    def __init__(self, config: RiskConfig):
        if config.capital <= 0:
            raise ValueError("Capital must be > 0")
        if not 0 < config.risk_per_trade_pct <= 100:
            raise ValueError("risk_per_trade_pct must be between 0 and 100")
        if not 0 < config.max_daily_loss_pct <= 100:
            raise ValueError("max_daily_loss_pct must be between 0 and 100")
        if config.max_positions < 1:
            raise ValueError("max_positions must be >= 1")
        if config.min_risk_reward <= 0:
            raise ValueError("min_risk_reward must be > 0")
        if not 0 < config.max_position_value_pct <= 100:
            raise ValueError("max_position_value_pct must be between 0 and 100")

        self.config = config

    # ========================================================
    # LIMITS
    # ========================================================

    @property
    def risk_amount_limit(self) -> float:
        return self.config.capital * self.config.risk_per_trade_pct / 100.0

    @property
    def daily_loss_limit(self) -> float:
        return self.config.capital * self.config.max_daily_loss_pct / 100.0

    @property
    def max_position_value(self) -> float:
        return self.config.capital * self.config.max_position_value_pct / 100.0

    # ========================================================
    # EVALUATE
    # ========================================================

    def evaluate(
        self,
        *,
        entry: float,
        stop_loss: float,
        target: float,
        quantity: Optional[int] = None,
        current_daily_pnl: float = 0.0,
        open_positions: int = 0,
        side: str = "LONG",
    ) -> dict:

        side = str(side).upper().strip()
        if side not in {"LONG", "SHORT"}:
            return self._blocked("INVALID_SIDE")

        try:
            entry = float(entry)
            stop_loss = float(stop_loss)
            target = float(target)
            current_daily_pnl = float(current_daily_pnl)
        except (TypeError, ValueError):
            return self._blocked("INVALID_NUMERIC_INPUT")

        if entry <= 0 or stop_loss <= 0 or target <= 0:
            return self._blocked("PRICES_MUST_BE_POSITIVE")

        # Directional validation.
        if side == "LONG":
            if not stop_loss < entry:
                return self._blocked("LONG_STOP_MUST_BE_BELOW_ENTRY")
            if not target > entry:
                return self._blocked("LONG_TARGET_MUST_BE_ABOVE_ENTRY")
        else:
            if not stop_loss > entry:
                return self._blocked("SHORT_STOP_MUST_BE_ABOVE_ENTRY")
            if not target < entry:
                return self._blocked("SHORT_TARGET_MUST_BE_BELOW_ENTRY")

        risk_per_unit = abs(entry - stop_loss)
        reward_per_unit = abs(target - entry)
        rr = reward_per_unit / risk_per_unit if risk_per_unit else 0.0

        if rr < self.config.min_risk_reward:
            return self._blocked(
                "RISK_REWARD_BELOW_MINIMUM",
                risk_per_unit=risk_per_unit,
                reward_per_unit=reward_per_unit,
                risk_reward_ratio=rr,
            )

        # Risk budget after today's realized P&L.
        daily_loss_used = max(0.0, -current_daily_pnl)
        remaining_daily_loss = max(
            0.0,
            self.daily_loss_limit - daily_loss_used,
        )

        if remaining_daily_loss <= 0:
            return self._blocked(
                "DAILY_LOSS_LIMIT_REACHED",
                risk_per_unit=risk_per_unit,
                reward_per_unit=reward_per_unit,
                risk_reward_ratio=rr,
                remaining_daily_loss=remaining_daily_loss,
            )

        if open_positions >= self.config.max_positions:
            return self._blocked(
                "MAX_OPEN_POSITIONS_REACHED",
                risk_per_unit=risk_per_unit,
                reward_per_unit=reward_per_unit,
                risk_reward_ratio=rr,
                remaining_daily_loss=remaining_daily_loss,
            )

        max_allowed_risk = min(
            self.risk_amount_limit,
            remaining_daily_loss,
        )

        # Quantity from risk budget.
        calculated_quantity = int(
            max_allowed_risk // risk_per_unit
        )

        if quantity is not None:
            try:
                requested_quantity = int(quantity)
            except (TypeError, ValueError):
                return self._blocked("INVALID_QUANTITY")
            if requested_quantity <= 0:
                return self._blocked("QUANTITY_MUST_BE_POSITIVE")
            calculated_quantity = min(
                calculated_quantity,
                requested_quantity,
            )

        if calculated_quantity <= 0:
            return self._blocked("RISK_BUDGET_TOO_SMALL_FOR_ONE_UNIT")

        position_value = entry * calculated_quantity

        if position_value > self.max_position_value:
            value_limited_qty = int(
                self.max_position_value // entry
            )
            calculated_quantity = min(
                calculated_quantity,
                value_limited_qty,
            )
            position_value = entry * calculated_quantity

        if calculated_quantity <= 0:
            return self._blocked("POSITION_VALUE_LIMIT_TOO_LOW")

        total_trade_risk = risk_per_unit * calculated_quantity
        total_trade_reward = reward_per_unit * calculated_quantity
        risk_pct = total_trade_risk / self.config.capital * 100.0

        # Caution if the setup uses most of the daily remaining loss budget.
        status = "ALLOWED"
        if total_trade_risk > self.risk_amount_limit * 0.8:
            status = "CAUTION"
        if remaining_daily_loss > 0 and total_trade_risk > remaining_daily_loss * 0.8:
            status = "CAUTION"

        return {
            "allowed": True,
            "status": status,
            "reason": "RISK_CHECK_PASSED",
            "side": side,
            "entry": entry,
            "stop_loss": stop_loss,
            "target": target,
            "quantity": int(calculated_quantity),
            "risk_per_unit": risk_per_unit,
            "reward_per_unit": reward_per_unit,
            "risk_amount": total_trade_risk,
            "reward_amount": total_trade_reward,
            "risk_percent": risk_pct,
            "risk_reward_ratio": rr,
            "position_value": position_value,
            "daily_loss_limit": self.daily_loss_limit,
            "daily_loss_used": daily_loss_used,
            "remaining_daily_loss": remaining_daily_loss,
            "open_positions": open_positions,
            "max_positions": self.config.max_positions,
        }

    # ========================================================
    # BLOCK HELPER
    # ========================================================

    @staticmethod
    def _blocked(reason: str, **extra) -> dict:
        result = {
            "allowed": False,
            "status": "BLOCKED",
            "reason": reason,
        }
        result.update(extra)
        return result

    # ========================================================
    # CONFIG / STATUS
    # ========================================================

    def status(self) -> dict:
        return {
            "config": asdict(self.config),
            "risk_amount_limit": self.risk_amount_limit,
            "daily_loss_limit": self.daily_loss_limit,
            "max_position_value": self.max_position_value,
        }