import requests
import urllib3
from datetime import datetime


urllib3.disable_warnings()


class OptionChain:

    BASE_URL = "https://www.nseindia.com"

    # =========================================================
    # INDEX CONFIGURATION
    # =========================================================

    INDEX_CONFIG = {

        "NIFTY 50": {
            "symbol": "NIFTY",
            "api_symbol": "NIFTY",
        },

        "BANK NIFTY": {
            "symbol": "BANKNIFTY",
            "api_symbol": "BANKNIFTY",
        },

        "FINNIFTY": {
            "symbol": "FINNIFTY",
            "api_symbol": "FINNIFTY",
        },

        "MIDCAP NIFTY": {
            "symbol": "MIDCPNIFTY",
            "api_symbol": "MIDCPNIFTY",
        },
    }

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self):

        self.session = requests.Session()

        self.session.verify = False

        self.headers = {

            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            ),

            "Accept": (
                "application/json, text/plain, */*"
            ),

            "Accept-Language":
                "en-US,en;q=0.9",

            "Referer":
                "https://www.nseindia.com/option-chain/",

            "Connection":
                "keep-alive",

            "Cache-Control":
                "no-cache",

        }

        self._initialize_session()

    # =========================================================
    # NORMALIZE INDEX
    # =========================================================

    def normalize_index(self, index):

        index = str(
            index or "NIFTY 50"
        ).strip().upper()

        aliases = {

            "NIFTY":
                "NIFTY 50",

            "NIFTY50":
                "NIFTY 50",

            "NIFTY 50":
                "NIFTY 50",

            "BANKNIFTY":
                "BANK NIFTY",

            "BANK NIFTY":
                "BANK NIFTY",

            "BANK NIFTY 50":
                "BANK NIFTY",

            "FINNIFTY":
                "FINNIFTY",

            "FIN NIFTY":
                "FINNIFTY",

            "MIDCAP NIFTY":
                "MIDCAP NIFTY",

            "MIDCAPNIFTY":
                "MIDCAP NIFTY",

            "MIDCPNIFTY":
                "MIDCAP NIFTY",
        }

        return aliases.get(
            index,
            "NIFTY 50"
        )

    # =========================================================
    # NSE SESSION
    # =========================================================

    def _initialize_session(self):

        try:

            # -------------------------------------------------
            # First request NSE homepage.
            # -------------------------------------------------

            response = self.session.get(
                self.BASE_URL,
                headers=self.headers,
                timeout=15
            )

            print(
                "NSE homepage:",
                response.status_code
            )

            # -------------------------------------------------
            # Then open option-chain page.
            # -------------------------------------------------

            response = self.session.get(
                f"{self.BASE_URL}/option-chain/",
                headers=self.headers,
                timeout=15
            )

            print(
                "NSE option-chain page:",
                response.status_code
            )

        except Exception as e:

            print(
                "NSE session initialization error:",
                e
            )

    # =========================================================
    # REFRESH SESSION
    # =========================================================

    def refresh_session(self):

        try:

            self.session.close()

        except Exception:

            pass

        self.session = requests.Session()

        self.session.verify = False

        self._initialize_session()

    # =========================================================
    # GENERIC GET JSON
    # =========================================================

    def _get_json(
        self,
        url,
        retry=True
    ):

        try:

            response = self.session.get(
                url,
                headers=self.headers,
                timeout=20
            )

            # -------------------------------------------------
            # NSE may return 401/403 when session expires.
            # -------------------------------------------------

            if response.status_code in (
                401,
                403
            ):

                if retry:

                    print(
                        "NSE session expired. "
                        "Refreshing session..."
                    )

                    self.refresh_session()

                    return self._get_json(
                        url,
                        retry=False
                    )

                print(
                    "NSE request blocked:",
                    response.status_code
                )

                return None

            response.raise_for_status()

            text = response.text.strip()

            if not text:

                print(
                    "NSE returned empty response."
                )

                return None

            data = response.json()

            if not isinstance(
                data,
                dict
            ):

                print(
                    "NSE returned unexpected "
                    "response type."
                )

                return None

            return data

        except requests.exceptions.RequestException as e:

            print(
                "NSE request error:",
                e
            )

            if retry:

                try:

                    self.refresh_session()

                    return self._get_json(
                        url,
                        retry=False
                    )

                except Exception:

                    pass

            return None

        except ValueError as e:

            print(
                "NSE returned invalid JSON:",
                e
            )

            return None

        except Exception as e:

            print(
                "NSE API error:",
                e
            )

            return None

    # =========================================================
    # GET CONFIG
    # =========================================================

    def _get_config(self, index):

        index = self.normalize_index(
            index
        )

        return self.INDEX_CONFIG.get(
            index
        )

    # =========================================================
    # GET EXPIRY DATES
    # =========================================================

    def get_expiry_dates(
        self,
        index="NIFTY 50"
    ):

        index = self.normalize_index(
            index
        )

        config = self._get_config(
            index
        )

        if not config:

            print(
                f"Unsupported index: {index}"
            )

            return []

        symbol = config[
            "api_symbol"
        ]

        url = (
            f"{self.BASE_URL}/api/"
            "option-chain-contract-info"
            f"?symbol={symbol}"
        )

        data = self._get_json(
            url
        )

        if not data:

            print(
                f"Unable to fetch "
                f"{index} expiry information."
            )

            return []

        expiry_dates = (
            data.get(
                "expiryDates"
            )
            or []
        )

        if not expiry_dates:

            print(
                f"No {index} expiry dates "
                "returned by NSE."
            )

            return []

        # -----------------------------------------------------
        # Remove duplicates while preserving order.
        # -----------------------------------------------------

        cleaned = []

        seen = set()

        for expiry in expiry_dates:

            expiry = str(
                expiry
            ).strip()

            if not expiry:
                continue

            if expiry in seen:
                continue

            seen.add(
                expiry
            )

            cleaned.append(
                expiry
            )

        # -----------------------------------------------------
        # Sort chronologically where possible.
        # -----------------------------------------------------

        def expiry_key(value):

            try:

                return datetime.strptime(
                    value,
                    "%d-%b-%Y"
                )

            except Exception:

                return datetime.max

        cleaned.sort(
            key=expiry_key
        )

        return cleaned

    # =========================================================
    # GET CURRENT / NEAREST EXPIRY
    # =========================================================

    def get_current_expiry(
        self,
        index="NIFTY 50"
    ):

        index = self.normalize_index(
            index
        )

        expiry_dates = (
            self.get_expiry_dates(
                index
            )
        )

        if not expiry_dates:

            print(
                f"Could not determine "
                f"current {index} expiry."
            )

            return None

        today = datetime.now().date()

        valid_expiries = []

        for expiry in expiry_dates:

            try:

                expiry_date = datetime.strptime(
                    expiry,
                    "%d-%b-%Y"
                ).date()

                if expiry_date >= today:

                    valid_expiries.append(
                        (
                            expiry_date,
                            expiry
                        )
                    )

            except Exception:

                continue

        if not valid_expiries:

            print(
                f"No future {index} "
                "expiry found."
            )

            return None

        valid_expiries.sort(
            key=lambda item: item[0]
        )

        current_expiry = (
            valid_expiries[0][1]
        )

        print(
            f"{index} expiry selected: "
            f"{current_expiry}"
        )

        return current_expiry

    # =========================================================
    # GENERIC OPTION CHAIN
    # =========================================================

    def get_chain(
        self,
        symbol="NIFTY 50",
        expiry=None
    ):

        index = self.normalize_index(
            symbol
        )

        config = self._get_config(
            index
        )

        if not config:

            print(
                f"Unsupported option-chain "
                f"index: {index}"
            )

            return None

        api_symbol = config[
            "api_symbol"
        ]

        # -----------------------------------------------------
        # Resolve expiry automatically.
        # -----------------------------------------------------

        if not expiry:

            expiry = self.get_current_expiry(
                index
            )

        if not expiry:

            print(
                f"Unable to determine "
                f"{index} expiry."
            )

            return None

        expiry = str(
            expiry
        ).strip()

        print(
            f"Fetching {index} "
            f"option chain | "
            f"Expiry: {expiry}"
        )

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # expiry must be included.
        # NSE may return {} when omitted.
        # -----------------------------------------------------

        url = (
            f"{self.BASE_URL}/api/"
            "option-chain-v3"
            "?type=Indices"
            f"&symbol={api_symbol}"
            f"&expiry={expiry}"
        )

        data = self._get_json(
            url
        )

        if not data:

            print(
                f"{index} option chain "
                f"returned no data for "
                f"expiry {expiry}."
            )

            return None

        # -----------------------------------------------------
        # Validate response.
        # -----------------------------------------------------

        records = data.get(
            "records"
        )

        if not records:

            print(
                f"{index} option chain "
                "does not contain records."
            )

            return None

        # -----------------------------------------------------
        # Attach useful metadata.
        # -----------------------------------------------------

        data["_selected_index"] = (
            index
        )

        data["_selected_symbol"] = (
            api_symbol
        )

        data["_selected_expiry"] = (
            expiry
        )

        return data

    # =========================================================
    # NIFTY
    # =========================================================

    def get_nifty(
        self,
        expiry=None
    ):

        return self.get_chain(
            symbol="NIFTY 50",
            expiry=expiry
        )

    # =========================================================
    # BANK NIFTY
    # =========================================================

    def get_banknifty(
        self,
        expiry=None
    ):

        return self.get_chain(
            symbol="BANK NIFTY",
            expiry=expiry
        )

    # =========================================================
    # FINNIFTY
    # =========================================================

    def get_finnifty(
        self,
        expiry=None
    ):

        return self.get_chain(
            symbol="FINNIFTY",
            expiry=expiry
        )

    # =========================================================
    # MIDCAP NIFTY
    # =========================================================

    def get_midcapnifty(
        self,
        expiry=None
    ):

        return self.get_chain(
            symbol="MIDCAP NIFTY",
            expiry=expiry
        )

    # =========================================================
    # EXPLICIT EXPIRY HELPERS
    # =========================================================

    def get_nifty_for_expiry(
        self,
        expiry
    ):

        return self.get_nifty(
            expiry=expiry
        )

    # ---------------------------------------------------------

    def get_banknifty_for_expiry(
        self,
        expiry
    ):

        return self.get_banknifty(
            expiry=expiry
        )

    # ---------------------------------------------------------

    def get_finnifty_for_expiry(
        self,
        expiry
    ):

        return self.get_finnifty(
            expiry=expiry
        )

    # ---------------------------------------------------------

    def get_midcapnifty_for_expiry(
        self,
        expiry
    ):

        return self.get_midcapnifty(
            expiry=expiry
        )

    # =========================================================
    # GET ALL EXPIRIES + CHAIN
    # =========================================================

    def get_chain_with_expiries(
        self,
        index="NIFTY 50"
    ):

        index = self.normalize_index(
            index
        )

        expiry_dates = (
            self.get_expiry_dates(
                index
            )
        )

        if not expiry_dates:

            return None

        current_expiry = (
            self.get_current_expiry(
                index
            )
        )

        if not current_expiry:

            return None

        chain = self.get_chain(
            symbol=index,
            expiry=current_expiry
        )

        if not chain:

            return None

        return {

            "index":
                index,

            "symbol":
                self.INDEX_CONFIG[
                    index
                ]["api_symbol"],

            "expiry":
                current_expiry,

            "expiry_dates":
                expiry_dates,

            "data":
                chain
        }

    # =========================================================
    # NIFTY COMPATIBILITY
    # =========================================================

    def get_nifty_with_expiries(
        self
    ):

        return self.get_chain_with_expiries(
            "NIFTY 50"
        )

    # =========================================================
    # BANK NIFTY COMPATIBILITY
    # =========================================================

    def get_banknifty_with_expiries(
        self
    ):

        return self.get_chain_with_expiries(
            "BANK NIFTY"
        )

    # =========================================================
    # FINNIFTY COMPATIBILITY
    # =========================================================

    def get_finnifty_with_expiries(
        self
    ):

        return self.get_chain_with_expiries(
            "FINNIFTY"
        )

    # =========================================================
    # MIDCAP NIFTY COMPATIBILITY
    # =========================================================

    def get_midcapnifty_with_expiries(
        self
    ):

        return self.get_chain_with_expiries(
            "MIDCAP NIFTY"
        )