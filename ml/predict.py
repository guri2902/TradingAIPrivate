# ============================================================
# TradingAI - NIFTY ML PREDICTOR
# ============================================================

import os

import joblib
import numpy as np
import pandas as pd

from feature_engine import create_features


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
            "prediction": "UNKNOWN",
            "up_probability": 0.0,
            "down_probability": 0.0,
            "neutral_probability": 0.0,
            "confidence": 0.0,
        }


    # --------------------------------------------------------
    # Create same features used during training
    # --------------------------------------------------------

    data = create_features(
        df
    )


    data = data.replace(
        [np.inf, -np.inf],
        np.nan
    )


    valid = (
        data
        .dropna(
            subset=features
        )
    )


    if valid.empty:

        return {
            "prediction": "UNKNOWN",
            "up_probability": 0.0,
            "down_probability": 0.0,
            "neutral_probability": 0.0,
            "confidence": 0.0,
        }


    latest = valid.iloc[-1]


    X = pd.DataFrame(
        [latest[features]]
    )


    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    probabilities = (
        model
        .predict_proba(X)[0]
    )

    classes = model.classes_


    result = {

        "BEARISH": 0.0,

        "SIDEWAYS": 0.0,

        "BULLISH": 0.0,

    }


    # IMPORTANT:
    #
    # Training classes:
    #
    # -1 = BEARISH
    #  0 = SIDEWAYS
    #  1 = BULLISH
    #

    for cls, probability in zip(
        classes,
        probabilities
    ):

        probability = float(
            probability
        )

        if cls == -1:

            result["BEARISH"] = probability

        elif cls == 0:

            result["SIDEWAYS"] = probability

        elif cls == 1:

            result["BULLISH"] = probability


    prediction = max(
        result,
        key=result.get
    )


    confidence = result[
        prediction
    ]


    # --------------------------------------------------------
    # Dashboard-friendly response
    # --------------------------------------------------------

    return {

        "prediction": prediction,

        "up_probability": result[
            "BULLISH"
        ],

        "down_probability": result[
            "BEARISH"
        ],

        "neutral_probability": result[
            "SIDEWAYS"
        ],

        "confidence": confidence,

    }