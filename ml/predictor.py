import os
import joblib
import numpy as np
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "models",
    "nifty_direction_model.pkl"
)


class TradingMLPredictor:

    def __init__(self):

        if not os.path.exists(MODEL_FILE):
            raise FileNotFoundError(
                "ML model not found. "
                "Run ml/train_model.py first."
            )

        package = joblib.load(
            MODEL_FILE
        )

        self.model = package["model"]
        self.features = package["features"]


    def predict(self, features):

        X = pd.DataFrame(
            [features]
        )

        X = X[
            self.features
        ]

        prediction = self.model.predict(X)[0]

        probabilities = (
            self.model.predict_proba(X)[0]
        )

        classes = self.model.classes_

        probability_map = {
            int(cls): float(prob)
            for cls, prob
            in zip(
                classes,
                probabilities
            )
        }

        bullish = (
            probability_map.get(
                1,
                0
            )
        )

        bearish = (
            probability_map.get(
                -1,
                0
            )
        )

        neutral = (
            probability_map.get(
                0,
                0
            )
        )

        if prediction == 1:

            direction = "BULLISH"

            confidence = bullish

        elif prediction == -1:

            direction = "BEARISH"

            confidence = bearish

        else:

            direction = "SIDEWAYS"

            confidence = neutral


        return {
            "direction": direction,

            "confidence": round(
                confidence * 100,
                2
            ),

            "bullish_probability": round(
                bullish * 100,
                2
            ),

            "bearish_probability": round(
                bearish * 100,
                2
            ),

            "sideways_probability": round(
                neutral * 100,
                2
            )
        }