class PatternAnalyzer:

    def analyze(self, candles):

        o = candles["Open"].iloc[-1]
        h = candles["High"].iloc[-1]
        l = candles["Low"].iloc[-1]
        c = candles["Close"].iloc[-1]

        po = candles["Open"].iloc[-2]
        pc = candles["Close"].iloc[-2]

        body = abs(c - o)
        upper = h - max(c, o)
        lower = min(c, o) - l

        patterns = []
        score = 0

        # ==========================================
        # Doji
        # ==========================================

        if body <= (h - l) * 0.1:

            patterns.append("Doji")
            score += 5

        # ==========================================
        # Hammer
        # ==========================================

        if lower > body * 2 and upper < body:

            patterns.append("Hammer")
            score += 15

        # ==========================================
        # Shooting Star
        # ==========================================

        if upper > body * 2 and lower < body:

            patterns.append("Shooting Star")
            score += 15

        # ==========================================
        # Bullish Engulfing
        # ==========================================

        if pc < po and c > o:

            if c > po and o < pc:

                patterns.append("Bullish Engulfing")
                score += 20

        # ==========================================
        # Bearish Engulfing
        # ==========================================

        if pc > po and c < o:

            if o > pc and c < po:

                patterns.append("Bearish Engulfing")
                score += 20

        # ==========================================
        # Marubozu
        # ==========================================

        if body >= (h - l) * 0.9:

            if c > o:

                patterns.append("Bullish Marubozu")
                score += 20

            else:

                patterns.append("Bearish Marubozu")
                score += 20

        confidence = min(score, 100)

        return {

            "patterns": patterns,

            "confidence": confidence

        }