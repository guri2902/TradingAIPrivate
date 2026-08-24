import pandas as pd


class BacktestData:

    def __init__(self, csv_path):

        self.csv_path = csv_path
        self.data = None

    # ==================================================
    # LOAD DATA
    # ==================================================

    def load(self):

        self.data = pd.read_csv(
            self.csv_path,
            parse_dates=["Datetime"]
        )

        self.data.sort_values(
            "Datetime",
            inplace=True
        )

        self.data.reset_index(
            drop=True,
            inplace=True
        )

        return self.data

    # ==================================================
    # GET DATA UP TO TIME
    # ==================================================

    def candles_until(self, timestamp):

        if self.data is None:
            self.load()

        timestamp = pd.Timestamp(timestamp)

        return self.data[
            self.data["Datetime"] <= timestamp
        ].copy()

    # ==================================================
    # GET CURRENT CANDLE
    # ==================================================

    def candle_at(self, index):

        return self.data.iloc[index]

    # ==================================================
    # RANGE
    # ==================================================

    def get_range(self, start, end):

        if self.data is None:
            self.load()

        start = pd.Timestamp(start)
        end = pd.Timestamp(end)

        return self.data[
            (self.data["Datetime"] >= start) &
            (self.data["Datetime"] <= end)
        ].copy()