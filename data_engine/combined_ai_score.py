# ============================================================
# TradingAI - COMBINED AI SCORE
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.direction_model import DirectionModel
from data_engine.regime_model import RegimeModel
from data_engine.volatility_model import VolatilityModel


class CombinedAIScore:

    def __init__(
        self,
        model_dir="market_data/models",
    ):

        self.model_dir = Path(model_dir)

        self.weights = {
            "direction": 0.40,
            "regime": 0.30,
            "volatility": 0.30,
        }

        # Direction / Regime accept model_dir
        self.direction_model = DirectionModel(
            model_dir=self.model_dir
        )

        self.regime_model = RegimeModel(
            model_dir=self.model_dir
        )

        # VolatilityModel uses its own default model directory
        self.volatility_model = VolatilityModel()

    # ========================================================
    # LOAD
    # ========================================================

    def load(self):

        print(
            "[COMBINED] Loading AI models..."
        )

        self.direction_model.load()
        self.regime_model.load()
        self.volatility_model.load()

        print(
            "[COMBINED] All models loaded."
        )

        return self

    # ========================================================
    # CLIP
    # ========================================================

    @staticmethod
    def _clip(
        value,
        low=0.0,
        high=1.0,
    ):

        return max(
            low,
            min(
                high,
                float(value)
            )
        )

    # ========================================================
    # DIRECTION SCORE
    # ========================================================

    @staticmethod
    def _direction_score(
        up_probability,
        down_probability,
    ):

        return float(
            float(up_probability)
            - float(down_probability)
        )

    # ========================================================
    # REGIME SCORE
    # ========================================================

    @staticmethod
    def _regime_score(
        bear_probability,
        sideways_probability,
        bull_probability,
    ):

        return float(
            (-1.0 * float(bear_probability))
            + (1.0 * float(bull_probability))
        )

    # ========================================================
    # VOLATILITY MODIFIER
    # ========================================================

    @staticmethod
    def _volatility_modifier(
        low_probability,
        normal_probability,
        high_probability,
    ):

        return float(
            (0.20 * float(low_probability))
            + (0.00 * float(normal_probability))
            + (-0.30 * float(high_probability))
        )

    # ========================================================
    # CALCULATE
    # ========================================================

    def calculate(
        self,
        df,
    ):

        if df is None or df.empty:

            raise ValueError(
                "Input dataframe is empty."
            )

        direction = (
            self.direction_model.predict(df)
        )

        regime = (
            self.regime_model.predict(df)
        )

        volatility = (
            self.volatility_model.predict(df)
        )

        results = []

        for index in range(len(df)):

            direction_row = direction.iloc[index]
            regime_row = regime.iloc[index]
            volatility_row = volatility.iloc[index]

            # ------------------------------------------------
            # COMPONENT SCORES
            # ------------------------------------------------

            direction_score = (
                self._direction_score(
                    up_probability=direction_row[
                        "up_probability"
                    ],
                    down_probability=direction_row[
                        "down_probability"
                    ],
                )
            )

            regime_score = (
                self._regime_score(
                    bear_probability=regime_row[
                        "bear_probability"
                    ],
                    sideways_probability=regime_row[
                        "sideways_probability"
                    ],
                    bull_probability=regime_row[
                        "bull_probability"
                    ],
                )
            )

            volatility_modifier = (
                self._volatility_modifier(
                    low_probability=volatility_row[
                        "low_probability"
                    ],
                    normal_probability=volatility_row[
                        "normal_probability"
                    ],
                    high_probability=volatility_row[
                        "high_probability"
                    ],
                )
            )

            # ------------------------------------------------
            # COMBINED DIRECTIONAL SCORE
            #
            # Range: -1 → +1
            # ------------------------------------------------

            combined_score = (
                self.weights["direction"]
                * direction_score
            ) + (
                self.weights["regime"]
                * regime_score
            ) + (
                self.weights["volatility"]
                * volatility_modifier
            )

            combined_score = max(
                -1.0,
                min(
                    1.0,
                    float(combined_score)
                )
            )

            # ------------------------------------------------
            # CONFIDENCE
            # ------------------------------------------------

            direction_confidence = max(
                float(
                    direction_row[
                        "up_probability"
                    ]
                ),
                float(
                    direction_row[
                        "down_probability"
                    ]
                ),
            )

            regime_confidence = float(
                regime_row[
                    "confidence"
                ]
            )

            volatility_confidence = float(
                volatility_row[
                    "confidence"
                ]
            )

            confidence = (
                self.weights["direction"]
                * direction_confidence
            ) + (
                self.weights["regime"]
                * regime_confidence
            ) + (
                self.weights["volatility"]
                * volatility_confidence
            )

            confidence = self._clip(
                confidence
            )

            # ------------------------------------------------
            # SIGNAL
            # ------------------------------------------------

            if combined_score >= 0.20:

                signal = "BULLISH"

            elif combined_score <= -0.20:

                signal = "BEARISH"

            else:

                signal = "NEUTRAL"

            # ------------------------------------------------
            # STRENGTH
            # ------------------------------------------------

            magnitude = abs(
                combined_score
            )

            if magnitude >= 0.60:

                strength = "STRONG"

            elif magnitude >= 0.35:

                strength = "MODERATE"

            elif magnitude >= 0.20:

                strength = "WEAK"

            else:

                strength = "NONE"

            # ------------------------------------------------
            # TRADE SUITABILITY
            # ------------------------------------------------

            if (
                signal != "NEUTRAL"
                and confidence >= 0.65
            ):

                trade_suitability = "FAVORABLE"

            elif (
                signal != "NEUTRAL"
                and confidence >= 0.50
            ):

                trade_suitability = "CAUTION"

            else:

                trade_suitability = "AVOID"

            results.append({

                "direction_prediction":
                    direction_row[
                        "prediction"
                    ],

                "up_probability":
                    float(
                        direction_row[
                            "up_probability"
                        ]
                    ),

                "down_probability":
                    float(
                        direction_row[
                            "down_probability"
                        ]
                    ),

                "regime_prediction":
                    regime_row[
                        "regime_prediction"
                    ],

                "bear_probability":
                    float(
                        regime_row[
                            "bear_probability"
                        ]
                    ),

                "sideways_probability":
                    float(
                        regime_row[
                            "sideways_probability"
                        ]
                    ),

                "bull_probability":
                    float(
                        regime_row[
                            "bull_probability"
                        ]
                    ),

                "predicted_volatility":
                    float(
                        volatility_row[
                            "predicted_volatility"
                        ]
                    ),

                "volatility_regime":
                    volatility_row[
                        "volatility_regime"
                    ],

                "direction_score":
                    direction_score,

                "regime_score":
                    regime_score,

                "volatility_modifier":
                    volatility_modifier,

                "combined_score":
                    combined_score,

                "direction_confidence":
                    direction_confidence,

                "regime_confidence":
                    regime_confidence,

                "volatility_confidence":
                    volatility_confidence,

                "confidence":
                    confidence,

                "signal":
                    signal,

                "strength":
                    strength,

                "trade_suitability":
                    trade_suitability,
            })

        return pd.DataFrame(results)

    # ========================================================
    # PREDICT
    # ========================================================

    def predict(
        self,
        df,
    ):

        return self.calculate(df)