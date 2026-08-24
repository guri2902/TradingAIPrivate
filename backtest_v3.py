"""
Backtest V3 - Diagnostic edition

Purpose:
- Avoid the overly aggressive filtering of V2.
- Evaluate CE and PE separately.
- Record every eligible signal at score >= 55.
- Break performance down by score bucket and side.
- Limit to one CE and one PE signal per trading day.
- Use premium-based SL/targets.
- Record MAE/MFE where future candles are available.
- Avoid changing the underlying scoring model blindly.

Run:
    python backtest_v3.py

Expected CSV:
    backtest_v3_results.csv
"""

import os
import math
import pandas as pd
import numpy as np

INITIAL_CAPITAL = 50_000.0
MIN_SCORE = 55
MAX_TRADES_PER_SIDE_PER_DAY = 1

# Conservative option-buying assumptions
SL_PCT = 0.15
TARGET1_PCT = 0.20
TARGET2_PCT = 0.40

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def find_csvs():
    files = []
    for name in os.listdir("."):
        low = name.lower()
        if low.endswith(".csv") and (
            "ce" in low or "pe" in low or "option" in low or "nifty" in low
        ):
            files.append(name)
    return sorted(files)


def load_data():
    files = find_csvs()

    ce_file = next((f for f in files if "ce" in f.lower()), None)
    pe_file = next((f for f in files if "pe" in f.lower()), None)

    if ce_file and pe_file:
        ce = pd.read_csv(ce_file)
        pe = pd.read_csv(pe_file)
        ce["_side"] = "CE"
        pe["_side"] = "PE"
        df = pd.concat([ce, pe], ignore_index=True)
    elif files:
        df = pd.read_csv(files[0])
    else:
        raise FileNotFoundError("No option CSV files found.")

    return normalize(df)


