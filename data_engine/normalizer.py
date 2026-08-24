# ============================================================
# TradingAI - MARKET DATA NORMALIZER
# ============================================================

import pandas as pd


class MarketDataNormalizer:

    # ========================================================
    # JUGAAD
    # ========================================================

    @staticmethod
    def from_jugaad(df):

        data = pd.DataFrame()

        data["timestamp"] = pd.to_datetime(
            df["HistoricalDate"],
            errors="coerce"
        )

        data["symbol"] = (
            df["INDEX_NAME"]
            if "INDEX_NAME" in df.columns
            else df.get("Index Name")
        )

        data["open"] = pd.to_numeric(
            df["OPEN"],
            errors="coerce"
        )

        data["high"] = pd.to_numeric(
            df["HIGH"],
            errors="coerce"
        )

        data["low"] = pd.to_numeric(
            df["LOW"],
            errors="coerce"
        )

        data["close"] = pd.to_numeric(
            df["CLOSE"],
            errors="coerce"
        )

        # Jugaad index data doesn't provide these
        data["volume"] = pd.NA
        data["oi"] = pd.NA
        data["total_trades"] = pd.NA
        data["qty_per_trade"] = pd.NA
        data["delivery_qty"] = pd.NA
        data["series"] = pd.NA

        data["source"] = "jugaad"

        return MarketDataNormalizer._finalize(
            data
        )


    # ========================================================
    # EOD2
    # ========================================================

    @staticmethod
    def from_eod2(
        df,
        symbol=None
    ):

        data = pd.DataFrame()

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            data["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

        elif "Date" in df.columns:

            data["timestamp"] = pd.to_datetime(
                df["Date"],
                errors="coerce"
            )

        else:

            raise ValueError(
                "EOD2 data has no Date/timestamp column"
            )


        # ----------------------------------------------------
        # SYMBOL
        # ----------------------------------------------------

        if symbol is not None:

            data["symbol"] = str(symbol).upper()

        elif "SYMBOL" in df.columns:

            data["symbol"] = df["SYMBOL"]

        else:

            data["symbol"] = pd.NA


        # ----------------------------------------------------
        # OHLC
        # ----------------------------------------------------

        for source_col, target_col in [
            ("Open", "open"),
            ("High", "high"),
            ("Low", "low"),
            ("Close", "close"),
        ]:

            if source_col in df.columns:

                data[target_col] = pd.to_numeric(
                    df[source_col],
                    errors="coerce"
                )

            else:

                data[target_col] = pd.NA


        # ----------------------------------------------------
        # VOLUME
        # ----------------------------------------------------

        if "Volume" in df.columns:

            data["volume"] = pd.to_numeric(
                df["Volume"],
                errors="coerce"
            )

        else:

            data["volume"] = pd.NA


        # ----------------------------------------------------
        # OPEN INTEREST
        # ----------------------------------------------------

        if "OI" in df.columns:

            data["oi"] = pd.to_numeric(
                df["OI"],
                errors="coerce"
            )

        else:

            data["oi"] = pd.NA


        # ----------------------------------------------------
        # TOTAL TRADES
        # ----------------------------------------------------

        if "TOTAL_TRADES" in df.columns:

            data["total_trades"] = pd.to_numeric(
                df["TOTAL_TRADES"],
                errors="coerce"
            )

        else:

            data["total_trades"] = pd.NA


        # ----------------------------------------------------
        # QUANTITY PER TRADE
        # ----------------------------------------------------

        if "QTY_PER_TRADE" in df.columns:

            data["qty_per_trade"] = pd.to_numeric(
                df["QTY_PER_TRADE"],
                errors="coerce"
            )

        else:

            data["qty_per_trade"] = pd.NA


        # ----------------------------------------------------
        # DELIVERY QUANTITY
        # ----------------------------------------------------

        if "DLV_QTY" in df.columns:

            data["delivery_qty"] = pd.to_numeric(
                df["DLV_QTY"],
                errors="coerce"
            )

        else:

            data["delivery_qty"] = pd.NA


        # ----------------------------------------------------
        # SERIES
        # ----------------------------------------------------

        if "Series" in df.columns:

            data["series"] = df["Series"]

        else:

            data["series"] = pd.NA


        data["source"] = "eod2"


        return MarketDataNormalizer._finalize(
            data
        )


    # ========================================================
    # FINALIZE
    # ========================================================

    @staticmethod
    def _finalize(data):

        columns = [
            "timestamp",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "oi",
            "total_trades",
            "qty_per_trade",
            "delivery_qty",
            "series",
            "source",
        ]

        for column in columns:

            if column not in data.columns:

                data[column] = pd.NA


        data = data[columns].copy()


        # ----------------------------------------------------
        # CLEAN NUMERIC COLUMNS
        # ----------------------------------------------------

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "oi",
            "total_trades",
            "qty_per_trade",
            "delivery_qty",
        ]

        for column in numeric_columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )


        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        data = (
            data
            .sort_values("timestamp")
            .reset_index(drop=True)
        )


        return data