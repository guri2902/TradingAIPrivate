class ProbabilityEngine:

    def calculate(
        self,
        market,
        chain,
        option
    ):

        score = 0
        reasons = []

        # ------------------------
        # Market
        # ------------------------

        score += market["score"]

        reasons.extend(
            market["reasons"]
        )

        # ------------------------
        # Option Chain
        # ------------------------

        score += chain["score"]

        reasons.extend(
            chain["reasons"]
        )

        # ------------------------
        # Individual Option
        # ------------------------

        score += option["score"]

        reasons.extend(
            option["reasons"]
        )

        probability = max(
            0,
            min(100, score)
        )

        if probability >= 75:
            action = "STRONG BUY"

        elif probability >= 60:
            action = "BUY"

        elif probability >= 45:
            action = "WATCH"

        else:
            action = "AVOID"

        return {

            "probability": probability,

            "action": action,

            "score": score,

            "reasons": reasons

        }