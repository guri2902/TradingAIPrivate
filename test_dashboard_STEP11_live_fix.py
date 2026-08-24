from pathlib import Path
import ast

p=Path(__file__).resolve().parent / "dashboard.py"
s=p.read_text(encoding="utf-8")
ast.parse(s)
assert "PredictionTracker" in s
assert "self.prediction_tracker.record_generation(" in s
assert "self.prediction_tracker.update_market_snapshot(" in s
print("STEP 11 DASHBOARD LIVE FIX TEST PASSED")
