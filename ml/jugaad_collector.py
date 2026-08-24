from datetime import date, timedelta
from pathlib import Path
import time
import pandas as pd

from jugaad_data.nse import (
    derivatives_df,
    expiry_dates,
)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "ml_data"

NIFTY_DIR = DATA_DIR / "nifty"
FUTURES_DIR = DATA_DIR / "futures"
OPTIONS_DIR = DATA_DIR / "options"

NIFTY_DIR.mkdir(parents=True, exist_ok=True)
FUTURES_DIR.mkdir(parents=True, exist_ok=True)
OPTIONS_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Change these later if required
# ------------------------------------------------------------

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 8, 17)

# Number of strikes above/below ATM
STRIKES_EACH_SIDE = 5

# Strike interval for NIFTY
NIFTY_STRIKE_STEP = 50

# Small delay so we don't hammer NSE
REQUEST_DELAY = 1.0


# ============================================================
# HELPERS
# ============================================================

def clean_filename(value):
    return str(value).replace("/", "-").replace(":", "-")


def date_range(start_date, end_date):
    current = start_date

    while current <= end_date:
        yield current
        current += timedelta(days=1)


def normalize_columns(df):
    if df is None:
        return None

    df = df.copy()

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    return df


# ============================================================
# EXPIRY DISCOVERY
# ============================================================

def get_nifty_expiries(start_date, end_date):
    """
    Discover NIFTY option expiry dates through jugaad-data.
    """

    print("\n" + "=" * 70)
    print("DISCOVERING NIFTY EXPIRIES")
    print("=" * 70)

    expiries = []

    current = start_date

    # Ask for expiries around each month.
    # This avoids repeatedly requesting every trading day.
    checked_months = set()

    while current <= end_date:

        month_key = (
            current.year,
            current.month
        )

        if month_key not in checked_months:

            checked_months.add(month_key)

            try:

                print(
                    f"Checking expiry dates around {current}..."
                )

                result = expiry_dates(
                    current,
                    instrument_type="OPTIDX",
                    symbol="NIFTY"
                )

                print("Result:", result)

                if result is not None:

                    if isinstance(result, (list, tuple)):

                        for item in result:

                            if item not in expiries:
                                expiries.append(item)

                    elif isinstance(result, pd.DataFrame):

                        for col in result.columns:

                            for item in result[col].tolist():

                                if item not in expiries:
                                    expiries.append(item)

                    else:

                        try:

                            for item in result:

                                if item not in expiries:
                                    expiries.append(item)

                        except TypeError:
                            pass

            except Exception as exc:

                print(
                    f"Expiry lookup failed for {current}: {exc}"
                )

        # Move to next month
        if current.month == 12:

            current = date(
                current.year + 1,
                1,
                1
            )

        else:

            current = date(
                current.year,
                current.month + 1,
                1
            )

    # --------------------------------------------------------
    # Normalize expiry values
    # --------------------------------------------------------

    normalized = []

    for expiry in expiries:

        if expiry is None:
            continue

        if isinstance(expiry, pd.Timestamp):
            expiry = expiry.date()

        if isinstance(expiry, date):
            expiry = expiry

        normalized.append(expiry)

    # Remove duplicates
    unique = []

    for expiry in normalized:

        if expiry not in unique:
            unique.append(expiry)

    unique.sort(
        key=lambda x: str(x)
    )

    print("\nDiscovered expiries:")

    for expiry in unique:
        print(" ", expiry)

    return unique


# ============================================================
# GET UNDERLYING PRICE
# ============================================================

def get_reference_price():

    nifty_file = (
        NIFTY_DIR /
        "nifty_2025-01-01_2026-08-17.csv"
    )

    if nifty_file.exists():

        df = pd.read_csv(
            nifty_file
        )

        if "CLOSE" in df.columns:

            close = pd.to_numeric(
                df["CLOSE"],
                errors="coerce"
            ).dropna()

            if not close.empty:
                return float(close.iloc[-1])

    return None


# ============================================================
# ROUND TO NIFTY STRIKE
# ============================================================

def nearest_strike(
    price,
    step=NIFTY_STRIKE_STEP
):

    if price is None:
        return None

    return int(
        round(price / step) * step
    )


# ============================================================
# BUILD STRIKE LIST
# ============================================================

def build_strikes(
    atm,
    each_side=STRIKES_EACH_SIDE
):

    if atm is None:
        return []

    strikes = []

    for offset in range(
        -each_side,
        each_side + 1
    ):

        strike = (
            atm +
            offset * NIFTY_STRIKE_STEP
        )

        strikes.append(
            int(strike)
        )

    return strikes


# ============================================================
# DOWNLOAD ONE OPTION
# ============================================================

def download_option(
    expiry,
    strike,
    option_type,
    start_date,
    end_date
):

    print(
        f"  {expiry} | "
        f"{strike} | "
        f"{option_type}"
    )

    try:

        df = derivatives_df(
            symbol="NIFTY",
            from_date=start_date,
            to_date=end_date,
            expiry_date=expiry,
            instrument_type="OPTIDX",
            strike_price=strike,
            option_type=option_type
        )

        if df is None:
            print("    -> no data")
            return None

        df = normalize_columns(df)

        if df.empty:
            print("    -> empty")
            return None

        # Add our own metadata
        df["underlying"] = "NIFTY"
        df["expiry_requested"] = str(expiry)
        df["strike_requested"] = strike
        df["option_type_requested"] = option_type

        print(
            f"    -> {len(df)} rows"
        )

        return df

    except Exception as exc:

        print(
            f"    ERROR: {exc}"
        )

        return None


