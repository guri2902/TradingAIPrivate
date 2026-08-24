from pathlib import Path
import json
import tempfile

from data_engine.step11_performance_analyzer import (
    TradePerformanceAnalyzer,
)


with tempfile.TemporaryDirectory() as tmp:

    report_path = (
        Path(tmp)
        / "step10.json"
    )

    report = {
        "trades": [
            {
                "type": "CE",
                "ai_score": 73,
                "probability": 65,
                "rr": 2.67,
                "outcome": "STOP_LOSS",
                "r_multiple": -1.0,
            },
            {
                "type": "PE",
                "ai_score": 82,
                "probability": 70,
                "rr": 2.0,
                "outcome": "TARGET_1",
                "r_multiple": 1.0,
            },
            {
                "type": "CE",
                "ai_score": 61,
                "probability": 60,
                "rr": 1.8,
                "outcome": "END_OF_DATA",
                "r_multiple": None,
            },
        ]
    }

    report_path.write_text(
        json.dumps(report),
        encoding="utf-8",
    )

    analyzer = (
        TradePerformanceAnalyzer(
            report_path
        )
    )

    result = analyzer.analyze()

    assert result[
        "total_candidates"
    ] == 3

    assert result[
        "resolved"
    ] == 2

    assert result[
        "overall_win_rate"
    ] == 50.0

    assert "70+" in result[
        "probability_analysis"
    ]

print(
    "STEP 11 PERFORMANCE ANALYZER TEST PASSED"
)