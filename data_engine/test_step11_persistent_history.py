from data_engine.step11_performance_analyzer import TradePerformanceAnalyzer

analyzer = TradePerformanceAnalyzer()

history = analyzer.history_summary()
tracker = analyzer.tracker_summary()

assert isinstance(history, dict)
assert isinstance(tracker, dict)
assert "rows" in history
assert "available" in tracker

print("STEP 11 PERSISTENT HISTORY CONNECTION TEST PASSED")
print(
    f"Persistent history available: "
    f"{history.get('available')}"
)
print(
    f"Persistent rows: "
    f"{history.get('rows', 0)}"
)
print(
    f"Persistent resolved: "
    f"{history.get('resolved', 0)}"
)
print(
    f"Persistent win rate: "
    f"{history.get('win_rate', 0.0)}%"
)
print(
    f"Tracker available: "
    f"{tracker.get('available')}"
)
print(
    f"Tracker predictions: "
    f"{tracker.get('prediction_records', 0)}"
)
print(
    f"Tracker pending: "
    f"{tracker.get('pending_records', 0)}"
)