class AIScore:

    @staticmethod
    def calculate(data):

        bull = 0
        bear = 0
        reasons = []

        # ---------------- EMA ----------------

        if data["ema20"] > data["ema50"] > data["ema200"]:
            bull += 15
            reasons.append("EMA Bullish Alignment")

        elif data["ema20"] < data["ema50"] < data["ema200"]:
            bear += 15
            reasons.append("EMA Bearish Alignment")

        # ---------------- RSI ----------------

        rsi = data["rsi"]

        if rsi > 60:
            bull += 10
            reasons.append("Strong RSI")

        elif rsi < 40:
            bear += 10
            reasons.append("Weak RSI")

        # ---------------- MACD ----------------

        if data["macd"] > data["signal"]:
            bull += 10
            reasons.append("MACD Bullish")

        else:
            bear += 10
            reasons.append("MACD Bearish")

        # ---------------- PCR ----------------

        pcr = data["pcr"]

        if pcr > 1:
            bull += 15
            reasons.append("Bullish PCR")

        elif pcr < 0.9:
            bear += 15
            reasons.append("Bearish PCR")

        # ---------------- Trend ----------------

        if data["trend"] == "Bullish":
            bull += 10

        elif data["trend"] == "Bearish":
            bear += 10

        # ---------------- Option Chain ----------------

        if data["oi_bias"] == "Bullish":
            bull += 15

        elif data["oi_bias"] == "Bearish":
            bear += 15

        # ---------------- Multi TF ----------------

        if data["mtf"] == "Bullish":
            bull += 20

        elif data["mtf"] == "Bearish":
            bear += 20

        total = bull + bear

        if total == 0:
            confidence = 50
        else:
            confidence = round(max(bull, bear) / total * 100)

        if bull > bear:

            bias = "Bullish"

        elif bear > bull:

            bias = "Bearish"

        else:

            bias = "Sideways"

        return {

            "bull": bull,

            "bear": bear,

            "bias": bias,

            "confidence": confidence,

            "reasons": reasons

        }