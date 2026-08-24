from pathlib import Path
import ast

dashboard = (
    Path(__file__).resolve().parent
    / "dashboard_current_step11_updated.py"
)

source = dashboard.read_text(
    encoding="utf-8"
)

ast.parse(source)

assert "class Dashboard" in source
assert "PredictionTracker" in source
assert "def track_ai_trade_prediction(" in source
assert "self.prediction_tracker.track(" in source
assert "self.tracked_trades.append(" in source

print("STEP 11 CURRENT DASHBOARD TRACKER WIRING TEST PASSED")