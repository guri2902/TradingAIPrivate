from pathlib import Path
import json
import tempfile

import pandas as pd

from data_engine.step11_data_collector import (
    Step11DataCollector,
)


with tempfile.TemporaryDirectory() as tmp:

    root = Path(tmp)

    report_path = root / "step10.json"
    history_path = (
        root / "history.parquet"
    )

    report = {
        "trades": [
            {
                "window": 1,
                "timestamp":
                    "2026-08-21T10:00:00",
                "expiry":
                    "2026-08-25",
                "strike": 24250,
                "type": "CE",
                "ai_score": 70,
                "probability": 65,
                "rr": 2.0,
                "entry": 100,
                "stop_loss": 90,
                "target1": 120,
                "target2": 140,
                "outcome":
                    "STOP_LOSS",
                "outcome_price": 90,
                "closed_at":
                    "2026-08-21T10:05:00",
                "r_multiple": -1.0,
            }
        ]
    }

    report_path.write_text(
        json.dumps(report),
        encoding="utf-8",
    )

    collector = Step11DataCollector(
        walk_forward_report=report_path,
        history_file=history_path,
    )

    first = collector.collect()

    assert first["new_rows"] == 1
    assert first["history_rows"] == 1

    second = collector.collect()

    assert second["new_rows"] == 0
    assert second["history_rows"] == 1

    df = pd.read_parquet(
        history_path
    )

    assert len(df) == 1
    assert df.iloc[0]["outcome"] == "STOP_LOSS"

print(
    "STEP 11 DATA COLLECTOR TEST PASSED"
)