from pathlib import Path
import ast

dashboard = Path(__file__).resolve().parent / "dashboard_step11_final_resolution.py"
source = dashboard.read_text(encoding="utf-8")

ast.parse(source)

assert "def update_current_trade_prices(" in source
assert "self.prediction_tracker.update_market_snapshot(" in source
assert "self.prediction_tracker = PredictionTracker()" in source

print("STEP 11 LIVE OUTCOME RESOLUTION TEST PASSED")