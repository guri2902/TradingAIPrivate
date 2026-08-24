import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

CE_FILE = "nifty_ce.csv"
PE_FILE = "nifty_pe.csv"

CAPITAL = 50000
RISK_PERCENT = 1

SL_PERCENT = 0.15
TARGET1_PERCENT = 0.20
TARGET2_PERCENT = 0.40

MIN_SCORE = 55


# ============================================================
# LOAD DATA
# ============================================================

def load_csv(path):

    df = pd.read_csv(path)

    df.columns = [c.strip() for c in df.columns]

    # Convert dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Numeric columns
    numeric = [
        "Strike Price",
        "Open",
        "High",
        "Low",
        "Close",
        "LTP",
        "No. of contracts",
        "Open Int",
        "Change in OI",
        "Underlying Value"
    ]

    for col in numeric:

        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    df.dropna(
        subset=[
            "Date",
            "Strike Price",
            "Close",
            "Underlying Value"
        ],
        inplace=True
    )

    return df.sort_values("Date").reset_index(drop=True)


# ============================================================
# NORMALIZE OPTION DATA
# ============================================================

def normalize(df, option_type):

    out = pd.DataFrame()

    out["date"] = df["Date"].dt.normalize()

    out["expiry"] = pd.to_datetime(
        df["Expiry"],
        errors="coerce"
    )

    out["strike"] = df["Strike Price"]

    out["open"] = df["Open"]

    out["high"] = df["High"]

    out["low"] = df["Low"]

    out["close"] = df["Close"]

    out["oi"] = df["Open Int"]

    out["change_oi"] = df["Change in OI"]

    out["underlying"] = df["Underlying Value"]

    out["option_type"] = option_type

    return out


# ============================================================
# TRADE SIMULATION
# ============================================================

def simulate_trade(
    entry,
    high,
    low,
    option_type,
    score
):

    stop = entry * (1 - SL_PERCENT)

    target1 = entry * (1 + TARGET1_PERCENT)

    target2 = entry * (1 + TARGET2_PERCENT)

    # --------------------------------------------------------
    # Conservative assumption:
    # If both SL and target occur in same candle,
    # assume SL happened first.
    # --------------------------------------------------------

    if low <= stop:

        exit_price = stop

        result = "LOSS"

    elif high >= target2:

        exit_price = target2

        result = "TARGET2"

    elif high >= target1:

        exit_price = target1

        result = "TARGET1"

    else:

        exit_price = entry

        result = "OPEN"

    pnl = exit_price - entry

    return {

        "entry": round(entry, 2),

        "stop": round(stop, 2),

        "target1": round(target1, 2),

        "target2": round(target2, 2),

        "exit": round(exit_price, 2),

        "pnl_points": round(pnl, 2),

        "result": result,

        "score": score,

        "option_type": option_type
    }


# ============================================================
# BACKTEST
# ============================================================

