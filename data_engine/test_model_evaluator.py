# ============================================================
# TradingAI - MODEL EVALUATOR TEST
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.model_evaluator import (
    ModelEvaluator,
)


print("=" * 70)
print("TradingAI - MODEL EVALUATOR TEST")
print("=" * 70)


# ============================================================
# TEST 1 - LOAD
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD PREDICTIONS")
print("=" * 70)

evaluator = ModelEvaluator(
    minimum_sample_size=20
)

df = evaluator.load_predictions()

print(
    f"Resolved predictions: {len(df)}"
)

print(
    f"Prediction file exists: "
    f"{evaluator.prediction_file.exists()}"
)


# ============================================================
# TEST 2 - FULL EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - EVALUATE MODELS")
print("=" * 70)

report = evaluator.evaluate()

if not isinstance(
    report,
    dict,
):

    raise RuntimeError(
        "Evaluator did not return a dictionary."
    )

required_keys = [
    "total_predictions",
    "resolved_predictions",
    "pending_predictions",
    "direction",
    "confidence",
    "volatility",
    "signal_performance",
    "score_buckets",
]

missing = [
    key
    for key in required_keys
    if key not in report
]

if missing:

    raise RuntimeError(
        f"Missing evaluation fields: {missing}"
    )


# ============================================================
# TEST 3 - REPORT
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - EVALUATION REPORT")
print("=" * 70)

evaluator.print_report(
    report
)


# ============================================================
# TEST 4 - SAMPLE SIZE SAFETY
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - SAMPLE SIZE VALIDATION")
print("=" * 70)

direction = report["direction"]

if direction["sample_size"] < 20:

    if direction["status"] != "INSUFFICIENT_SAMPLE":

        raise RuntimeError(
            "Evaluator failed sample-size protection."
        )

    print(
        "Small sample correctly marked: "
        "INSUFFICIENT_SAMPLE"
    )

else:

    if direction["status"] != "VALID_SAMPLE":

        raise RuntimeError(
            "Valid sample incorrectly marked."
        )

    print(
        "Sufficient sample correctly marked: "
        "VALID_SAMPLE"
    )

# ============================================================
# TEST 5 - OUTPUT TYPES
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - OUTPUT VALIDATION")
print("=" * 70)

if not isinstance(
    report["total_predictions"],
    int,
):

    raise RuntimeError(
        "total_predictions must be int."
    )

if not isinstance(
    report["resolved_predictions"],
    int,
):

    raise RuntimeError(
        "resolved_predictions must be int."
    )

if (
    report["resolved_predictions"]
    > report["total_predictions"]
):

    raise RuntimeError(
        "Resolved predictions exceed total predictions."
    )


print(
    "Evaluation structure valid."
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("MODEL EVALUATOR TEST PASSED")
print("=" * 70)