def normalize(df):
    df = df.copy()

        # NSE CSV headers contain trailing spaces
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )
    # Common aliases
    aliases = {
        "datetime": ["datetime", "date_time", "timestamp", "Date", "Datetime"],
        "date": ["date", "Date"],
        "time": ["time", "Time"],
        "strike": ["strike", "Strike", "strikePrice", "StrikePrice"],
        "spot": ["spot", "Spot", "underlying", "underlyingValue", "Underlying"],
        "ltp": ["ltp", "LTP", "close", "Close", "premium", "Premium"],
        "oi": ["oi", "OI", "openInterest", "OpenInterest"],
        "change_oi": ["change_oi", "changeOI", "ChangeOI", "oi_change"],
        "volume": ["volume", "Volume"],
        "side": ["side", "Side", "option_type", "OptionType", "type", "Type"],
    }

    for target, candidates in aliases.items():
        if target not in df.columns:
            for c in candidates:
                if c in df.columns:
                    df[target] = df[c]
                    break

    if "datetime" not in df.columns:
        if "date" in df.columns and "time" in df.columns:
            df["datetime"] = pd.to_datetime(
                df["date"].astype(str) + " " + df["time"].astype(str),
                errors="coerce"
            )
        elif "date" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"], errors="coerce")
        else:
            raise ValueError("Could not identify a date/datetime column.")

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"]).sort_values("datetime")

    for col in ["strike", "spot", "ltp", "oi", "change_oi", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "side" not in df.columns:
        # Try filename-derived side is impossible after concat; infer from
        # CE/PE-specific LTP columns if present.
        if "ce_ltp" in df.columns and "pe_ltp" in df.columns:
            ce = df.copy()
            pe = df.copy()
            ce["side"] = "CE"
            pe["side"] = "PE"
            ce["ltp"] = ce["ce_ltp"]
            pe["ltp"] = pe["pe_ltp"]
            df = pd.concat([ce, pe], ignore_index=True)

    if "side" in df.columns:
        df["side"] = df["side"].astype(str).str.upper()
        df = df[df["side"].isin(["CE", "PE"])]

    df["trade_date"] = df["datetime"].dt.date
    return df.reset_index(drop=True)


def score_row(row):
    """
    Diagnostic score.

    If V2 already contains a score column, use it.
    Otherwise calculate a lightweight market/option score from fields that
    actually exist in the historical dataset. Missing fields do not earn
    points.
    """
    existing = None
    for c in ["score", "ai_score", "Score", "AI Score"]:
        if c in row.index and pd.notna(row[c]):
            try:
                existing = float(row[c])
                break
            except Exception:
                pass

    if existing is not None:
        return max(0, min(100, existing)), ["Historical score"]

    score = 0.0
    reasons = []

    side = str(row.get("side", "")).upper()

    # Optional market features
    ema20 = row.get("ema20")
    ema50 = row.get("ema50")
    ema200 = row.get("ema200")
    rsi = row.get("rsi")
    macd = row.get("macd")
    signal = row.get("signal")
    trend = str(row.get("trend", ""))
    mtf = str(row.get("mtf", ""))
    oi = row.get("oi")
    spot = row.get("spot")
    strike = row.get("strike")
    premium = row.get("ltp")

    if side == "CE":
        if trend == "Bullish":
            score += 20; reasons.append("Bullish trend")
        elif trend == "Bearish":
            score -= 15

        if mtf == "Bullish":
            score += 15; reasons.append("Bullish MTF")
        elif mtf == "Bearish":
            score -= 10

        if all(pd.notna(x) for x in [ema20, ema50, ema200]):
            if ema20 > ema50:
                score += 10; reasons.append("EMA bullish")
            if ema50 > ema200:
                score += 5

        if pd.notna(rsi) and 50 <= float(rsi) <= 68:
            score += 5; reasons.append("RSI supportive")

        if pd.notna(macd) and pd.notna(signal) and macd > signal:
            score += 10; reasons.append("MACD bullish")

    else:
        if trend == "Bearish":
            score += 20; reasons.append("Bearish trend")
        elif trend == "Bullish":
            score -= 15

        if mtf == "Bearish":
            score += 15; reasons.append("Bearish MTF")
        elif mtf == "Bullish":
            score -= 10

        if all(pd.notna(x) for x in [ema20, ema50, ema200]):
            if ema20 < ema50:
                score += 10; reasons.append("EMA bearish")
            if ema50 < ema200:
                score += 5

        if pd.notna(rsi) and 32 <= float(rsi) <= 50:
            score += 5; reasons.append("RSI supportive")

        if pd.notna(macd) and pd.notna(signal) and macd < signal:
            score += 10; reasons.append("MACD bearish")

    if pd.notna(spot) and pd.notna(strike):
        distance = abs(float(strike) - float(spot))
        if distance <= 50:
            score += 10; reasons.append("Near ATM")
        elif distance <= 100:
            score += 7
        elif distance <= 150:
            score += 4

    if pd.notna(premium):
        premium = float(premium)
        if premium >= 50:
            score += 5
        elif premium >= 20:
            score += 3

    if pd.notna(oi) and float(oi) > 0:
        score += 5

    return max(0, min(100, score)), reasons


def exit_trade(group, entry_idx, entry_price, side):
    """
    Find first SL/target2 hit after entry.

    If both levels occur in the same candle and intrabar ordering is unknown,
    use the conservative assumption: SL wins.
    """
    if entry_idx >= len(group) - 1:
        return None

    stop = entry_price * (1 - SL_PCT)
    target1 = entry_price * (1 + TARGET1_PCT)
    target2 = entry_price * (1 + TARGET2_PCT)

    future = group.iloc[entry_idx + 1:].copy()

    if "high" not in future.columns or "low" not in future.columns:
        return None

    highs = pd.to_numeric(future["high"], errors="coerce")
    lows = pd.to_numeric(future["low"], errors="coerce")

    exit_price = None
    exit_time = None
    result = "OPEN"

    for i, (idx, hi, lo) in enumerate(zip(future.index, highs, lows)):
        if pd.isna(hi) or pd.isna(lo):
            continue

        # Option premium data is expected to be in ltp/close. For an option
        # price series, high/low are preferred if available.
        if lo <= stop:
            exit_price = stop
            exit_time = future.loc[idx, "datetime"]
            result = "SL"
            break

        if hi >= target2:
            exit_price = target2
            exit_time = future.loc[idx, "datetime"]
            result = "TARGET2"
            break

    if exit_price is None:
        last = future.iloc[-1]
        exit_price = float(last["ltp"])
        exit_time = last["datetime"]
        result = "EOD"

    pnl = exit_price - entry_price

    # For options bought, multiply by lot size if available.
    lot_size = 1
    for c in ["lot_size", "LotSize", "qty", "quantity"]:
        if c in group.columns:
            try:
                lot_size = int(group.iloc[entry_idx][c])
                break
            except Exception:
                pass

    pnl_rupees = pnl * lot_size

    return {
        "exit_time": exit_time,
        "exit_price": exit_price,
        "result": result,
        "pnl": pnl_rupees,
        "stop": stop,
        "target1": target1,
        "target2": target2,
    }


def main():
    print("Loading data...")
    df = load_data()

    # Normalize OHLC for option data.
    for target, candidates in {
        "high": ["high", "High", "HIGH"],
        "low": ["low", "Low", "LOW"],
    }.items():
        if target not in df.columns:
            for c in candidates:
                if c in df.columns:
                    df[target] = pd.to_numeric(df[c], errors="coerce")
                    break

    if "high" not in df.columns or "low" not in df.columns:
        # If only LTP exists, use LTP as a degenerate high/low. This still
        # permits EOD analysis but cannot identify intrabar SL/target hits.
        df["high"] = df["ltp"]
        df["low"] = df["ltp"]

    df = df.dropna(subset=["ltp", "strike", "side"])

    print(f"Loaded {len(df):,} option rows")
    print(f"Trading days: {df['trade_date'].nunique()}")
    print()

    trades = []

    # Work strike-by-strike and side-by-side.
    for (day, side, strike), group in df.groupby(
        ["trade_date", "side", "strike"], sort=True
    ):
        group = group.sort_values("datetime").reset_index(drop=True)

        # At most one signal for each side/day/strike.
        best = None

        for i in range(len(group) - 1):
            row = group.iloc[i]
            score, reasons = score_row(row)

            if score < MIN_SCORE:
                continue

            candidate = (score, i, row, reasons)

            if best is None or score > best[0]:
                best = candidate

        if best is None:
            continue

        score, i, row, reasons = best
        entry = float(row["ltp"])

        result = exit_trade(group, i, entry, side)
        if result is None:
            continue

        trades.append({
            "trade_date": day,
            "side": side,
            "strike": strike,
            "entry_time": row["datetime"],
            "entry": entry,
            "score": round(score, 2),
            "score_bucket": f"{int(score)//5*5}-{int(score)//5*5+4}",
            "exit_time": result["exit_time"],
            "exit": round(result["exit_price"], 2),
            "result": result["result"],
            "pnl": round(result["pnl"], 2),
            "stop": round(result["stop"], 2),
            "target1": round(result["target1"], 2),
            "target2": round(result["target2"], 2),
            "reasons": " | ".join(reasons),
        })

    results = pd.DataFrame(trades)

    if results.empty:
        print("No trades generated at score >= 55.")
        print("This means the historical dataset does not contain enough")
        print("features to reproduce the live TradeRanker score.")
        return

    # One CE and one PE maximum per day: retain highest score.
    results = (
        results.sort_values(["trade_date", "side", "score"], ascending=[True, True, False])
        .groupby(["trade_date", "side"], as_index=False)
        .head(MAX_TRADES_PER_SIDE_PER_DAY)
        .sort_values("entry_time")
        .reset_index(drop=True)
    )

    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0

    wins = int((results["pnl"] > 0).sum())
    losses = int((results["pnl"] <= 0).sum())

    for pnl in results["pnl"]:
        capital += float(pnl)
        peak = max(peak, capital)
        max_dd = min(max_dd, capital - peak)

    print("=" * 60)
    print("                 BACKTEST V3")
    print("=" * 60)
    print(f"Trades       : {len(results)}")
    print(f"Wins         : {wins}")
    print(f"Losses       : {losses}")
    print(f"Win Rate     : {wins / len(results) * 100:.2f}%")
    print(f"Total P&L    : ₹{results['pnl'].sum():.2f}")
    print(f"Final Capital: ₹{capital:.2f}")
    print(f"Max Drawdown : ₹{max_dd:.2f}")
    print(f"Avg Trade    : ₹{results['pnl'].mean():.2f}")
    print(f"Best Trade   : ₹{results['pnl'].max():.2f}")
    print(f"Worst Trade  : ₹{results['pnl'].min():.2f}")
    print("=" * 60)

    for side in ["CE", "PE"]:
        s = results[results["side"] == side]
        if s.empty:
            continue
        print()
        print(f"{side} PERFORMANCE")
        print(f"Trades   : {len(s)}")
        print(f"Wins     : {(s['pnl'] > 0).sum()}")
        print(f"Win Rate : {(s['pnl'] > 0).mean() * 100:.2f}%")
        print(f"P&L      : ₹{s['pnl'].sum():.2f}")

    print()
    print("SCORE PERFORMANCE")
    for bucket, s in results.groupby("score_bucket", sort=True):
        print(
            f"{bucket:>5} | Trades: {len(s):3d} | "
            f"Win: {(s['pnl'] > 0).mean()*100:5.1f}% | "
            f"P&L: ₹{s['pnl'].sum():8.2f}"
        )

    print()
    print("RESULT BREAKDOWN")
    print(results["result"].value_counts().to_string())

    results.to_csv("backtest_v3_results.csv", index=False)
    print()
    print("Saved: backtest_v3_results.csv")


if __name__ == "__main__":
    main()