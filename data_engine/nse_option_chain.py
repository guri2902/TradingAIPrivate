from pathlib import Path
from datetime import datetime
import json

import pandas as pd
from nse import NSE


class NseOptionChain:

    def __init__(
        self,
        output_dir="market_data/raw/nse",
        history_dir="market_data/processed",
    ):
        self.output_dir = Path(output_dir)
        self.history_dir = Path(history_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

        self.nse = NSE(
            download_folder=self.output_dir
        )

    # ========================================================
    # RAW OPTION CHAIN
    # ========================================================

    def get_raw(
        self,
        symbol="NIFTY",
        expiry=None
    ):

        print(
            f"\n[NSE-OPTION] Downloading option chain: {symbol}"
        )

        expiry_date = None

        if expiry:

            if isinstance(expiry, str):

                expiry_date = datetime.strptime(
                    expiry,
                    "%d-%b-%Y"
                )

            elif isinstance(expiry, datetime):

                expiry_date = expiry

            else:

                raise TypeError(
                    "expiry must be a string or datetime"
                )

        data = self.nse.optionChain(
            symbol.lower(),
            expiry_date=expiry_date
        )

        if not isinstance(data, dict):

            raise ValueError(
                "Unexpected NSE option-chain response"
            )

        records = data.get("records", {})

        rows = records.get("data", [])

        expiries = records.get(
            "expiryDates",
            []
        )

        print(
            f"[NSE-OPTION] Rows: {len(rows)}"
        )

        print(
            f"[NSE-OPTION] Expiries: {len(expiries)}"
        )

        if expiries:

            print(
                f"[NSE-OPTION] Nearest expiry: "
                f"{expiries[0]}"
            )

        return data

    # ========================================================
    # EXPIRY NORMALIZER
    # ========================================================

    @staticmethod
    def _normalize_expiry(value):

        if value is None:
            return None

        # ----------------------------------------------------
        # List / tuple
        # ----------------------------------------------------

        if isinstance(value, (list, tuple)):

            if not value:
                return None

            value = value[0]

        # ----------------------------------------------------
        # Timestamp / datetime
        # ----------------------------------------------------

        if isinstance(
            value,
            (pd.Timestamp, datetime)
        ):

            return pd.Timestamp(value)

        # ----------------------------------------------------
        # String
        # ----------------------------------------------------

        value = str(value).strip()

        if not value:
            return None

        # NSE format: 25-Aug-2026
        parsed = pd.to_datetime(
            value,
            format="%d-%b-%Y",
            errors="coerce"
        )

        if pd.notna(parsed):
            return parsed

        # Other possible formats
        parsed = pd.to_datetime(
            value,
            errors="coerce"
        )

        if pd.notna(parsed):
            return parsed

        return None

    # ========================================================
    # NORMALIZE
    # ========================================================

    def normalize(
        self,
        data,
        symbol="NIFTY"
    ):

        if not isinstance(data, dict):

            raise ValueError(
                "Option-chain data must be a dictionary"
            )

        records = data.get(
            "records",
            {}
        )

        rows = records.get(
            "data",
            []
        )

        available_expiries = records.get(
            "expiryDates",
            []
        )

        if not rows:

            return pd.DataFrame()

        # ----------------------------------------------------
        # IMPORTANT
        #
        # The NSE response contains expiry information in the
        # individual CE/PE records. Use that first.
        #
        # If unavailable, use the requested expiry.
        #
        # Finally use the nearest expiry from expiryDates.
        # ----------------------------------------------------

        fallback_expiry = None

        if available_expiries:

            fallback_expiry = (
                available_expiries[0]
            )

        timestamp = pd.Timestamp.now()

        normalized = []

        # ====================================================
        # PROCESS EACH STRIKE
        # ====================================================

        for item in rows:

            if not isinstance(item, dict):
                continue

            strike = item.get(
                "strikePrice"
            )

            ce = item.get("CE")

            pe = item.get("PE")

            # ------------------------------------------------
            # Extract expiry directly from CE / PE
            # ------------------------------------------------

            ce_expiry = None
            pe_expiry = None

            if isinstance(ce, dict):

                ce_expiry = (
                    ce.get("expiryDate")
                    or ce.get("expiry")
                )

            if isinstance(pe, dict):

                pe_expiry = (
                    pe.get("expiryDate")
                    or pe.get("expiry")
                )

            # Parent-level fallback
            parent_expiry = (
                item.get("expiryDate")
                or item.get("expiry")
            )

            # =================================================
            # CALL
            # =================================================

            if isinstance(ce, dict):

                expiry = (
                    ce_expiry
                    or parent_expiry
                    or fallback_expiry
                )

                normalized.append({

                    "timestamp": timestamp,

                    "symbol": symbol.upper(),

                    "expiry": expiry,

                    "strike": strike,

                    "option_type": "CE",

                    "last_price": ce.get(
                        "lastPrice"
                    ),

                    "change": ce.get(
                        "change"
                    ),

                    "percent_change": ce.get(
                        "pChange"
                    ),

                    "volume": ce.get(
                        "totalTradedVolume"
                    ),

                    "oi": ce.get(
                        "openInterest"
                    ),

                    "oi_change": ce.get(
                        "changeinOpenInterest"
                    ),

                    "iv": ce.get(
                        "impliedVolatility"
                    ),

                    "bid_price": ce.get(
                        "buyPrice1"
                    ),

                    "ask_price": ce.get(
                        "sellPrice1"
                    ),

                    "bid_quantity": ce.get(
                        "buyQuantity1"
                    ),

                    "ask_quantity": ce.get(
                        "sellQuantity1"
                    ),

                    "total_buy_quantity": ce.get(
                        "totalBuyQuantity"
                    ),

                    "total_sell_quantity": ce.get(
                        "totalSellQuantity"
                    ),

                    "underlying_value": ce.get(
                        "underlyingValue"
                    ),

                    "source": "nse"
                })

            # =================================================
            # PUT
            # =================================================

            if isinstance(pe, dict):

                expiry = (
                    pe_expiry
                    or parent_expiry
                    or fallback_expiry
                )

                normalized.append({

                    "timestamp": timestamp,

                    "symbol": symbol.upper(),

                    "expiry": expiry,

                    "strike": strike,

                    "option_type": "PE",

                    "last_price": pe.get(
                        "lastPrice"
                    ),

                    "change": pe.get(
                        "change"
                    ),

                    "percent_change": pe.get(
                        "pChange"
                    ),

                    "volume": pe.get(
                        "totalTradedVolume"
                    ),

                    "oi": pe.get(
                        "openInterest"
                    ),

                    "oi_change": pe.get(
                        "changeinOpenInterest"
                    ),

                    "iv": pe.get(
                        "impliedVolatility"
                    ),

                    "bid_price": pe.get(
                        "buyPrice1"
                    ),

                    "ask_price": pe.get(
                        "sellPrice1"
                    ),

                    "bid_quantity": pe.get(
                        "buyQuantity1"
                    ),

                    "ask_quantity": pe.get(
                        "sellQuantity1"
                    ),

                    "total_buy_quantity": pe.get(
                        "totalBuyQuantity"
                    ),

                    "total_sell_quantity": pe.get(
                        "totalSellQuantity"
                    ),

                    "underlying_value": pe.get(
                        "underlyingValue"
                    ),

                    "source": "nse"
                })

        df = pd.DataFrame(normalized)

        if df.empty:

            print(
                "[NSE-OPTION] WARNING: "
                "No normalized option rows"
            )

            return df

        # ====================================================
        # NUMERIC COLUMNS
        # ====================================================

        numeric_columns = [
            "strike",
            "last_price",
            "change",
            "percent_change",
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

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # ====================================================
        # TIMESTAMP
        # ====================================================

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        # ====================================================
        # EXPIRY
        # ====================================================

        df["expiry"] = df["expiry"].apply(
            self._normalize_expiry
        )

        # ----------------------------------------------------
        # If expiry is STILL missing, use nearest NSE expiry
        # ----------------------------------------------------

        if df["expiry"].isna().any():

            fallback = self._normalize_expiry(
                fallback_expiry
            )

            if fallback is not None:

                df["expiry"] = (
                    df["expiry"]
                    .fillna(fallback)
                )

        # ----------------------------------------------------
        # Do NOT silently throw away the whole snapshot
        # ----------------------------------------------------

        invalid_expiry = int(
            df["expiry"].isna().sum()
        )

        if invalid_expiry:

            print(
                f"[NSE-OPTION] WARNING: "
                f"{invalid_expiry} rows have invalid expiry"
            )

            df = df[
                df["expiry"].notna()
            ].copy()

        if df.empty:

            raise RuntimeError(
                "NSE option chain contains no valid expiry data."
            )

        # ====================================================
        # SORT
        # ====================================================

        df = (
            df
            .sort_values(
                [
                    "expiry",
                    "strike",
                    "option_type"
                ]
            )
            .reset_index(drop=True)
        )

        print(
            f"[NSE-OPTION] Normalized rows: "
            f"{len(df)}"
        )

        print(
            f"[NSE-OPTION] Expiry: "
            f"{df['expiry'].dt.strftime('%d-%b-%Y').unique().tolist()}"
        )

        return df

    # ========================================================
    # SAVE RAW
    # ========================================================

    def save_raw(
        self,
        data,
        filename="nifty_option_chain_raw.json"
    ):

        path = (
            self.output_dir /
            filename
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                default=str
            )

        print(
            f"[NSE-OPTION] Raw saved: {path}"
        )

        return path

    # ========================================================
    # SAVE CURRENT NORMALIZED
    # ========================================================

    # ============================================================
    # SAVE NORMALIZED + APPEND OPTION HISTORY
    # ============================================================

    def save_normalized(self, df):

        if df is None or df.empty:
            raise ValueError(
                "Cannot save empty normalized option data."
            )

        df = df.copy()

        # --------------------------------------------------------
        # Normalize timestamp
        # --------------------------------------------------------

        if "timestamp" not in df.columns:
            df["timestamp"] = pd.Timestamp.now()

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        df = df.dropna(
            subset=["timestamp"]
        )

        # --------------------------------------------------------
        # Normalize expiry
        # --------------------------------------------------------

        if "expiry" in df.columns:

            df["expiry"] = pd.to_datetime(
                df["expiry"],
                errors="coerce",
                dayfirst=True
            )

        # --------------------------------------------------------
        # Save latest normalized snapshot
        # --------------------------------------------------------

        normalized_path = (
            self.output_dir
            / "nifty_option_chain.csv"
        )

        df.to_csv(
            normalized_path,
            index=False
        )

        print(
            f"[NSE-OPTION] Normalized saved: "
            f"{normalized_path}"
        )

        # --------------------------------------------------------
        # OPTION HISTORY
        # --------------------------------------------------------

        history_dir = (
            Path("market_data")
            / "processed"
        )

        history_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        history_path = (
            history_dir
            / "nifty_option_history.parquet"
        )

        # --------------------------------------------------------
        # Load existing history
        # --------------------------------------------------------

        if history_path.exists():

            try:

                history = pd.read_parquet(
                    history_path
                )

            except Exception:

                print(
                    "[NSE-OPTION] Existing history "
                    "could not be read. Rebuilding."
                )

                history = pd.DataFrame()

        else:

            history = pd.DataFrame()

        # --------------------------------------------------------
        # Append new snapshot
        # --------------------------------------------------------

        if not history.empty:

            combined = pd.concat(
                [
                    history,
                    df
                ],
                ignore_index=True
            )

        else:

            combined = df.copy()

        # --------------------------------------------------------
        # Clean history
        # --------------------------------------------------------

        combined["timestamp"] = pd.to_datetime(
            combined["timestamp"],
            errors="coerce"
        )

        combined["expiry"] = pd.to_datetime(
            combined["expiry"],
            errors="coerce"
        )

        combined = combined.dropna(
            subset=[
                "timestamp",
                "expiry",
                "strike",
                "option_type"
            ]
        )

        # --------------------------------------------------------
        # Remove exact duplicate snapshots
        # --------------------------------------------------------

        key_columns = [
            "timestamp",
            "symbol",
            "expiry",
            "strike",
            "option_type"
        ]

        existing_keys = [
            c
            for c in key_columns
            if c in combined.columns
        ]

        combined = (
            combined
            .drop_duplicates(
                subset=existing_keys,
                keep="last"
            )
            .sort_values(
                existing_keys
            )
            .reset_index(drop=True)
        )

        # --------------------------------------------------------
        # Save history
        # --------------------------------------------------------

        combined.to_parquet(
            history_path,
            index=False
        )

        print(
            f"[NSE-OPTION] History saved: "
            f"{history_path}"
        )

        print(
            f"[NSE-OPTION] History rows: "
            f"{len(combined)}"
        )

        print(
            f"[NSE-OPTION] History timestamps: "
            f"{combined['timestamp'].nunique()}"
        )

        return df

    # ========================================================
    # HISTORY NOTE
    # ========================================================
    # save_normalized() already appends the current normalized
    # snapshot to nifty_option_history.parquet.
    #
    # Do NOT append the same dataframe again from fetch_and_save().
    # Doing that would create duplicate snapshots and could make
    # the movement dataset compare identical prices.

    # ========================================================
    # FETCH + SAVE EVERYTHING
    # ========================================================

    def fetch_and_save(
        self,
        symbol="NIFTY",
        expiry=None
    ):

        data = self.get_raw(
            symbol=symbol,
            expiry=expiry
        )

        df = self.normalize(
            data,
            symbol=symbol
        )

        if df.empty:

            raise RuntimeError(
                "NSE option chain returned no rows."
            )

        self.save_raw(
            data
        )

        # save_normalized() saves the latest CSV AND appends exactly
        # one market snapshot to the history parquet.
        self.save_normalized(
            df
        )

        return df

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        try:

            self.nse.exit()

        except Exception:

            pass