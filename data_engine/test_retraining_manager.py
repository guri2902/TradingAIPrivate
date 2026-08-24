# ============================================================
# TradingAI - RETRAINING MANAGER TEST
# ============================================================

from pathlib import Path
import tempfile

from data_engine.retraining_manager import (
    RetrainingManager,
)


print("=" * 70)
print("TradingAI - RETRAINING MANAGER TEST")
print("=" * 70)


manager = RetrainingManager(
    minimum_training_samples=500,
    minimum_new_samples=100,
)


# ============================================================
# TEST 1 - CURRENT REAL DATA
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - CURRENT DATA SAFETY")
print("=" * 70)

current_result = manager.can_retrain(
    total_samples=1,
    new_samples=1,
    weakness_report={
        "status":
            "INSUFFICIENT_EVIDENCE",
        "total_weaknesses":
            0,
    },
)

print(
    current_result
)

if current_result["eligible"]:

    raise RuntimeError(
        "Retraining should NOT be allowed "
        "with the current tiny dataset."
    )


# ============================================================
# TEST 2 - ENOUGH DATA BUT NO WEAKNESS
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - DATA WITHOUT CONFIRMED WEAKNESS")
print("=" * 70)

result = manager.can_retrain(
    total_samples=1000,
    new_samples=200,
    weakness_report={
        "status":
            "NO_MAJOR_WEAKNESSES",
        "total_weaknesses":
            0,
    },
)

print(
    result
)

if result["eligible"]:

    raise RuntimeError(
        "Retraining should require "
        "confirmed weakness."
    )


# ============================================================
# TEST 3 - VALID RETRAINING CONDITIONS
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - VALID RETRAINING CONDITIONS")
print("=" * 70)

result = manager.can_retrain(
    total_samples=1000,
    new_samples=200,
    weakness_report={
        "status":
            "WEAKNESSES_DETECTED",
        "total_weaknesses":
            2,
    },
)

print(
    result
)

if not result["eligible"]:

    raise RuntimeError(
        "Valid retraining conditions "
        "were rejected."
    )


# ============================================================
# TEST 4 - CANDIDATE VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - CANDIDATE VALIDATION")
print("=" * 70)

approved = manager.validate_candidate(
    current_metrics={
        "accuracy": 0.55,
    },
    candidate_metrics={
        "accuracy": 0.60,
    },
)

print(
    f"Better candidate: {approved}"
)

if not approved["approved"]:

    raise RuntimeError(
        "Improved candidate was rejected."
    )

rejected = manager.validate_candidate(
    current_metrics={
        "accuracy": 0.60,
    },
    candidate_metrics={
        "accuracy": 0.55,
    },
)

print(
    f"Worse candidate: {rejected}"
)

if rejected["approved"]:

    raise RuntimeError(
        "Worse candidate was approved."
    )


# ============================================================
# TEST 5 - BACKUP / PROMOTION
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - BACKUP AND PROMOTION")
print("=" * 70)

with tempfile.TemporaryDirectory() as temp_dir:

    test_manager = RetrainingManager(
        model_dir=temp_dir
    )

    model_path = (
        Path(temp_dir)
        / "direction_model.pkl"
    )

    candidate_path = (
        Path(temp_dir)
        / "candidate_direction.pkl"
    )

    model_path.write_bytes(
        b"old-model"
    )

    candidate_path.write_bytes(
        b"new-model"
    )

    result = (
        test_manager.promote_candidate(
            candidate_path=
                candidate_path,

            model_name=
                "direction_model.pkl",
        )
    )

    print(
        result
    )

    if not result[
        "promoted"
    ]:

        raise RuntimeError(
            "Candidate model was not promoted."
        )

    backup = (
        Path(
            result["backup"]
        )
        if result["backup"]
        else None
    )

    if (
        backup is None
        or not backup.exists()
    ):

        raise RuntimeError(
            "Current model backup was not created."
        )

    if model_path.read_bytes() != b"new-model":

        raise RuntimeError(
            "Candidate was not copied correctly."
        )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("RETRAINING MANAGER TEST PASSED")
print("=" * 70)