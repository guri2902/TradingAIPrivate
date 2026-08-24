from pathlib import Path
import tempfile
import json
import pandas as pd

from data_engine.step11_data_collector import Step11DataCollector


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

    # The current generic PredictionTracker in the project has no option
    # trade fields, so live import must safely no-op.
    imported = collector.collect_live_tracker_trades()

    assert imported == 0

print("STEP 11 LIVE TRACKER COLLECTION TEST PASSED")