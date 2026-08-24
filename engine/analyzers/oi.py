class OIAnalyzer:

    def score(self, strike):

        score = 0

        oi = strike["ce_oi"]

        change = strike["ce_change_oi"]

        if oi > 100000:
            score += 20

        elif oi > 50000:
            score += 15

        elif oi > 20000:
            score += 10

        if change > 50000:
            score += 15

        elif change > 20000:
            score += 10

        elif change > 10000:
            score += 5

        return score