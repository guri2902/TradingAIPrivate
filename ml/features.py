import numpy as np
import pandas as pd


def build_features(df):

    df = df.copy()

    # ---------------------------------------------------------
    # Normalize column names
    # ---------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["HistoricalDate"],
        errors="coerce"
    )

    for col in ["OPEN", "HIGH", "LOW", "CLOSE"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.sort_values("date").reset_index(drop=True)

    # ---------------------------------------------------------
    # Price returns
    # ---------------------------------------------------------

    df["return_1d"] = (
        df["CLOSE"].pct_change(1)
    )

    df["return_3d"] = (
        df["CLOSE"].pct_change(3)
    )

    df["return_5d"] = (
        df["CLOSE"].pct_change(5)
    )

    df["return_10d"] = (
        df["CLOSE"].pct_change(10)
    )

    # ---------------------------------------------------------
    # Moving averages
    # ---------------------------------------------------------

    df["sma_5"] = (
        df["CLOSE"].rolling(5).mean()
    )

    df["sma_10"] = (
        df["CLOSE"].rolling(10).mean()
    )

    df["sma_20"] = (
        df["CLOSE"].rolling(20).mean()
    )

    df["sma_50"] = (
        df["CLOSE"].rolling(50).mean()
    )

    # ---------------------------------------------------------
    # EMA
    # ---------------------------------------------------------

    df["ema_12"] = (
        df["CLOSE"]
        .ewm(span=12, adjust=False)
        .mean()
    )

    df["ema_26"] = (
        df["CLOSE"]
        .ewm(span=26, adjust=False)
        .mean()
    )

    df["ema_12_distance"] = (
        df["CLOSE"] / df["ema_12"] - 1
    )

    df["ema_26_distance"] = (
        df["CLOSE"] / df["ema_26"] - 1
    )

    # ---------------------------------------------------------
    # RSI
    # ---------------------------------------------------------

    delta = df["CLOSE"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = (
        avg_gain /
        avg_loss.replace(0, np.nan)
    )

    df["rsi"] = (
        100 -
        (100 / (1 + rs))
    )

    # ---------------------------------------------------------
    # MACD
    # ---------------------------------------------------------

    df["macd"] = (
        df["ema_12"] -
        df["ema_26"]
    )

    df["macd_signal"] = (
        df["macd"]
        .ewm(span=9, adjust=False)
        .mean()
    )

    df["macd_hist"] = (
        df["macd"] -
        df["macd_signal"]
    )

    # ---------------------------------------------------------
    # ATR
    # ---------------------------------------------------------

    previous_close = (
        df["CLOSE"].shift(1)
    )

    tr1 = (
        df["HIGH"] -
        df["LOW"]
    )

    tr2 = (
        df["HIGH"] -
        previous_close
    ).abs()

    tr3 = (
        df["LOW"] -
        previous_close
    ).abs()

    true_range = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    df["atr_14"] = (
        true_range
        .rolling(14)
        .mean()
    )

    # ---------------------------------------------------------
    # Volatility
    # ---------------------------------------------------------

    df["volatility_10"] = (
        df["return_1d"]
        .rolling(10)
        .std()
    )

    # ---------------------------------------------------------
    # Candle structure
    # ---------------------------------------------------------

    df["body"] = (
        df["CLOSE"] -
        df["OPEN"]
    )

    df["body_pct"] = (
        df["body"] /
        df["OPEN"]
    )

    df["range"] = (
        df["HIGH"] -
        df["LOW"]
    )

    df["range_pct"] = (
        df["range"] /
        df["OPEN"]
    )

    df["upper_wick"] = (
        df["HIGH"] -
        df[["OPEN", "CLOSE"]].max(axis=1)
    )

    df["lower_wick"] = (
        df[["OPEN", "CLOSE"]].min(axis=1) -
        df["LOW"]
    )

    # ---------------------------------------------------------
    # Target
    # ---------------------------------------------------------

    df["next_close"] = (
        df["CLOSE"].shift(-1)
    )

    df["next_return"] = (
        (
            df["next_close"] /
            df["CLOSE"]
        ) - 1
    ) * 100

    # ---------------------------------------------------------
    # Classification
    #
    # +0.50% = UP
    # -0.50% = DOWN
    # otherwise SIDEWAYS
    # ---------------------------------------------------------

    df["target"] = np.select(
        [
            df["next_return"] >= 0.50,
            df["next_return"] <= -0.50
        ],
        [
            1,
            -1
        ],
        default=0
    )

    return df