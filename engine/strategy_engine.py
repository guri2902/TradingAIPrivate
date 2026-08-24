import math


class StrategyEngine:

    def analyse(self, market):

        bull_score = 0
        bear_score = 0
        reasons = []

        # =================================================
        # PRIMARY TREND
        # =================================================

        trend = market.get("trend", "Sideways")

        if trend == "Bullish":
            bull_score += 20
            reasons.append("Primary Trend Bullish")

        elif trend == "Bearish":
            bear_score += 20
            reasons.append("Primary Trend Bearish")

        # =================================================
        # MULTI TIMEFRAME
        # =================================================

        multi = market.get("multi_tf", {})

        bull = multi.get("bull", 0)
        bear = multi.get("bear", 0)

        bull_score += bull * 5
        bear_score += bear * 5

        reasons.append(
            f"Multi TF Bull:{bull} Bear:{bear}"
        )

        confidence = multi.get("confidence", 0)

        if confidence >= 80:

            if bull > bear:

                bull_score += 15
                reasons.append("Strong Bullish Alignment")

            elif bear > bull:

                bear_score += 15
                reasons.append("Strong Bearish Alignment")

        # =================================================
        # EMA ALIGNMENT
        # =================================================

        ema20 = market.get("ema20", 0)
        ema50 = market.get("ema50", 0)
        ema200 = market.get("ema200", 0)

        if ema20 > ema50 > ema200:

            bull_score += 15
            reasons.append("EMA Bullish")

        elif ema20 < ema50 < ema200:

            bear_score += 15
            reasons.append("EMA Bearish")

        # =================================================
        # RSI
        # =================================================

        rsi = market.get("rsi", 50)

        if rsi >= 60:

            bull_score += 10
            reasons.append("RSI Strong")

        elif rsi <= 40:

            bear_score += 10
            reasons.append("RSI Weak")

        # =================================================
        # MOMENTUM
        # =================================================

        momentum = market.get("momentum", 0)

        if momentum > 0:

            bull_score += 10
            reasons.append("Positive Momentum")

        elif momentum < 0:

            bear_score += 10
            reasons.append("Negative Momentum")

        # =================================================
        # MACD
        # =================================================

        macd = market.get("macd", 0)
        signal = market.get("signal", 0)

        if macd > signal:

            bull_score += 15
            reasons.append("MACD Bullish")

        else:

            bear_score += 15
            reasons.append("MACD Bearish")

        # =================================================
        # VWAP
        # =================================================

        vwap = market.get("vwap")
        price = market.get("price", 0)

        if (
            vwap is not None
            and not math.isnan(vwap)
        ):

            if price > vwap:

                bull_score += 10
                reasons.append("Above VWAP")

            else:

                bear_score += 10
                reasons.append("Below VWAP")

        # =================================================
        # MARKET STRENGTH
        # =================================================

        strength = float(
            market.get("strength", 0)
        )

        if trend == "Bullish":

            bull_score += strength * 0.2

        elif trend == "Bearish":

            bear_score += strength * 0.2

        # =================================================
        # FINAL
        # =================================================

        total = bull_score + bear_score

        if total == 0:

            confidence = 0

        else:

            confidence = round(
                max(bull_score, bear_score) / total * 100,
                2
            )

        if bull_score > bear_score:

            direction = "CE"

        elif bear_score > bull_score:

            direction = "PE"

        else:

            direction = "NO TRADE"

        return {

            "direction": direction,

            "confidence": confidence,

            "bull_score": round(
                bull_score,
                2
            ),

            "bear_score": round(
                bear_score,
                2
            ),

            "reasons": reasons

        }