class MarketIndicators:

    def analyze(self, latest, previous):

        momentum = round(latest - previous, 2)

        if momentum > 0:
            trend = "Bullish"

        elif momentum < 0:
            trend = "Bearish"

        else:
            trend = "Sideways"

        strength = min(
            100,
            int(abs(momentum) * 10)
        )

        volatility = round(abs(momentum), 2)

        return {

            "price": latest,

            "trend": trend,

            "momentum": momentum,

            "strength": strength,

            "volatility": volatility,

            "volume": 0

        }