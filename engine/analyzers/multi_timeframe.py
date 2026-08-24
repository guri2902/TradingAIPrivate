from engine.market_data import MarketData
from engine.analyzers.market_analyzer import MarketAnalyzer


class MultiTimeframeAnalyzer:

    def __init__(self):

        self.market = MarketData()
        self.analyzer = MarketAnalyzer()

    def analyze(self):

        timeframes = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h"
        }

        frames = {}

        bull = 0
        bear = 0
        sideways = 0

        for name, interval in timeframes.items():

            try:

                candles = self.market.get_nifty_candles(
                    interval=interval
                )

                if candles is None or candles.empty:
                    continue

                data = self.analyzer.analyze(candles)

                frames[name] = data

                trend = data.get("trend", "Sideways")

                if trend == "Bullish":
                    bull += 1

                elif trend == "Bearish":
                    bear += 1

                else:
                    sideways += 1

            except Exception as e:

                print(e)

                frames[name] = None

        # ============================================
        # Overall Trend
        # ============================================

        if bull > bear and bull > sideways:

            overall = "Bullish"

        elif bear > bull and bear > sideways:

            overall = "Bearish"

        else:

            overall = "Sideways"

        total = bull + bear + sideways

        if total == 0:

            confidence = 0

        else:

            confidence = round(
                max(bull, bear, sideways) / total * 100,
                2
            )

        return {

            "overall": overall,

            "confidence": confidence,

            "bull": bull,

            "bear": bear,

            "sideways": sideways,

            "frames": frames

        }