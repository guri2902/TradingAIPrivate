class VolumeAnalyzer:

    def score(self, strike):

        score = 0

        volume = strike["ce_volume"]

        if volume > 500000:
            score += 25

        elif volume > 200000:
            score += 18

        elif volume > 100000:
            score += 12

        elif volume > 50000:
            score += 8

        else:
            score += 2

        return score