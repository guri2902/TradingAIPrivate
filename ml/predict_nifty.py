# ============================================================
# TradingAI - NIFTY ML PREDICTOR
# ============================================================

import os
import joblib
import numpy as np
import pandas as pd

from ml.feature_engine import create_features


# ============================================================
# PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "ml_models",
    "nifty_direction_model.pkl"
)


# ============================================================
# LOAD MODEL
# ============================================================

artifact = joblib.load(
    MODEL_FILE
)

model = artifact["model"]

features = artifact["features"]


# ============================================================
# PREDICT
# ============================================================

def predict_nifty(df):

    if df is None or len(df) == 0:
        return {
            "prediction": "NEUTRAL",
            "up_probability": 0.0,
            "down_probability": 0.0,
            "neutral_probability": 0.0,
            "confidence": 0.0,
        }


    data = create_features(
        df.copy()
    )


    data = data.replace(
        [np.inf, -np.inf],
        np.nan
    )


    valid = (
        data
        .dropna(subset=features)
    )


    if valid.empty:

        return {
            "prediction": "NEUTRAL",
            "up_probability": 0.0,
            "down_probability": 0.0,
            "neutral_probability": 0.0,
            "confidence": 0.0,
        }


    latest = valid.iloc[-1]


    X = pd.DataFrame(
        [latest[features]]
    )


    probabilities = (
        model
        .predict_proba(X)[0]
    )

    classes = model.classes_


    result = {
        "DOWN": 0.0,
        "NEUTRAL": 0.0,
        "UP": 0.0
    }


    for cls, probability in zip(
        classes,
        probabilities
    ):

        probability = float(
            probability
        )

        if cls == -1:
            result["DOWN"] = probability

        elif cls == 0:
            result["NEUTRAL"] = probability

        elif cls == 1:
            result["UP"] = probability


    prediction = max(
        result,
        key=result.get
    )


    confidence = result[
        prediction
    ]


    return {

        "prediction": prediction,

        "up_probability":
            result["UP"],

        "down_probability":
            result["DOWN"],

        "neutral_probability":
            result["NEUTRAL"],

        "confidence":
            confidence
    }