# ============================================================
# DOWNLOAD FUTURES
# ============================================================

def download_future(
    expiry,
    start_date,
    end_date
):

    print(
        f"  FUTIDX | expiry={expiry}"
    )

    try:

        df = derivatives_df(
            symbol="NIFTY",
            from_date=start_date,
            to_date=end_date,
            expiry_date=expiry,
            instrument_type="FUTIDX"
        )

        if df is None:
            return None

        df = normalize_columns(df)

        if df.empty:
            return None

        df["underlying"] = "NIFTY"
        df["expiry_requested"] = str(expiry)

        print(
            f"    -> {len(df)} rows"
        )

        return df

    except Exception as exc:

        print(
            f"    ERROR: {exc}"
        )

        return None


# ============================================================
# SAVE DATA
# ============================================================

def save_dataframe(
    df,
    directory,
    filename
):

    if df is None or df.empty:
        return None

    path = directory / filename

    df.to_csv(
        path,
        index=False
    )

    print(
        f"Saved: {path}"
    )

    return path


# ============================================================
# MAIN OPTIONS COLLECTION
# ============================================================

def collect_options(
    start_date,
    end_date
):

    print("\n" + "=" * 70)
    print("NIFTY OPTIONS COLLECTION")
    print("=" * 70)

    reference_price = get_reference_price()

    if reference_price is None:

        raise RuntimeError(
            "Could not determine NIFTY reference price."
        )

    atm = nearest_strike(
        reference_price
    )

    strikes = build_strikes(
        atm
    )

    print(
        f"\nReference NIFTY: {reference_price}"
    )

    print(
        f"ATM strike: {atm}"
    )

    print(
        f"Strikes: {strikes}"
    )

    expiries = get_nifty_expiries(
        start_date,
        end_date
    )

    if not expiries:

        raise RuntimeError(
            "No NIFTY expiries were discovered."
        )

    all_frames = []

    for expiry in expiries:

        print(
            "\n" +
            "-" * 70
        )

        print(
            f"EXPIRY: {expiry}"
        )

        print(
            "-" * 70
        )

        # ----------------------------------------------------
        # Skip expiry completely outside requested period
        # ----------------------------------------------------

        try:

            if hasattr(expiry, "date"):
                expiry_date = expiry.date()
            else:
                expiry_date = expiry

            if (
                expiry_date < start_date
                or expiry_date > end_date
            ):
                continue

        except Exception:
            pass

        for strike in strikes:

            for option_type in ["CE", "PE"]:

                df = download_option(
                    expiry,
                    strike,
                    option_type,
                    start_date,
                    end_date
                )

                if df is not None:

                    all_frames.append(
                        df
                    )

                time.sleep(
                    REQUEST_DELAY
                )

    if not all_frames:

        print(
            "\nNo option data was collected."
        )

        return None

    result = pd.concat(
        all_frames,
        ignore_index=True
    )

    result = result.drop_duplicates()

    output = (
        OPTIONS_DIR /
        f"nifty_options_"
        f"{start_date}_"
        f"{end_date}.csv"
    )

    result.to_csv(
        output,
        index=False
    )

    print(
        "\n" +
        "=" * 70
    )

    print(
        "OPTIONS COLLECTION COMPLETE"
    )

    print(
        "Rows:",
        len(result)
    )

    print(
        "Columns:",
        result.columns.tolist()
    )

    print(
        "Saved:",
        output
    )

    return result


# ============================================================
# MAIN FUTURES COLLECTION
# ============================================================

def collect_futures(
    start_date,
    end_date
):

    print("\n" + "=" * 70)
    print("NIFTY FUTURES COLLECTION")
    print("=" * 70)

    expiries = get_nifty_expiries(
        start_date,
        end_date
    )

    frames = []

    for expiry in expiries:

        try:

            df = download_future(
                expiry,
                start_date,
                end_date
            )

            if df is not None:

                frames.append(
                    df
                )

            time.sleep(
                REQUEST_DELAY
            )

        except Exception as exc:

            print(
                f"Future error: {exc}"
            )

    if not frames:

        print(
            "No futures data collected."
        )

        return None

    result = pd.concat(
        frames,
        ignore_index=True
    )

    result = result.drop_duplicates()

    output = (
        FUTURES_DIR /
        f"nifty_futures_"
        f"{start_date}_"
        f"{end_date}.csv"
    )

    result.to_csv(
        output,
        index=False
    )

    print(
        "\nFUTURES COMPLETE"
    )

    print(
        "Rows:",
        len(result)
    )

    print(
        "Columns:",
        result.columns.tolist()
    )

    print(
        "Saved:",
        output
    )

    return result


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("TRADINGAI - JUGAAD F&O DATA COLLECTOR")
    print("=" * 70)

    print(
        "\nStart:",
        START_DATE
    )

    print(
        "End:",
        END_DATE
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "This collector requests a limited ATM ± "
        f"{STRIKES_EACH_SIDE} strike range."
    )

    print(
        "It does NOT download every possible option strike."
    )

    # --------------------------------------------------------
    # Futures
    # --------------------------------------------------------

    collect_futures(
        START_DATE,
        END_DATE
    )

    # --------------------------------------------------------
    # Options
    # --------------------------------------------------------

    collect_options(
        START_DATE,
        END_DATE
    )

    print(
        "\n" +
        "=" * 70
    )

    print(
        "ALL F&O COLLECTION FINISHED"
    )

    print(
        "=" * 70
    )