# ============================================================
# TradingAI - WEAKNESS DETECTOR TEST
# ============================================================

from data_engine.model_evaluator import (
    ModelEvaluator,
)

from data_engine.weakness_detector import (
    WeaknessDetector,
)


print("=" * 70)
print("TradingAI - WEAKNESS DETECTOR TEST")
print("=" * 70)


# ============================================================
# TEST 1 - LOAD EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD EVALUATION REPORT")
print("=" * 70)

evaluator = ModelEvaluator(
    minimum_sample_size=20
)

report = evaluator.evaluate()

print(
    f"Total predictions: "
    f"{report['total_predictions']}"
)

print(
    f"Resolved predictions: "
    f"{report['resolved_predictions']}"
)


# ============================================================
# TEST 2 - DETECTOR
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - RUN WEAKNESS DETECTION")
print("=" * 70)

detector = WeaknessDetector(
    minimum_sample_size=20
)

analysis = detector.analyze(
    report
)

if not isinstance(
    analysis,
    dict,
):

    raise RuntimeError(
        "Weakness detector returned invalid output."
    )

required_keys = [
    "status",
    "high_count",
    "medium_count",
    "total_weaknesses",
    "weaknesses",
]

missing = [
    key
    for key in required_keys
    if key not in analysis
]

if missing:

    raise RuntimeError(
        f"Missing weakness fields: {missing}"
    )


# ============================================================
# TEST 3 - CURRENT SMALL SAMPLE
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - SMALL SAMPLE SAFETY")
print("=" * 70)

if (
    report["resolved_predictions"]
    < 20
):

    if (
        analysis["status"]
        != "INSUFFICIENT_EVIDENCE"
    ):

        raise RuntimeError(
            "Weakness detector should reject "
            "small samples."
        )

    print(
        "Small sample correctly rejected "
        "as evidence."
    )

else:

    print(
        "Sufficient historical sample available."
    )


# ============================================================
# TEST 4 - SYNTHETIC VALID SAMPLE
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - SYNTHETIC WEAKNESS TEST")
print("=" * 70)

synthetic_report = {

    "direction": {
        "sample_size": 40,
        "accuracy": 0.40,
        "up_accuracy": 0.55,
        "down_accuracy": 0.25,
        "status": "VALID_SAMPLE",
    },

    "confidence": {
        "sample_size": 40,
        "average_confidence": 0.78,
        "actual_accuracy": 0.46,
        "confidence_gap": 0.32,
        "status": "VALID_SAMPLE",
    },

    "volatility": {
        "sample_size": 40,
        "mae": 0.08,
        "rmse": 0.10,
        "average_error": 0.06,
        "status": "VALID_SAMPLE",
    },

    "signal_performance": {
        "BEARISH": {
            "sample_size": 25,
            "accuracy": 0.40,
            "average_actual_return": -0.01,
            "status": "VALID_SAMPLE",
        },
    },

    "score_buckets": {
        "STRONG_BEARISH": {
            "sample_size": 25,
            "accuracy": 0.40,
            "average_actual_return": -0.005,
            "status": "VALID_SAMPLE",
        },
    },
}

synthetic_analysis = detector.analyze(
    synthetic_report
)

if (
    synthetic_analysis["status"]
    == "INSUFFICIENT_EVIDENCE"
):

    raise RuntimeError(
        "Synthetic valid sample was incorrectly rejected."
    )

if (
    synthetic_analysis["total_weaknesses"]
    < 1
):

    raise RuntimeError(
        "Expected synthetic weaknesses were not detected."
    )

print(
    f"Synthetic status: "
    f"{synthetic_analysis['status']}"
)

print(
    f"Weaknesses detected: "
    f"{synthetic_analysis['total_weaknesses']}"
)


# ============================================================
# TEST 5 - REPORT
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - WEAKNESS REPORT")
print("=" * 70)

detector.print_report(
    analysis
)

saved_path = detector.save_report(
    analysis
)

print(
    f"\nSaved: {saved_path}"
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("WEAKNESS DETECTOR TEST PASSED")
print("=" * 70)