import pandas as pd
import numpy as np

# ============================================================
# CONFIG
# ============================================================

CE_FILE = "nifty_ce.csv"
PE_FILE = "nifty_pe.csv"

CAPITAL = 50000
LOT_SIZE = 25

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

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

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
        "Underlying Value",
    ]

    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(
        subset=["Date", "Strike Price", "Close", "Underlying Value"],
        inplace=True,
    )

    return df.sort_values("Date").reset_index(drop=True)


def normalize(df, option_type):
    out = pd.DataFrame()

    out["date"] = df["Date"].dt.normalize()
    out["expiry"] = pd.to_datetime(df["Expiry"], errors="coerce")
    out["strike"] = df["Strike Price"]
    out["open"] = df["Open"]
    out["high"] = df["High"]
    out["low"] = df["Low"]
    out["close"] = df["Close"]
    out["oi"] = df["Open Int"].fillna(0)
    out["change_oi"] = df["Change in OI"].fillna(0)
    out["underlying"] = df["Underlying Value"]
    out["option_type"] = option_type

    return out


# ============================================================
# MARKET INDICATORS
# ============================================================

def market_features(history):
    """
    Calculate only information available up to the current day.
    This is intentionally based on the underlying index history,
    not future prices.
    """

    close = history["underlying"].astype(float)

    if len(close) < 20:
        return None

    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    momentum = close.iloc[-1] - close.iloc[-2]

    latest = float(close.iloc[-1])

    # We don't have index High/Low in the option files,
    # so ATR is not calculated here.
    return {
        "price": latest,
        "ema20": float(ema20.iloc[-1]),
        "ema50": float(ema50.iloc[-1]),
        "ema200": float(ema200.iloc[-1]),
        "rsi": float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else 50.0,
        "macd": float(macd.iloc[-1]),
        "signal": float(signal.iloc[-1]),
        "momentum": float(momentum),
    }


# ============================================================
# TRADE RANKER V2
# ============================================================

def rank_trade_v2(option_type, strike, spot, market, option_row):

    score = 0
    reasons = []
    warnings = []

    # --------------------------------------------------------
    # 1. MARKET DIRECTION — 20
    # --------------------------------------------------------

    ema20 = market["ema20"]
    ema50 = market["ema50"]
    ema200 = market["ema200"]

    if ema20 > ema50 > ema200:

        if option_type == "CE":
            score += 20
            reasons.append("Bullish EMA alignment")
        else:
            warnings.append("Bearish trade against EMA alignment")

    elif ema20 < ema50 < ema200:

        if option_type == "PE":
            score += 20
            reasons.append("Bearish EMA alignment")
        else:
            warnings.append("Bullish trade against EMA alignment")

    else:

        score += 5
        warnings.append("EMA structure not fully aligned")

    # --------------------------------------------------------
    # 2. EMA MOMENTUM — 10
    # --------------------------------------------------------

    if option_type == "CE" and ema20 > ema50:
        score += 10
        reasons.append("EMA momentum bullish")

    elif option_type == "PE" and ema20 < ema50:
        score += 10
        reasons.append("EMA momentum bearish")

    # --------------------------------------------------------
    # 3. RSI — 10
    # --------------------------------------------------------

    rsi = market["rsi"]

    if option_type == "CE":

        if 50 <= rsi <= 68:
            score += 10
            reasons.append("RSI supports bullish momentum")

        elif rsi < 40:
            score -= 5
            warnings.append("RSI weak for CE")

    else:

        if 32 <= rsi <= 50:
            score += 10
            reasons.append("RSI supports bearish momentum")

        elif rsi > 60:
            score -= 5
            warnings.append("RSI strong against PE")

    # --------------------------------------------------------
    # 4. MACD — 10
    # --------------------------------------------------------

    macd = market["macd"]
    signal = market["signal"]

    if option_type == "CE":

        if macd > signal:
            score += 10
            reasons.append("MACD bullish")

        else:
            score -= 5
            warnings.append("MACD bearish")

    else:

        if macd < signal:
            score += 10
            reasons.append("MACD bearish")

        else:
            score -= 5
            warnings.append("MACD bullish")

    # --------------------------------------------------------
    # 5. MOMENTUM — 10
    # --------------------------------------------------------

    momentum = market["momentum"]

    if option_type == "CE" and momentum > 0:
        score += 10
        reasons.append("Underlying momentum bullish")

    elif option_type == "PE" and momentum < 0:
        score += 10
        reasons.append("Underlying momentum bearish")

    else:
        warnings.append("Underlying momentum conflicts")

    # --------------------------------------------------------
    # 6. DELTA PROXY — 10
    #
    # Historical CSV does not contain Greeks.
    # Use moneyness as a conservative proxy instead of inventing
    # historical delta values.
    # --------------------------------------------------------

    distance = abs(strike - spot)

    if distance <= 50:
        score += 10
        reasons.append("Strike close to ATM")

    elif distance <= 100:
        score += 7

    elif distance <= 150:
        score += 4

    else:
        score -= 3
        warnings.append("Strike far from ATM")

    # --------------------------------------------------------
    # 7. OPEN INTEREST — 5
    # --------------------------------------------------------

    oi = float(option_row["oi"])

    if oi > 0:
        score += 5
        reasons.append("Open interest available")

    # --------------------------------------------------------
    # 8. CHANGE IN OI — 10
    #
    # For a buyer, rising OI alone isn't bullish/bearish.
    # We therefore use it only as participation confirmation.
    # --------------------------------------------------------

    change_oi = float(option_row["change_oi"])

    if change_oi > 0:
        score += 10
        reasons.append("Positive change in OI")
    else:
        warnings.append("No positive OI participation")

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    score = max(0, min(100, score))

    # Keep this as a score-derived estimate only.
    probability = round(45 + score * 0.35)
    probability = max(45, min(80, probability))

    return {
        "score": score,
        "probability": probability,
        "reasons": reasons,
        "warnings": warnings,
    }


