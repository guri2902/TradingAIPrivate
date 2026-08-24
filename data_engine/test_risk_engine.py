# ============================================================
# TradingAI - RISK ENGINE TEST
# ============================================================

from data_engine.risk_engine import RiskConfig, RiskEngine


print("=" * 70)
print("TradingAI - RISK ENGINE TEST")
print("=" * 70)

engine = RiskEngine(
    RiskConfig(
        capital=100000,
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_positions=1,
        min_risk_reward=1.5,
        max_position_value_pct=100.0,
    )
)

print("\nTEST 1 - ENGINE STATUS")
print(engine.status())

print("\nTEST 2 - VALID LONG")
valid = engine.evaluate(
    entry=100,
    stop_loss=98,
    target=104,
    open_positions=0,
    side="LONG",
)
print(valid)
assert valid["allowed"] is True
assert valid["risk_reward_ratio"] == 2.0

print("\nTEST 3 - BAD R:R")
blocked_rr = engine.evaluate(
    entry=100,
    stop_loss=98,
    target=101,
    side="LONG",
)
print(blocked_rr)
assert blocked_rr["allowed"] is False
assert blocked_rr["reason"] == "RISK_REWARD_BELOW_MINIMUM"

print("\nTEST 4 - DAILY LOSS LIMIT")
blocked_daily = engine.evaluate(
    entry=100,
    stop_loss=98,
    target=104,
    current_daily_pnl=-3000,
    side="LONG",
)
print(blocked_daily)
assert blocked_daily["allowed"] is False
assert blocked_daily["reason"] == "DAILY_LOSS_LIMIT_REACHED"

print("\nTEST 5 - POSITION LIMIT")
blocked_positions = engine.evaluate(
    entry=100,
    stop_loss=98,
    target=104,
    open_positions=1,
    side="LONG",
)
print(blocked_positions)
assert blocked_positions["allowed"] is False
assert blocked_positions["reason"] == "MAX_OPEN_POSITIONS_REACHED"

print("\nTEST 6 - VALID SHORT")
valid_short = engine.evaluate(
    entry=100,
    stop_loss=102,
    target=96,
    side="SHORT",
)
print(valid_short)
assert valid_short["allowed"] is True
assert valid_short["risk_reward_ratio"] == 2.0

print("\n" + "=" * 70)
print("RISK ENGINE TEST PASSED")
print("=" * 70)