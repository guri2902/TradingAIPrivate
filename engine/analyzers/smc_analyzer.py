import pandas as pd


class SMCAnalyzer:

    def analyze(self, candles):

        high = candles["High"]
        low = candles["Low"]
        close = candles["Close"]

        # ==========================================
        # Swing High / Low
        # ==========================================

        swing_high = float(high.tail(20).max())
        swing_low = float(low.tail(20).min())

        last_close = float(close.iloc[-1])

        # ==========================================
        # Break of Structure
        # ==========================================

        bos = False
        choch = False

        if last_close > swing_high:

            bos = True

        elif last_close < swing_low:

            choch = True

        # ==========================================
        # Order Block
        # ==========================================

        bullish_ob = float(low.tail(10).min())
        bearish_ob = float(high.tail(10).max())

        # ==========================================
        # Fair Value Gap
        # ==========================================

        fvg = None

        if len(candles) >= 3:

            c1_high = high.iloc[-3]
            c3_low = low.iloc[-1]

            if c3_low > c1_high:

                fvg = (
                    round(c1_high, 2),
                    round(c3_low, 2)
                )

        # ==========================================
        # Liquidity
        # ==========================================

        liquidity = []

        if abs(last_close - swing_high) <= 20:

            liquidity.append("Liquidity above High")

        if abs(last_close - swing_low) <= 20:

            liquidity.append("Liquidity below Low")

        # ==========================================
        # Market Structure
        # ==========================================

        if bos:

            structure = "Bullish Breakout"

        elif choch:

            structure = "Bearish Breakdown"

        else:

            structure = "Inside Structure"

        return {

            "structure": structure,

            "bos": bos,

            "choch": choch,

            "swing_high": round(swing_high, 2),

            "swing_low": round(swing_low, 2),

            "bullish_order_block": round(bullish_ob, 2),

            "bearish_order_block": round(bearish_ob, 2),

            "fair_value_gap": fvg,

            "liquidity": liquidity

        }