def run_backtest():

    print("\nLoading data...")

    ce_raw = load_csv(CE_FILE)

    pe_raw = load_csv(PE_FILE)

    ce = normalize(
        ce_raw,
        "CE"
    )

    pe = normalize(
        pe_raw,
        "PE"
    )

    data = pd.concat(
        [ce, pe],
        ignore_index=True
    )

    data.sort_values(
        ["date", "expiry", "strike"],
        inplace=True
    )

    dates = sorted(
        data["date"].dropna().unique()
    )

    trades = []

    print(
        f"Loaded {len(data):,} option rows"
    )

    print(
        f"Trading days: {len(dates)}"
    )

    # ========================================================
    # EACH TRADING DAY
    # ========================================================

    for i in range(len(dates) - 1):

        date = dates[i]

        next_date = dates[i + 1]

        today = data[
            data["date"] == date
        ]

        tomorrow = data[
            data["date"] == next_date
        ]

        if today.empty or tomorrow.empty:
            continue

        # ----------------------------------------------------
        # Use nearest expiry available that day
        # ----------------------------------------------------

        expiries = sorted(
            today["expiry"].dropna().unique()
        )

        if not expiries:
            continue

        expiry = expiries[0]

        today_exp = today[
            today["expiry"] == expiry
        ]

        tomorrow_exp = tomorrow[
            tomorrow["expiry"] == expiry
        ]

        if today_exp.empty:
            continue

        # ----------------------------------------------------
        # Underlying
        # ----------------------------------------------------

        spot = today_exp["underlying"].median()

        # ----------------------------------------------------
        # ATM
        # ----------------------------------------------------

        strikes = sorted(
            today_exp["strike"].unique()
        )

        if not strikes:
            continue

        atm = min(
            strikes,
            key=lambda x: abs(x - spot)
        )

        # ----------------------------------------------------
        # Candidate strikes
        # ----------------------------------------------------

        candidate_strikes = [
            s for s in strikes
            if abs(s - spot) <= 100
        ]

        candidates = today_exp[
            today_exp["strike"].isin(
                candidate_strikes
            )
        ]

        # ----------------------------------------------------
        # Simple initial scoring
        #
        # We intentionally do NOT fake the full live
        # TradeRanker here.
        #
        # This gives us a clean baseline first.
        # ----------------------------------------------------

        for option_type in ["CE", "PE"]:

            opts = candidates[
                candidates["option_type"]
                == option_type
            ]

            if opts.empty:
                continue

            scored = []

            for _, row in opts.iterrows():

                score = 50

                distance = abs(
                    row["strike"] - spot
                )

                # ATM bonus
                if distance <= 50:
                    score += 10

                elif distance <= 100:
                    score += 5

                # OI
                if row["oi"] > 0:
                    score += 5

                # Volume
                if row.get(
                    "change_oi",
                    0
                ) > 0:

                    score += 5

                scored.append(
                    (
                        score,
                        row
                    )
                )

            scored.sort(
                key=lambda x: x[0],
                reverse=True
            )

            score, selected = scored[0]

            if score < MIN_SCORE:
                continue

            # ------------------------------------------------
            # Find same contract next day
            # ------------------------------------------------

            future = tomorrow_exp[
                (tomorrow_exp["strike"]
                 == selected["strike"])
                &
                (tomorrow_exp["option_type"]
                 == option_type)
            ]

            if future.empty:
                continue

            next_row = future.iloc[0]

            entry = float(
                selected["close"]
            )

            if entry <= 0:
                continue

            trade = simulate_trade(

                entry=entry,

                high=float(
                    next_row["high"]
                ),

                low=float(
                    next_row["low"]
                ),

                option_type=option_type,

                score=score
            )

            trade.update({

                "date": date,

                "next_date": next_date,

                "expiry": expiry,

                "strike": selected["strike"],

                "spot": spot,

                "entry_date": date,

                "exit_date": next_date

            })

            trades.append(trade)

    # ========================================================
    # RESULTS
    # ========================================================

    results = pd.DataFrame(trades)

    if results.empty:

        print("\nNO TRADES FOUND")

        return

    # Remove trades that never hit SL/target
    closed = results[
        results["result"] != "OPEN"
    ].copy()

    if closed.empty:

        print("\nNo closed trades.")

        return

    # --------------------------------------------------------
    # P&L
    # --------------------------------------------------------

    closed["pnl_rupees"] = (
        closed["pnl_points"] * 25
    )

    total_pnl = closed[
        "pnl_rupees"
    ].sum()

    wins = (
        closed["pnl_rupees"] > 0
    ).sum()

    losses = (
        closed["pnl_rupees"] < 0
    ).sum()

    total = len(closed)

    win_rate = (
        wins / total * 100
    )

    # --------------------------------------------------------
    # Equity
    # --------------------------------------------------------

    closed = closed.sort_values(
        "exit_date"
    )

    closed["equity"] = (
        CAPITAL
        + closed["pnl_rupees"].cumsum()
    )

    closed["peak"] = (
        closed["equity"].cummax()
    )

    closed["drawdown"] = (
        closed["equity"]
        - closed["peak"]
    )

    max_drawdown = (
        closed["drawdown"].min()
    )

    # ========================================================
    # REPORT
    # ========================================================

    print("\n")
    print("=" * 55)
    print("              BACKTEST RESULTS")
    print("=" * 55)

    print(
        f"Trades       : {total}"
    )

    print(
        f"Wins         : {wins}"
    )

    print(
        f"Losses       : {losses}"
    )

    print(
        f"Win Rate     : {win_rate:.2f}%"
    )

    print(
        f"Total P&L    : ₹{total_pnl:.2f}"
    )

    print(
        f"Final Capital : ₹{closed['equity'].iloc[-1]:.2f}"
    )

    print(
        f"Max Drawdown : ₹{max_drawdown:.2f}"
    )

    print(
        f"Avg Trade    : ₹{closed['pnl_rupees'].mean():.2f}"
    )

    print(
        f"Best Trade   : ₹{closed['pnl_rupees'].max():.2f}"
    )

    print(
        f"Worst Trade  : ₹{closed['pnl_rupees'].min():.2f}"
    )

    print("=" * 55)

    print("\nCE PERFORMANCE")

    ce_trades = closed[
        closed["option_type"] == "CE"
    ]

    if not ce_trades.empty:

        print(
            f"Trades : {len(ce_trades)}"
        )

        print(
            f"P&L    : ₹{ce_trades['pnl_rupees'].sum():.2f}"
        )

    print("\nPE PERFORMANCE")

    pe_trades = closed[
        closed["option_type"] == "PE"
    ]

    if not pe_trades.empty:

        print(
            f"Trades : {len(pe_trades)}"
        )

        print(
            f"P&L    : ₹{pe_trades['pnl_rupees'].sum():.2f}"
        )

    # ========================================================
    # SAVE
    # ========================================================

    closed.to_csv(
        "backtest_results.csv",
        index=False
    )

    print(
        "\nSaved: backtest_results.csv"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    run_backtest()