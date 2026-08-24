class OptionAnalyzer:

    def analyze(self, row):

        score = 0
        reasons = []

        # =========================================
        # Open Interest
        # =========================================

        ce_oi = row["ce_oi"]
        pe_oi = row["pe_oi"]

        oi = max(ce_oi, pe_oi)

        if oi >= 150000:
            score += 20
            reasons.append("Excellent Open Interest")

        elif oi >= 100000:
            score += 16
            reasons.append("Strong Open Interest")

        elif oi >= 50000:
            score += 10
            reasons.append("Good Open Interest")

        else:
            score += 3
            reasons.append("Low Open Interest")

        # =========================================
        # Change In OI
        # =========================================

        ce_change = row["ce_change_oi"]
        pe_change = row["pe_change_oi"]

        change = max(ce_change, pe_change)

        if change >= 25000:
            score += 20
            reasons.append("Aggressive OI Build-up")

        elif change >= 10000:
            score += 15
            reasons.append("Fresh OI Build-up")

        elif change >= 3000:
            score += 8
            reasons.append("OI Increasing")

        # =========================================
        # Volume
        # =========================================

        ce_volume = row["ce_volume"]
        pe_volume = row["pe_volume"]

        volume = max(ce_volume, pe_volume)

        if volume >= 500000:
            score += 20
            reasons.append("Exceptional Volume")

        elif volume >= 200000:
            score += 16
            reasons.append("Very High Volume")

        elif volume >= 100000:
            score += 12
            reasons.append("High Volume")

        elif volume >= 30000:
            score += 8
            reasons.append("Good Volume")

        # =========================================
        # IV
        # =========================================

        ce_iv = row["ce_iv"]
        pe_iv = row["pe_iv"]

        iv = max(ce_iv, pe_iv)

        if 10 <= iv <= 20:
            score += 15
            reasons.append("Excellent IV")

        elif 20 < iv <= 30:
            score += 12
            reasons.append("Healthy IV")

        elif 30 < iv <= 40:
            score += 8
            reasons.append("Acceptable IV")

        else:
            reasons.append("High IV Risk")

        # =========================================
        # Premium
        # =========================================

        ce_price = row["ce_ltp"]
        pe_price = row["pe_ltp"]

        premium = max(ce_price, pe_price)

        if 80 <= premium <= 250:
            score += 15
            reasons.append("Ideal Premium")

        elif 40 <= premium <= 350:
            score += 10
            reasons.append("Tradable Premium")

        else:
            reasons.append("Premium Less Suitable")

        # =========================================
        # Liquidity
        # =========================================

        liquidity = oi + volume

        if liquidity >= 600000:
            score += 10
            reasons.append("Excellent Liquidity")

        elif liquidity >= 300000:
            score += 7
            reasons.append("Good Liquidity")

        else:
            score += 3
            reasons.append("Average Liquidity")

        # =========================================
        # Confidence
        # =========================================

        confidence = min(score, 100)

        # =========================================
        # Rating
        # =========================================

        if confidence >= 90:
            rating = "★★★★★"

        elif confidence >= 80:
            rating = "★★★★☆"

        elif confidence >= 70:
            rating = "★★★☆☆"

        elif confidence >= 60:
            rating = "★★☆☆☆"

        else:
            rating = "★☆☆☆☆"

        # =========================================
        # Return
        # =========================================

        return {

            "strike": row["strike"],

            "score": score,

            "confidence": confidence,

            "rating": rating,

            "ce_ltp": ce_price,
            "pe_ltp": pe_price,

            "ce_oi": ce_oi,
            "pe_oi": pe_oi,

            "ce_volume": ce_volume,
            "pe_volume": pe_volume,

            "ce_iv": ce_iv,
            "pe_iv": pe_iv,

            "reasons": reasons

        }