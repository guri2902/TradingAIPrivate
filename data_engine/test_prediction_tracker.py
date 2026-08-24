# ============================================================
# TradingAI - PREDICTION TRACKER TEST
# ============================================================

from data_engine.prediction_tracker import (
    PredictionTracker,
)


print("=" * 70)
print("TradingAI - PREDICTION TRACKER TEST")
print("=" * 70)


# ============================================================
# TEST 1 - INITIALIZE
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - INITIALIZE TRACKER")
print("=" * 70)

tracker = PredictionTracker()

print(
    f"Prediction file: "
    f"{tracker.prediction_file}"
)

print(
    f"Pending file: "
    f"{tracker.pending_file}"
)


# ============================================================
# TEST 2 - CREATE PREDICTION
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - CREATE PREDICTION")
print("=" * 70)

sample_prediction = {

    "direction_prediction": 0,

    "up_probability": 0.388517,

    "down_probability": 0.611483,

    "regime_prediction": "BEAR",

    "bear_probability": 0.598946,

    "sideways_probability": 0.335384,

    "bull_probability": 0.065670,

    "predicted_volatility": 0.198430,

    "volatility_regime": "NORMAL",

    "direction_score": -0.222966,

    "regime_score": -0.533277,

    "volatility_modifier": 0.033734,

    "combined_score": -0.239049,

    "confidence": 0.585879,

    "signal": "BEARISH",

    "strength": "WEAK",

    "trade_suitability": "CAUTION",
}

record = tracker.create_record(
    symbol="RELIANCE",
    prediction=sample_prediction,
    horizon=1,
)

if not record.get(
    "prediction_id"
):

    raise RuntimeError(
        "Prediction ID was not created."
    )

print(
    f"Prediction ID: "
    f"{record['prediction_id']}"
)

print(
    f"Signal: "
    f"{record['signal']}"
)

print(
    f"Confidence: "
    f"{record['confidence']}"
)


# ============================================================
# TEST 3 - SAVE
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - SAVE PREDICTION")
print("=" * 70)

tracker.save_prediction(
    record
)

all_predictions = (
    tracker.load_predictions()
)

pending = (
    tracker.load_pending()
)

print(
    f"Total predictions: "
    f"{len(all_predictions)}"
)

print(
    f"Pending predictions: "
    f"{len(pending)}"
)

if len(all_predictions) < 1:

    raise RuntimeError(
        "Prediction was not saved."
    )

if len(pending) < 1:

    raise RuntimeError(
        "Prediction should initially be pending."
    )


# ============================================================
# TEST 4 - RECORD OUTCOME
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - RECORD ACTUAL OUTCOME")
print("=" * 70)

prediction_id = (
    record["prediction_id"]
)

outcome = tracker.record_outcome(
    prediction_id=prediction_id,
    actual_price=1290.0,
    reference_price=1310.0,
    actual_volatility=0.210,
)

print(
    f"Actual price: "
    f"{outcome['actual_price']}"
)

print(
    f"Actual return: "
    f"{outcome['actual_return']:.6f}"
)

print(
    f"Actual direction: "
    f"{outcome['actual_direction']}"
)

print(
    f"Direction correct: "
    f"{outcome['direction_correct']}"
)

print(
    f"Volatility error: "
    f"{outcome['volatility_error']}"
)

if not outcome[
    "outcome_recorded"
]:

    raise RuntimeError(
        "Outcome was not recorded."
    )


# ============================================================
# TEST 5 - STATISTICS
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - TRACKER STATISTICS")
print("=" * 70)

stats = tracker.statistics()

for key, value in stats.items():

    print(
        f"{key}: {value}"
    )

if stats[
    "resolved_predictions"
] < 1:

    raise RuntimeError(
        "Resolved prediction count is incorrect."
    )

if stats[
    "direction_accuracy"
] is None:

    raise RuntimeError(
        "Direction accuracy was not calculated."
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("PREDICTION TRACKER TEST PASSED")
print("=" * 70)