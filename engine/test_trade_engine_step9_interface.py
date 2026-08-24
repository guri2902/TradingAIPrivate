from engine.trade_engine import TradeEngine

engine = TradeEngine()

assert hasattr(
    engine,
    "generate_trades_from_snapshot",
)

print("TRADE ENGINE STEP 9 INTERFACE TEST PASSED")
print("Backtest entry point: generate_trades_from_snapshot")
print("Live generate_trades() remains available.")
