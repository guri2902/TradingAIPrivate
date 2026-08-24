class IVAnalyzer:

    def score(self, strike):

        iv = strike["ce_iv"]

        if iv == 0:
            return 0

        if 10 <= iv <= 18:
            return 20

        if 18 < iv <= 25:
            return 15

        if 25 < iv <= 35:
            return 10

        return 5