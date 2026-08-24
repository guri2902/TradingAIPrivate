from pathlib import Path
from tempfile import TemporaryDirectory
from data_engine.prediction_tracker import PredictionTracker

with TemporaryDirectory() as tmp:
    tracker = PredictionTracker(tmp)

    result = {
        "selected_index": "NIFTY 50",
        "selected_expiry": "2026-08-25",
        "trades": [
            {
                "strike": 24250.0,
                "type": "CE",
                "premium": 100.0,
                "ai_score": 73.0,
                "probability": 65.0,
                "recommendation": "TRADEABLE SETUP",
                "reasons": ["Market supports CE"],
                "warnings": [],
                "risk": {
                    "sl": 90.0,
                    "target1": 120.0,
                    "target2": 140.0,
                    "target3": 160.0,
                    "rr": 2.67,
                    "position_size": 34,
                    "max_loss": 500.0,
                },
                "unified_components": {
                    "ml_score": 0,
                    "futures_score": 5,
                },
            },
            {
                "strike": 24300.0,
                "type": "CE",
                "premium": 70.0,
                "ai_score": 68.0,
                "probability": 64.0,
                "recommendation": "WATCH",
                "risk": {
                    "sl": 60.0,
                    "target1": 90.0,
                    "target2": 110.0,
                },
            },
        ],
    }

    ids = tracker.record_generation(result)
    assert len(ids) == 2

    stats = tracker.trade_statistics()
    assert stats["total_predictions"] == 2
    assert stats["pending_predictions"] == 2

    tracker.update_market_snapshot(
        "NIFTY 50",
        [{
            "strike": 24250.0,
            "ce_ltp": 121.0,
            "pe_ltp": 80.0,
        }]
    )

    stats = tracker.trade_statistics()
    assert stats["target1_hits"] == 1
    assert stats["win_rate"] == 100.0

    rows = tracker.load_trade_predictions()
    first = rows.iloc[0].to_dict()
    assert first["entry"] == 100.0
    assert first["stop_loss"] == 90.0
    assert first["target1"] == 120.0
    assert first["target2"] == 140.0
    assert first["ai_score"] == 73.0
    assert first["probability"] == 65.0

print("EXISTING PREDICTION TRACKER STEP 8 TEST PASSED")