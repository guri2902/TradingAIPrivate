from pathlib import Path
import json
import tempfile

from data_engine.step11_data_collector import (
    Step11DataCollector,
)

with tempfile.TemporaryDirectory() as tmp:

    root = Path(tmp)

    report_path = root / "step10.json"
    history_path = root / "history.parquet"

    report_path.write_text(
        json.dumps({"trades": []}),
        encoding="utf-8",
    )

    collector = Step11DataCollector(
        walk_forward_report=report_path,
        history_file=history_path,
    )

    live_rows = (
        collector.collect_live_tracker_trades()
    )

    # Current tracker is generic and does not contain the option-trade
    # schema yet, so this should safely return zero.
    assert live_rows == 0

print(
    "STEP 11 LIVE TRACKER COLLECTION TEST PASSED"
)
print(
    "Existing generic PredictionTracker compatibility: OK"
)