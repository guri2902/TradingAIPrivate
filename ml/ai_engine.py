from ml.predictor import ml_predictor


class AIEngine:

    def __init__(self):

        self.ml = ml_predictor

    # =====================================================
    # MARKET AI
    # =====================================================

    def analyze_market(
        self,
        candles,
        market=None,
        multi_tf=None,
        chain=None,
        support_resistance=None
    ):

        ml = self.ml.predict(
            candles
        )

        # -------------------------------------------------
        # Base result
        # -------------------------------------------------

        result = {

            "direction": "NEUTRAL",

            "confidence": 0.0,

            "ml": ml,

            "technical_score": 0.0,

            "option_score": 0.0,

            "final_score": 0.0,

            "reasons": [],

            "warnings": []
        }

        if not ml["available"]:

            result["warnings"].append(
                "ML model unavailable."
            )

            return result

        # =================================================
        # ML SCORE
        # =================================================

        ml_score = 0.0

        if ml["direction"] == "UP":

            ml_score = ml["up_probability"]

            result["reasons"].append(
                f"ML favors UP ({ml['up_probability']:.1f}%)."
            )

        elif ml["direction"] == "DOWN":

            ml_score = -ml["down_probability"]

            result["reasons"].append(
                f"ML favors DOWN ({ml['down_probability']:.1f}%)."
            )

        else:

            result["reasons"].append(
                f"ML sees SIDEWAYS conditions "
                f"({ml['sideways_probability']:.1f}%)."
            )

        # =================================================
        # TECHNICAL SCORE
        # =================================================

        technical_score = 0.0

        if market:

            trend = str(
                market.get(
                    "trend",
                    ""
                )
            ).lower()

            signal = str(
                market.get(
                    "signal",
                    ""
                )
            ).lower()

            if (
                "bull" in trend
                or "up" in trend
            ):

                technical_score += 25

                result["reasons"].append(
                    "Technical trend is bullish."
                )

            elif (
                "bear" in trend
                or "down" in trend
            ):

                technical_score -= 25

                result["reasons"].append(
                    "Technical trend is bearish."
                )

            if "bull" in signal:

                technical_score += 15

            elif "bear" in signal:

                technical_score -= 15

        technical_score = max(
            -40,
            min(
                40,
                technical_score
            )
        )

        # =================================================
        # OPTION SCORE
        # =================================================

        option_score = 0.0

        if support_resistance:

            pcr = support_resistance.get(
                "pcr"
            )

            if pcr is not None:

                try:

                    pcr = float(pcr)

                    if pcr > 1.10:

                        option_score += 20

                        result["reasons"].append(
                            f"PCR supports bullish bias ({pcr:.2f})."
                        )

                    elif pcr < 0.90:

                        option_score -= 20

                        result["reasons"].append(
                            f"PCR supports bearish bias ({pcr:.2f})."
                        )

                    else:

                        result["reasons"].append(
                            f"PCR is neutral ({pcr:.2f})."
                        )

                except Exception:

                    pass

        # =================================================
        # FINAL SCORE
        # =================================================

        final_score = (
            ml_score * 0.60
            +
            technical_score
            +
            option_score
        )

        final_score = max(
            -100,
            min(
                100,
                final_score
            )
        )

        # =================================================
        # FINAL DIRECTION
        # =================================================

        if final_score >= 25:

            direction = "BULLISH"

        elif final_score <= -25:

            direction = "BEARISH"

        else:

            direction = "NEUTRAL"

        # =================================================
        # CONFIDENCE
        # =================================================

        confidence = abs(
            final_score
        )

        # Avoid pretending neutral conditions
        # have high directional confidence.

        if direction == "NEUTRAL":

            confidence = min(
                confidence,
                50
            )

        # =================================================
        # CONFLICT DETECTION
        # =================================================

        if (
            ml["direction"] == "UP"
            and direction == "BEARISH"
        ):

            result["warnings"].append(
                "ML and broader market signals conflict."
            )

        if (
            ml["direction"] == "DOWN"
            and direction == "BULLISH"
        ):

            result["warnings"].append(
                "ML and broader market signals conflict."
            )

        if (
            ml["direction"] == "SIDEWAYS"
        ):

            result["warnings"].append(
                "ML does not show strong directional conviction."
            )

        # =================================================
        # RESULT
        # =================================================

        result.update({

            "direction":
                direction,

            "confidence":
                round(
                    confidence,
                    2
                ),

            "technical_score":
                round(
                    technical_score,
                    2
                ),

            "option_score":
                round(
                    option_score,
                    2
                ),

            "final_score":
                round(
                    final_score,
                    2
                )
        })

        return result


# =========================================================
# SINGLETON
# =========================================================

ai_engine = AIEngine()