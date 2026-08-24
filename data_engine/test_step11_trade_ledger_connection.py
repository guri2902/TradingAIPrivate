from data_engine.prediction_tracker import PredictionTracker
from data_engine.step11_data_collector import Step11DataCollector

tracker = PredictionTracker()

trade_df = tracker.load_trade_predictions()

collector = Step11DataCollector()

assert trade_df is not None
assert hasattr(tracker, "load_trade_predictions")
assert hasattr(collector, "collect_live_tracker_trades")

print("STEP 11 TRADE LEDGER CONNECTION TEST PASSED")
print(
    f"Trade prediction records: {len(trade_df)}"
)
print(
    f"Trade ledger columns: {list(trade_df.columns)}"
)