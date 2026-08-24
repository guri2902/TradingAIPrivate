import pandas as pd


class VolumeProfile:

    def analyze(self, candles):

        if candles is None or candles.empty:
            return {}

        if "Volume" not in candles.columns:
            return {}

        close = candles["Close"]
        volume = candles["Volume"]

        df = pd.DataFrame({
            "price": close.round(0),
            "volume": volume
        })

        profile = (
            df.groupby("price")["volume"]
            .sum()
            .sort_values(ascending=False)
        )

        poc = float(profile.index[0])

        value_area = profile.head(10)

        vah = float(value_area.index.max())
        val = float(value_area.index.min())

        return {

            "poc": poc,

            "vah": vah,

            "val": val,

            "levels": profile.head(15).to_dict()

        }