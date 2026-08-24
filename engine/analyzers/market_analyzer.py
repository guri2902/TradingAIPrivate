import pandas as pd


class MarketAnalyzer:

    def analyze(self, candles):

        close = candles["Close"]
        high = candles["High"]
        low = candles["Low"]

        volume = candles["Volume"] if "Volume" in candles.columns else None

        # ==================================================
        # EMA
        # ==================================================

        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()

        # ==================================================
        # RSI
        # ==================================================

        delta = close.diff()

        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        # ==================================================
        # MACD
        # ==================================================

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()

        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal

        # ==================================================
        # ATR
        # ==================================================

        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(14).mean()

        # ==================================================
        # VWAP
        # ==================================================

        if volume is not None:

            typical = (high + low + close) / 3

            vwap = (typical * volume).cumsum() / volume.cumsum()

            current_volume = int(volume.iloc[-1])

            volume_sma20 = volume.rolling(20).mean()

        else:

            vwap = close.expanding().mean()

            current_volume = 0

            volume_sma20 = pd.Series([0] * len(close), index=close.index)

        # ==================================================
        # Bollinger Bands
        # ==================================================

        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()

        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)

        # ==================================================
        # Volatility
        # ==================================================

        volatility = close.pct_change().rolling(20).std() * 100

        # ==================================================
        # Trend
        # ==================================================

        latest = close.iloc[-1]

        if (
            ema20.iloc[-1] > ema50.iloc[-1]
            and ema50.iloc[-1] > ema200.iloc[-1]
            and latest > vwap.iloc[-1]
        ):

            trend = "Bullish"

        elif (
            ema20.iloc[-1] < ema50.iloc[-1]
            and ema50.iloc[-1] < ema200.iloc[-1]
            and latest < vwap.iloc[-1]
        ):

            trend = "Bearish"

        else:

            trend = "Sideways"

        # ==================================================
        # Momentum
        # ==================================================

        momentum = latest - close.iloc[-2]

        # ==================================================
        # Trend Strength
        # ==================================================

        strength = abs(ema20.iloc[-1] - ema50.iloc[-1])

        strength = min((strength / latest) * 1000, 100)

        # ==================================================
        # Bullish Score
        # ==================================================

        bull_score = 0
        bear_score = 0

        if ema20.iloc[-1] > ema50.iloc[-1]:
            bull_score += 20
        else:
            bear_score += 20

        if ema50.iloc[-1] > ema200.iloc[-1]:
            bull_score += 20
        else:
            bear_score += 20

        if latest > vwap.iloc[-1]:
            bull_score += 15
        else:
            bear_score += 15

        if macd.iloc[-1] > signal.iloc[-1]:
            bull_score += 15
        else:
            bear_score += 15

        if rsi.iloc[-1] > 55:
            bull_score += 10

        elif rsi.iloc[-1] < 45:
            bear_score += 10

        if momentum > 0:
            bull_score += 10
        else:
            bear_score += 10

        if volume is not None:

            if current_volume > volume_sma20.iloc[-1]:
                bull_score += 10

        bull_probability = round((bull_score / 100) * 100, 2)
        bear_probability = round((bear_score / 100) * 100, 2)

        sideways_probability = max(
            0,
            round(100 - bull_probability - bear_probability, 2)
        )

        # ==================================================
        # Result
        # ==================================================

        return {

            "price": round(float(latest), 2),

            "trend": trend,

            "strength": round(strength, 2),

            "momentum": round(momentum, 2),

            "volatility": round(float(volatility.iloc[-1]), 2),

            "volume": current_volume,

            "ema20": round(float(ema20.iloc[-1]), 2),

            "ema50": round(float(ema50.iloc[-1]), 2),

            "ema200": round(float(ema200.iloc[-1]), 2),

            "rsi": round(float(rsi.iloc[-1]), 2),

            "atr": round(float(atr.iloc[-1]), 2),

            "vwap": round(float(vwap.iloc[-1]), 2),

            "macd": round(float(macd.iloc[-1]), 2),

            "signal": round(float(signal.iloc[-1]), 2),

            "histogram": round(float(histogram.iloc[-1]), 2),

            "bb_upper": round(float(upper_band.iloc[-1]), 2),

            "bb_lower": round(float(lower_band.iloc[-1]), 2),

            "bull_probability": bull_probability,

            "bear_probability": bear_probability,

            "sideways_probability": sideways_probability

        }