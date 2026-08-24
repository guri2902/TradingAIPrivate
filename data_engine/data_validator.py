# ============================================================
# TradingAI - MARKET DATA VALIDATOR
# ============================================================

from pathlib import Path
import pandas as pd


class DataValidationError(Exception):
    """Raised when market data fails validation."""
    pass


class MarketDataValidator:

    # ========================================================
    # STOCK / INDEX VALIDATION
    # ========================================================

    @staticmethod
    def validate_ohlcv(
        df,
        symbol=None,
        strict=False
    ):
        errors = []
        warnings = []

        if df is None or df.empty:
            errors.append("DataFrame is empty.")
            return MarketDataValidator._result(
                errors,
                warnings,
                strict
            )

        required = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:
            errors.append(
                f"Missing required columns: {missing}"
            )
            return MarketDataValidator._result(
                errors,
                warnings,
                strict
            )

        data = df.copy()

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        data["timestamp"] = pd.to_datetime(
            data["timestamp"],
            errors="coerce"
        )

        invalid_timestamps = data["timestamp"].isna().sum()

        if invalid_timestamps:
            errors.append(
                f"Invalid timestamps: {invalid_timestamps}"
            )

        # ----------------------------------------------------
        # NUMERIC COLUMNS
        # ----------------------------------------------------

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        for column in numeric_columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

            invalid = data[column].isna().sum()

            if invalid:
                errors.append(
                    f"{column}: {invalid} invalid/missing values"
                )

        # ----------------------------------------------------
        # NEGATIVE VALUES
        # ----------------------------------------------------

        for column in [
            "open",
            "high",
            "low",
            "close",
        ]:

            if (data[column] < 0).any():

                errors.append(
                    f"{column}: negative prices detected"
                )

        if (data["volume"] < 0).any():

            errors.append(
                "volume: negative values detected"
            )

        # ----------------------------------------------------
        # OHLC LOGIC
        # ----------------------------------------------------

        invalid_high = (
            data["high"]
            < data[["open", "close", "low"]].max(axis=1)
        )

        invalid_low = (
            data["low"]
            > data[["open", "close", "high"]].min(axis=1)
        )

        if invalid_high.any():

            errors.append(
                f"Invalid OHLC high values: "
                f"{invalid_high.sum()} rows"
            )

        if invalid_low.any():

            errors.append(
                f"Invalid OHLC low values: "
                f"{invalid_low.sum()} rows"
            )

        # ----------------------------------------------------
        # DUPLICATES
        # ----------------------------------------------------

        duplicate_timestamps = data.duplicated(
            subset=["timestamp"]
        ).sum()

        if duplicate_timestamps:

            warnings.append(
                f"Duplicate timestamps: "
                f"{duplicate_timestamps}"
            )

        # ----------------------------------------------------
        # SORT ORDER
        # ----------------------------------------------------

        if not data["timestamp"].is_monotonic_increasing:

            warnings.append(
                "Data is not sorted chronologically."
            )

        # ----------------------------------------------------
        # SYMBOL
        # ----------------------------------------------------

        if symbol is not None and "symbol" in data.columns:

            symbols = (
                data["symbol"]
                .dropna()
                .astype(str)
                .str.upper()
                .unique()
            )

            expected = str(symbol).upper()

            unexpected = [
                value
                for value in symbols
                if value != expected
            ]

            if unexpected:

                errors.append(
                    f"Unexpected symbols: {unexpected}"
                )

        return MarketDataValidator._result(
            errors,
            warnings,
            strict
        )

    # ========================================================
    # OPTION CHAIN VALIDATION
    # ========================================================

    @staticmethod
    def validate_option_chain(
        df,
        symbol=None,
        strict=False
    ):
        errors = []
        warnings = []

        if df is None or df.empty:

            errors.append(
                "Option chain is empty."
            )

            return MarketDataValidator._result(
                errors,
                warnings,
                strict
            )

        required = [
            "timestamp",
            "symbol",
            "expiry",
            "strike",
            "option_type",
            "last_price",
            "volume",
            "oi",
            "oi_change",
            "iv",
            "bid_price",
            "ask_price",
            "bid_quantity",
            "ask_quantity",
            "total_buy_quantity",
            "total_sell_quantity",
            "underlying_value",
        ]

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:

            errors.append(
                f"Missing option columns: {missing}"
            )

            return MarketDataValidator._result(
                errors,
                warnings,
                strict
            )

        data = df.copy()

        # ----------------------------------------------------
        # TIMESTAMP / EXPIRY
        # ----------------------------------------------------

        data["timestamp"] = pd.to_datetime(
            data["timestamp"],
            errors="coerce"
        )

        data["expiry"] = pd.to_datetime(
            data["expiry"],
            errors="coerce"
        )

        if data["timestamp"].isna().any():

            errors.append(
                "Invalid option-chain timestamps."
            )

        if data["expiry"].isna().any():

            errors.append(
                "Invalid option expiry values."
            )

        # ----------------------------------------------------
        # OPTION TYPE
        # ----------------------------------------------------

        option_types = set(
            data["option_type"]
            .dropna()
            .astype(str)
            .str.upper()
        )

        invalid_types = option_types - {"CE", "PE"}

        if invalid_types:

            errors.append(
                f"Invalid option types: {invalid_types}"
            )

        # ----------------------------------------------------
        # NUMERIC COLUMNS
        # ----------------------------------------------------

        numeric_columns = [
            "strike",
            "last_price",
            "volume",
            "oi",
            "oi_change",
            "iv",
            "bid_price",
            "ask_price",
            "bid_quantity",
            "ask_quantity",
            "total_buy_quantity",
            "total_sell_quantity",
            "underlying_value",
        ]

        for column in numeric_columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

            invalid = data[column].isna().sum()

            if invalid:

                errors.append(
                    f"{column}: "
                    f"{invalid} invalid/missing values"
                )

        # ----------------------------------------------------
        # NEGATIVE VALUES
        # ----------------------------------------------------

        non_negative = [
            "strike",
            "last_price",
            "volume",
            "oi",
            "iv",
            "bid_price",
            "ask_price",
            "bid_quantity",
            "ask_quantity",
            "total_buy_quantity",
            "total_sell_quantity",
            "underlying_value",
        ]

        for column in non_negative:

            if (data[column] < 0).any():

                errors.append(
                    f"{column}: negative values detected"
                )

        # ----------------------------------------------------
        # BID / ASK
        # ----------------------------------------------------

        valid_bid_ask = (
            data["bid_price"].notna()
            & data["ask_price"].notna()
        )

        invalid_spread = (
            valid_bid_ask
            & (data["bid_price"] > data["ask_price"])
        )

        if invalid_spread.any():

            errors.append(
                f"Bid price greater than ask price: "
                f"{invalid_spread.sum()} rows"
            )

        # ----------------------------------------------------
        # CE / PE BALANCE
        # ----------------------------------------------------

        ce_count = (
            data["option_type"]
            .astype(str)
            .str.upper()
            .eq("CE")
            .sum()
        )

        pe_count = (
            data["option_type"]
            .astype(str)
            .str.upper()
            .eq("PE")
            .sum()
        )

        if ce_count == 0:

            errors.append(
                "No CE contracts found."
            )

        if pe_count == 0:

            errors.append(
                "No PE contracts found."
            )

        if ce_count != pe_count:

            warnings.append(
                f"CE/PE count mismatch: "
                f"CE={ce_count}, PE={pe_count}"
            )

        # ----------------------------------------------------
        # DUPLICATE CONTRACTS
        # ----------------------------------------------------

        duplicate_contracts = data.duplicated(
            subset=[
                "expiry",
                "strike",
                "option_type",
            ]
        ).sum()

        if duplicate_contracts:

            errors.append(
                f"Duplicate option contracts: "
                f"{duplicate_contracts}"
            )

        # ----------------------------------------------------
        # SYMBOL
        # ----------------------------------------------------

        if symbol is not None:

            expected = str(symbol).upper()

            actual = (
                data["symbol"]
                .dropna()
                .astype(str)
                .str.upper()
                .unique()
            )

            unexpected = [
                value
                for value in actual
                if value != expected
            ]

            if unexpected:

                errors.append(
                    f"Unexpected symbols: {unexpected}"
                )

        return MarketDataValidator._result(
            errors,
            warnings,
            strict
        )

    # ========================================================
    # RESULT
    # ========================================================

    @staticmethod
    def _result(
        errors,
        warnings,
        strict
    ):

        valid = len(errors) == 0

        result = {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
        }

        if strict and not valid:

            raise DataValidationError(
                "\n".join(errors)
            )

        return result