# ============================================================
# TRADE SIMULATION
# ============================================================

def simulate_trade(entry, high, low, option_type, score):

    stop = entry * (1 - SL_PERCENT)
    target1 = entry * (1 + TARGET1_PERCENT)
    target2 = entry * (1 + TARGET2_PERCENT)

    # Conservative candle assumption:
    # if both SL and target are touched, SL happens first.
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

    pnl_points = exit_price - entry

    return {
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target1": round(target1, 2),
        "target2": round(target2, 2),
        "exit": round(exit_price, 2),
        "pnl_points": round(pnl_points, 2),
        "result": result,
        "score": score,
        "option_type": option_type,
    }


# ============================================================
# BACKTEST
# ============================================================

def run_backtest():

    print("\nLoading data...")

    ce_raw = load_csv(CE_FILE)
    pe_raw = load_csv(PE_FILE)

    ce = normalize(ce_raw, "CE")
    pe = normalize(pe_raw, "PE")

    data = pd.concat([ce, pe], ignore_index=True)

    data.sort_values(
        ["date", "expiry", "strike"],
        inplace=True,
    )

    dates = sorted(data["date"].dropna().unique())

    trades = []

    print(f"Loaded {len(data):,} option rows")
    print(f"Trading days: {len(dates)}")

    # ========================================================
    # EACH TRADING DAY
    # ========================================================

    for i in range(len(dates) - 1):

        date = dates[i]
        next_date = dates[i + 1]

        today = data[data["date"] == date]
        tomorrow = data[data["date"] == next_date]

        if today.empty or tomorrow.empty:
            continue

        # ----------------------------------------------------
        # Nearest expiry
        # ----------------------------------------------------

        expiries = sorted(today["expiry"].dropna().unique())

        if not expiries:
            continue

        expiry = expiries[0]

        today_exp = today[today["expiry"] == expiry]
        tomorrow_exp = tomorrow[tomorrow["expiry"] == expiry]

        if today_exp.empty or tomorrow_exp.empty:
            continue

        # ----------------------------------------------------
        # Underlying history
        #
        # IMPORTANT:
        # Only dates <= current date are used.
        # ----------------------------------------------------

        underlying_daily = (
            data[data["date"] <= date]
            .groupby("date")["underlying"]
            .median()
            .reset_index()
            .sort_values("date")
        )

        market = market_features(underlying_daily)

        if market is None:
            continue

        spot = float(today_exp["underlying"].median())

        # ----------------------------------------------------
        # Candidate strikes
        # ----------------------------------------------------

        strikes = sorted(today_exp["strike"].unique())

        candidate_strikes = [
            s for s in strikes
            if abs(s - spot) <= 100
        ]

        candidates = today_exp[
            today_exp["strike"].isin(candidate_strikes)
        ]

        # ----------------------------------------------------
        # Pick best CE and PE independently
        # ----------------------------------------------------

        for option_type in ["CE", "PE"]:

            opts = candidates[
                candidates["option_type"] == option_type
            ]

            if opts.empty:
                continue

            scored = []

            for _, row in opts.iterrows():

                ranking = rank_trade_v2(
                    option_type=option_type,
                    strike=float(row["strike"]),
                    spot=spot,
                    market=market,
                    option_row=row,
                )

                scored.append((ranking, row))

            scored.sort(
                key=lambda x: x[0]["score"],
                reverse=True,
            )

            ranking, selected = scored[0]

            score = ranking["score"]

            if score < MIN_SCORE:
                continue

            # ------------------------------------------------
            # Same contract next day
            # ------------------------------------------------

            future = tomorrow_exp[
                (tomorrow_exp["strike"] == selected["strike"])
                &
                (tomorrow_exp["option_type"] == option_type)
            ]

            if future.empty:
                continue

            next_row = future.iloc[0]

            entry = float(selected["close"])

            if entry <= 0:
                continue

            trade = simulate_trade(
                entry=entry,
                high=float(next_row["high"]),
                low=float(next_row["low"]),
                option_type=option_type,
                score=score,
            )

            trade.update({

                "date": date,
                "next_date": next_date,
                "expiry": expiry,
                "strike": selected["strike"],
                "spot": spot,

                "rsi": market["rsi"],
                "ema20": market["ema20"],
                "ema50": market["ema50"],
                "ema200": market["ema200"],
                "macd": market["macd"],
                "signal": market["signal"],
                "momentum": market["momentum"],

                "oi": selected["oi"],
                "change_oi": selected["change_oi"],

                "probability": ranking["probability"],
                "reasons": " | ".join(ranking["reasons"]),
                "warnings": " | ".join(ranking["warnings"]),

                "entry_date": date,
                "exit_date": next_date,
            })

            trades.append(trade)

    # ========================================================
    # RESULTS
    # ========================================================

    results = pd.DataFrame(trades)

    if results.empty:
        print("\nNO TRADES FOUND")
        return

    closed = results[
        results["result"] != "OPEN"
    ].copy()

    if closed.empty:
        print("\nNo closed trades.")
        return

    closed["pnl_rupees"] = (
        closed["pnl_points"] * LOT_SIZE
    )

    total_pnl = closed["pnl_rupees"].sum()

    wins = (
        closed["pnl_rupees"] > 0
    ).sum()

    losses = (
        closed["pnl_rupees"] < 0
    ).sum()

    total = len(closed)

    win_rate = wins / total * 100

    closed = closed.sort_values("exit_date")

    closed["equity"] = (
        CAPITAL
        + closed["pnl_rupees"].cumsum()
    )

    closed["peak"] = closed["equity"].cummax()

    closed["drawdown"] = (
        closed["equity"]
        - closed["peak"]
    )

    max_drawdown = closed["drawdown"].min()

    # ========================================================
    # REPORT
    # ========================================================

    print("\n")
    print("=" * 60)
    print("                 BACKTEST V2")
    print("=" * 60)

    print(f"Trades       : {total}")
    print(f"Wins         : {wins}")
    print(f"Losses       : {losses}")
    print(f"Win Rate     : {win_rate:.2f}%")
    print(f"Total P&L    : ₹{total_pnl:.2f}")
    print(f"Final Capital: ₹{closed['equity'].iloc[-1]:.2f}")
    print(f"Max Drawdown : ₹{max_drawdown:.2f}")
    print(f"Avg Trade    : ₹{closed['pnl_rupees'].mean():.2f}")
    print(f"Best Trade   : ₹{closed['pnl_rupees'].max():.2f}")
    print(f"Worst Trade  : ₹{closed['pnl_rupees'].min():.2f}")

    print("=" * 60)

    # ========================================================
    # CE / PE
    # ========================================================

    for option_type in ["CE", "PE"]:

        subset = closed[
            closed["option_type"] == option_type
        ]

        if subset.empty:
            continue

        wins_type = (
            subset["pnl_rupees"] > 0
        ).sum()

        winrate_type = (
            wins_type / len(subset) * 100
        )

        print(f"\n{option_type} PERFORMANCE")
        print(f"Trades   : {len(subset)}")
        print(f"Wins     : {wins_type}")
        print(f"Win Rate : {winrate_type:.2f}%")
        print(f"P&L      : ₹{subset['pnl_rupees'].sum():.2f}")

    # ========================================================
    # SCORE BUCKETS
    # ========================================================

    print("\nSCORE PERFORMANCE")

    bins = [54, 59, 64, 69, 74, 79, 84, 100]
    labels = [
        "55-59",
        "60-64",
        "65-69",
        "70-74",
        "75-79",
        "80-84",
        "85-100",
    ]

    closed["score_bucket"] = pd.cut(
        closed["score"],
        bins=bins,
        labels=labels,
        include_lowest=True,
    )

    score_stats = (
        closed.groupby(
            "score_bucket",
            observed=True,
        )
        .agg(
            trades=("pnl_rupees", "count"),
            wins=("pnl_rupees", lambda x: (x > 0).sum()),
            pnl=("pnl_rupees", "sum"),
        )
        .reset_index()
    )

    for _, row in score_stats.iterrows():

        wr = (
            row["wins"] / row["trades"] * 100
            if row["trades"] else 0
        )

        print(
            f"{row['score_bucket']} | "
            f"Trades: {int(row['trades'])} | "
            f"Win: {wr:.1f}% | "
            f"P&L: ₹{row['pnl']:.2f}"
        )

    # ========================================================
    # SAVE
    # ========================================================

    closed.to_csv(
        "backtest_v2_results.csv",
        index=False,
    )

    print(
        "\nSaved: backtest_v2_results.csv"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    run_backtest()
