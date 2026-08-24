# ============================================================
# TradingAI - NSE DATA SOURCE
# ============================================================

from pathlib import Path
from datetime import datetime, date
import json

import pandas as pd
import requests


class NseSource:

    BASE_URL = "https://www.nseindia.com"

    def __init__(self, output_dir):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.session = requests.Session()

        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": "https://www.nseindia.com/",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
        })

        self._initialize_session()


    # ========================================================
    # SESSION
    # ========================================================

    def _initialize_session(self):

        print(
            "[NSE] Initializing NSE session..."
        )

        response = self.session.get(
            self.BASE_URL,
            timeout=20
        )

        print(
            f"[NSE] Homepage status: "
            f"{response.status_code}"
        )

        response.raise_for_status()

        # ----------------------------------------------------
        # Warm up option-chain page
        # ----------------------------------------------------

        option_page = self.session.get(
            f"{self.BASE_URL}/option-chain",
            timeout=20
        )

        print(
            f"[NSE] Option-chain page status: "
            f"{option_page.status_code}"
        )

        print(
            f"[NSE] Session initialized: "
            f"{response.status_code}"
        )


    # ========================================================
    # SESSION REFRESH
    # ========================================================

    def _refresh_session(self):

        print(
            "\n[NSE] Refreshing NSE session..."
        )

        self.session.close()

        self.session = requests.Session()

        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": "https://www.nseindia.com/",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
        })

        self._initialize_session()


    # ========================================================
    # GENERIC JSON REQUEST
    # ========================================================

    def _get_json(
        self,
        url,
        params=None,
        retries=2,
        refresh_on_403=True
    ):

        last_response = None

        for attempt in range(retries + 1):

            response = self.session.get(
                url,
                params=params,
                timeout=30
            )

            last_response = response

            print(
                f"[NSE] HTTP status: "
                f"{response.status_code}"
            )

            print(
                f"[NSE] Final URL: "
                f"{response.url}"
            )

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if response.status_code == 200:

                try:

                    return response.json()

                except ValueError as exc:

                    preview = response.text[:500]

                    raise requests.HTTPError(
                        "NSE returned invalid JSON.\n"
                        f"Response preview:\n{preview}"
                    ) from exc

            # ------------------------------------------------
            # 403
            # ------------------------------------------------

            if response.status_code == 403:

                print(
                    "[NSE] Access denied."
                )

                print(
                    "[NSE] Response preview:"
                )

                print(
                    response.text[:1000]
                )

                if (
                    refresh_on_403
                    and attempt < retries
                ):

                    print(
                        "[NSE] Retrying after "
                        "session refresh..."
                    )

                    self._refresh_session()

                    continue

                raise requests.HTTPError(
                    "NSE API access denied (403)"
                )

            # ------------------------------------------------
            # 404
            # ------------------------------------------------

            if response.status_code == 404:

                if attempt < retries:

                    print(
                        "[NSE] Request failed: "
                        f"NSE endpoint not found: "
                        f"{response.url}"
                    )

                    print(
                        "[NSE] Retrying..."
                    )

                    continue

                raise requests.HTTPError(
                    "NSE endpoint not found: "
                    f"{response.url}"
                )

            # ------------------------------------------------
            # OTHER ERROR
            # ------------------------------------------------

            if attempt < retries:

                print(
                    "[NSE] Request failed. "
                    "Retrying..."
                )

                continue

            response.raise_for_status()

        if last_response is not None:
            last_response.raise_for_status()

        raise requests.HTTPError(
            "NSE request failed."
        )


    # ========================================================
    # HISTORICAL INDEX
    # ========================================================

    def get_index_history(
        self,
        symbol,
        from_date,
        to_date
    ):

        print(
            f"\n[NSE] Downloading index history: "
            f"{symbol}"
        )

        url = (
            f"{self.BASE_URL}"
            "/api/historicalOR/"
            "indicesHistory"
        )

        params = {
            "indexType": symbol,
            "from": from_date.strftime(
                "%d-%m-%Y"
            ),
            "to": to_date.strftime(
                "%d-%m-%Y"
            ),
        }

        data = self._get_json(
            url=url,
            params=params,
            retries=2
        )

        records = data.get(
            "data",
            []
        )

        print(
            f"[NSE] {symbol}: "
            f"{len(records)} rows"
        )

        return records

    # ========================================================
    # FUTURES
    # ========================================================

    def get_futures(
        self,
        symbol="NIFTY"
    ):
        """
        Fetch NSE futures contracts using the current
        NSE NextApi derivatives endpoint.

        Returns normalized futures dataframe.
        """

        import pandas as pd

        symbol = str(symbol).upper().strip()

        print(
            f"\n[NSE-FUTURES] Downloading futures: "
            f"{symbol}"
        )

        # ----------------------------------------------------
        # CURRENT NSE NEXT API
        # ----------------------------------------------------

        url = (
            f"{self.BASE_URL}"
            "/api/NextApi/apiClient/GetQuoteApi"
        )

        params = {
            "functionName": "getSymbolDerivativesData",
            "symbol": symbol,
        }

        data = self._get_json(
            url=url,
            params=params,
            retries=2
        )

        if not data:
            raise RuntimeError(
                f"NSE returned empty futures response "
                f"for {symbol}"
            )

        # ----------------------------------------------------
        # EXTRACT DATA
        # ----------------------------------------------------

        records = data.get(
            "data",
            []
        )

        if not isinstance(records, list):
            records = []

        if not records:
            raise RuntimeError(
                f"No derivative contracts returned "
                f"for {symbol}"
            )

        print(
            f"[NSE-FUTURES] Raw contracts: "
            f"{len(records)}"
        )

        # ----------------------------------------------------
        # DATAFRAME
        # ----------------------------------------------------

        df = pd.json_normalize(
            records
        )

        # ----------------------------------------------------
        # NORMALIZE COLUMN NAMES
        # ----------------------------------------------------

        df.columns = [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            for column in df.columns
        ]

        # ----------------------------------------------------
        # KEEP FUTURES ONLY
        # ----------------------------------------------------

        if "instrumenttype" in df.columns:

            df = df[
                df["instrumenttype"]
                .astype(str)
                .str.upper()
                .str.startswith("FUT")
            ]

        elif "instrument_type" in df.columns:

            df = df[
                df["instrument_type"]
                .astype(str)
                .str.upper()
                .str.startswith("FUT")
            ]

        # ----------------------------------------------------
        # STANDARD COLUMN NAMES
        # ----------------------------------------------------

        rename_map = {
            "expirydate": "expiry",
            "expiry_date": "expiry",

            "lastprice": "last_price",
            "last_price": "last_price",

            "openprice": "open",
            "open_price": "open",

            "highprice": "high",
            "high_price": "high",

            "lowprice": "low",
            "low_price": "low",

            "previousclose": "previous_close",
            "prevclose": "previous_close",
            "prev_close": "previous_close",

            "oi": "open_interest",
            "oi_change": "open_interest_change",

            "openinterest": "open_interest",
            "changeinopeninterest": "open_interest_change",

            "totaltradedvolume": "volume",
            "total_traded_volume": "volume",

            "underlyingvalue": "underlying_value",
            "underlying_value": "underlying_value",

            "turnover": "turnover",
        }

        existing_renames = {}

        for old, new in rename_map.items():

            if old in df.columns:
                existing_renames[old] = new

        if existing_renames:

            df = df.rename(
                columns=existing_renames
            )

        # ----------------------------------------------------
        # SYMBOL
        # ----------------------------------------------------

        df["symbol"] = symbol

        # ----------------------------------------------------
        # SOURCE
        # ----------------------------------------------------

        df["source"] = "nse"

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

        else:

            df["timestamp"] = pd.Timestamp.now()

        # ----------------------------------------------------
        # EXPIRY
        # ----------------------------------------------------

        if "expiry" in df.columns:

            df["expiry"] = pd.to_datetime(
                df["expiry"],
                errors="coerce"
            )

        # ----------------------------------------------------
        # NUMERIC FIELDS
        # ----------------------------------------------------

        numeric_columns = [
            "open",
            "high",
            "low",
            "previous_close",
            "last_price",
            "volume",
            "open_interest",
            "open_interest_change",
            "underlying_value",
            "turnover",
        ]

        for column in numeric_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        sort_columns = []

        if "expiry" in df.columns:
            sort_columns.append("expiry")

        if "symbol" in df.columns:
            sort_columns.append("symbol")

        if sort_columns:

            df = df.sort_values(
                sort_columns
            )

        # ----------------------------------------------------
        # REMOVE DUPLICATES
        # ----------------------------------------------------

        df = df.drop_duplicates(
            ignore_index=True
        )

        print(
            f"[NSE-FUTURES] Futures rows: "
            f"{len(df)}"
        )

        print(
            f"[NSE-FUTURES] Columns:"
        )

        print(
            list(df.columns)
        )

        return df.reset_index(
            drop=True
        )
    # ========================================================
    # STOCK QUOTE
    # ========================================================

    def get_quote(
        self,
        symbol
    ):

        print(
            f"\n[NSE] Getting quote: "
            f"{symbol}"
        )

        # ----------------------------------------------------
        # NOTE
        # ----------------------------------------------------
        # NSE currently returns 403 for this endpoint in the
        # current environment even after warming the quote page.
        #
        # We keep the method here so the unified architecture
        # remains intact.
        # ----------------------------------------------------

        quote_page = self.session.get(
            f"{self.BASE_URL}/get-quotes/equity",
            params={
                "symbol": symbol
            },
            timeout=20
        )

        print(
            f"[NSE] Quote page status: "
            f"{quote_page.status_code}"
        )

        url = (
            f"{self.BASE_URL}"
            "/api/quote-equity"
        )

        return self._get_json(
            url=url,
            params={
                "symbol": symbol
            },
            retries=2
        )


    # ========================================================
    # OPTION CHAIN
    # ========================================================

    def get_option_chain(
        self,
        symbol="NIFTY",
        expiry=None
    ):
        """
        Fetch option-chain data using the
        NseIndiaApi GitHub library.

        This is intentionally NOT using the old:

            /api/option-chain-indices

        endpoint because that endpoint is returning 404.

        The installed NseIndiaApi library uses:

            option-chain-contract-info
            option-chain-v3
        """

        print(
            f"\n[NSE-OPTION] Downloading option chain: "
            f"{symbol}"
        )

        symbol = str(
            symbol
        ).upper()

        # ----------------------------------------------------
        # IMPORT GITHUB LIBRARY
        # ----------------------------------------------------

        try:

            from nse import NSE

        except ImportError as exc:

            raise ImportError(
                "NseIndiaApi library is required "
                "for option chain.\n"
                "Install it with:\n"
                "pip install nse"
            ) from exc

        # ----------------------------------------------------
        # CREATE CLIENT
        # ----------------------------------------------------

        client = NSE(
            download_folder=self.output_dir
        )

        try:

            expiry_date = None

            # ------------------------------------------------
            # PARSE REQUESTED EXPIRY
            # ------------------------------------------------

            if expiry is not None:

                if isinstance(
                    expiry,
                    datetime
                ):

                    expiry_date = expiry

                elif isinstance(
                    expiry,
                    date
                ):

                    expiry_date = datetime.combine(
                        expiry,
                        datetime.min.time()
                    )

                elif isinstance(
                    expiry,
                    str
                ):

                    expiry_text = (
                        expiry.strip()
                    )

                    formats = [
                        "%d-%b-%Y",
                        "%d-%B-%Y",
                        "%d-%m-%Y",
                        "%Y-%m-%d",
                    ]

                    for fmt in formats:

                        try:

                            expiry_date = (
                                datetime.strptime(
                                    expiry_text,
                                    fmt
                                )
                            )

                            break

                        except ValueError:
                            continue

                    if expiry_date is None:

                        raise ValueError(
                            "Unsupported expiry format: "
                            f"{expiry}"
                        )

            # ------------------------------------------------
            # FETCH RAW DATA
            # ------------------------------------------------

            raw = client.optionChain(
                symbol.lower(),
                expiry_date=expiry_date
            )

            records = raw.get(
                "records",
                {}
            )

            rows = records.get(
                "data",
                []
            )

            expiry_dates = records.get(
                "expiryDates",
                []
            )

            print(
                f"[NSE-OPTION] Rows: "
                f"{len(rows)}"
            )

            print(
                f"[NSE-OPTION] Expiries: "
                f"{len(expiry_dates)}"
            )

            if expiry_dates:

                print(
                    f"[NSE-OPTION] Nearest expiry: "
                    f"{expiry_dates[0]}"
                )

            if not rows:

                return pd.DataFrame()

            # ------------------------------------------------
            # NORMALIZE CE / PE
            # ------------------------------------------------

            normalized = []

            timestamp = pd.Timestamp.now()

            for row in rows:

                strike = row.get(
                    "strikePrice"
                )

                row_expiry = row.get(
                    "expiryDates"
                )

                for option_type in (
                    "CE",
                    "PE"
                ):

                    option = row.get(
                        option_type
                    )

                    if not option:
                        continue

                    normalized.append({

                        "timestamp": timestamp,

                        "symbol": symbol,

                        "expiry": row_expiry,

                        "strike": strike,

                        "option_type": option_type,

                        "last_price": option.get(
                            "lastPrice"
                        ),

                        "change": option.get(
                            "change"
                        ),

                        "percent_change": option.get(
                            "pChange"
                        ),

                        "volume": option.get(
                            "totalTradedVolume"
                        ),

                        "oi": option.get(
                            "openInterest"
                        ),

                        "oi_change": option.get(
                            "changeinOpenInterest"
                        ),

                        "iv": option.get(
                            "impliedVolatility"
                        ),

                        "bid_price": option.get(
                            "buyPrice1"
                        ),

                        "ask_price": option.get(
                            "sellPrice1"
                        ),

                        "bid_quantity": option.get(
                            "buyQuantity1"
                        ),

                        "ask_quantity": option.get(
                            "sellQuantity1"
                        ),

                        "total_buy_quantity": option.get(
                            "totalBuyQuantity"
                        ),

                        "total_sell_quantity": option.get(
                            "totalSellQuantity"
                        ),

                        "underlying_value": option.get(
                            "underlyingValue"
                        ),

                        "source": "nse",

                    })

            df = pd.DataFrame(
                normalized
            )

            # ------------------------------------------------
            # EXPIRY
            # ------------------------------------------------

            if not df.empty:

                df["expiry"] = pd.to_datetime(
                    df["expiry"],
                    format="%d-%b-%Y",
                    errors="coerce"
                )

                df = (
                    df
                    .sort_values(
                        [
                            "expiry",
                            "strike",
                            "option_type"
                        ]
                    )
                    .reset_index(
                        drop=True
                    )
                )

            print(
                f"[NSE-OPTION] Normalized rows: "
                f"{len(df)}"
            )

            return df

        finally:

            try:
                client.exit()

            except Exception:
                pass


    # ========================================================
    # MARKET STATUS
    # ========================================================

    def get_market_status(self):

        print(
            "\n[NSE] Getting market status..."
        )

        url = (
            f"{self.BASE_URL}"
            "/api/marketStatus"
        )

        return self._get_json(
            url=url,
            retries=2
        )


    # ========================================================
    # SAVE JSON
    # ========================================================

    def save(
        self,
        data,
        filename
    ):

        path = (
            self.output_dir /
            filename
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as fp:

            json.dump(
                data,
                fp,
                indent=2,
                default=str
            )

        print(
            f"[NSE] Saved: {path}"
        )

        return path