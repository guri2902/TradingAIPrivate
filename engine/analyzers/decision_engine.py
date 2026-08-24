class DecisionEngine:

    def analyze(self, option):

        score = 0
        reasons = []

        # -----------------------------
        # Open Interest
        # -----------------------------

        if option["ce_oi"] > 50000:
            score += 20
            reasons.append("Strong Open Interest")

        # -----------------------------
        # Volume
        # -----------------------------

        if option["ce_volume"] > 100000:
            score += 20
            reasons.append("High Volume")

        # -----------------------------
        # IV
        # -----------------------------

        iv = option["ce_iv"]

        if 10 <= iv <= 20:
            score += 15
            reasons.append("Healthy IV")

        elif iv < 10:
            score += 5

        else:
            score -= 5

        # -----------------------------
        # OI Change
        # -----------------------------

        if option["ce_change_oi"] > 10000:
            score += 20
            reasons.append("Fresh OI Build-up")

        # -----------------------------
        # Premium
        # -----------------------------

        premium = option["ce_ltp"]

        if 50 <= premium <= 200:
            score += 15
            reasons.append("Tradable Premium")

        # -----------------------------
        # Final Confidence
        # -----------------------------

        confidence = min(score, 100)

        return {

            "strike": option["strike"],

            "premium": premium,

            "score": confidence,

            "confidence": confidence,

            "reasons": reasons

        }