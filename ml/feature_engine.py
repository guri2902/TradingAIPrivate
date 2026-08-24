import numpy as np
import pandas as pd


# ============================================================
# TradingAI Pro
# Feature Engineering
# ============================================================


def prepare_ohlc(df):
    """
    Normalize NIFTY historical OHLC data.
    """

    df = df.copy()

    # --------------------------------------------------------
    # Find columns regardless of NSE/Jugaad capitalization
    # --------------------------------------------------------

    rename_map = {}

    for col in df.columns:

        c = str(col).strip().lower()

        if c in ("historicaldate", "date", "timestamp", "datetime"):
            rename_map[col] = "timestamp"

        elif c in ("open", "opening_price"):
            rename_map[col] = "open"

        elif c in ("high", "high_price"):
            rename_map[col] = "high"

        elif c in ("low", "low_price"):
            rename_map[col] = "low"

        elif c in ("close", "closing_price"):
            rename_map[col] = "close"

        elif c == "volume":
            rename_map[col] = "volume"

        elif c in ("oi", "open_interest"):
            rename_map[col] = "oi"

    df = df.rename(columns=rename_map)

    required = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
    ]

    missing = [
        x for x in required
        if x not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    for col in ["open", "high", "low", "close"]:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    if "volume" not in df.columns:
        df["volume"] = 0

    if "oi" not in df.columns:
        df["oi"] = 0

    df["volume"] = pd.to_numeric(
        df["volume"],
        errors="coerce"
    ).fillna(0)

    df["oi"] = pd.to_numeric(
        df["oi"],
        errors="coerce"
    ).fillna(0)

    df = df.dropna(
        subset=[
            "timestamp",
            "open",
            "high",
            "low",
            "close"
        ]
    )

    df = df.sort_values("timestamp")
    df = df.drop_duplicates("timestamp")

    return df.reset_index(drop=True)


# ============================================================
# RSI
# ============================================================

def rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        np.nan
    )

    result = 100 - (
        100 / (1 + rs)
    )

    return result.fillna(50)


# ============================================================
# ATR
# ============================================================

def atr(df, period=14):

    previous_close = df["close"].shift(1)

    tr1 = df["high"] - df["low"]

    tr2 = (
        df["high"] -
        previous_close
    ).abs()

    tr3 = (
        df["low"] -
        previous_close
    ).abs()

    true_range = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    return true_range.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()


# ============================================================
# MACD
# ============================================================

def macd(series):

    ema12 = series.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = series.ewm(
        span=26,
        adjust=False
    ).mean()

    macd_line = ema12 - ema26

    signal = macd_line.ewm(
        span=9,
        adjust=False
    ).mean()

    histogram = (
        macd_line -
        signal
    )

    return (
        macd_line,
        signal,
        histogram
    )


# ============================================================
# FEATURE CREATION
# ============================================================

def create_features(df):

    df = prepare_ohlc(df)

    # --------------------------------------------------------
    # Returns
    # --------------------------------------------------------

    df["return_1"] = (
        df["close"]
        .pct_change(1)
    )

    df["return_3"] = (
        df["close"]
        .pct_change(3)
    )

    df["return_5"] = (
        df["close"]
        .pct_change(5)
    )

    df["return_10"] = (
        df["close"]
        .pct_change(10)
    )

    # --------------------------------------------------------
    # Moving averages
    # --------------------------------------------------------

    df["sma_5"] = (
        df["close"]
        .rolling(5)
        .mean()
    )

    df["sma_10"] = (
        df["close"]
        .rolling(10)
        .mean()
    )

    df["sma_20"] = (
        df["close"]
        .rolling(20)
        .mean()
    )

    df["sma_50"] = (
        df["close"]
        .rolling(50)
        .mean()
    )

    # --------------------------------------------------------
    # Distance from moving averages
    # --------------------------------------------------------

    df["dist_sma_5"] = (
        df["close"] /
        df["sma_5"] - 1
    )

    df["dist_sma_20"] = (
        df["close"] /
        df["sma_20"] - 1
    )

    df["dist_sma_50"] = (
        df["close"] /
        df["sma_50"] - 1
    )

    # --------------------------------------------------------
    # EMA
    # --------------------------------------------------------

    df["ema_9"] = (
        df["close"]
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )

    df["ema_21"] = (
        df["close"]
        .ewm(
            span=21,
            adjust=False
        )
        .mean()
    )

    df["ema_gap"] = (
        df["ema_9"] /
        df["ema_21"] - 1
    )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    df["rsi_14"] = rsi(
        df["close"],
        14
    )

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    df["atr_14"] = atr(
        df,
        14
    )

    df["atr_pct"] = (
        df["atr_14"] /
        df["close"]
    )

    # --------------------------------------------------------
    # MACD
    # --------------------------------------------------------

    (
        df["macd"],
        df["macd_signal"],
        df["macd_hist"]
    ) = macd(
        df["close"]
    )

    # --------------------------------------------------------
    # Bollinger Bands
    # --------------------------------------------------------

    bb_mid = (
        df["close"]
        .rolling(20)
        .mean()
    )

    bb_std = (
        df["close"]
        .rolling(20)
        .std()
    )

    df["bb_upper"] = (
        bb_mid +
        2 * bb_std
    )

    df["bb_lower"] = (
        bb_mid -
        2 * bb_std
    )

    df["bb_width"] = (
        df["bb_upper"] -
        df["bb_lower"]
    ) / df["close"]

    df["bb_position"] = (
        df["close"] -
        df["bb_lower"]
    ) / (
        df["bb_upper"] -
        df["bb_lower"]
    ).replace(0, np.nan)

    # --------------------------------------------------------
    # Candle structure
    # --------------------------------------------------------

    df["candle_range"] = (
        df["high"] -
        df["low"]
    )

    df["body"] = (
        df["close"] -
        df["open"]
    )

    df["body_pct"] = (
        df["body"] /
        df["close"]
    )

    df["upper_wick"] = (
        df["high"] -
        df[["open", "close"]].max(axis=1)
    )

    df["lower_wick"] = (
        df[["open", "close"]].min(axis=1) -
        df["low"]
    )

    # --------------------------------------------------------
    # Volume
    # --------------------------------------------------------

    df["volume_ma_20"] = (
        df["volume"]
        .rolling(20)
        .mean()
    )

    df["volume_ratio"] = (
        df["volume"] /
        df["volume_ma_20"].replace(
            0,
            np.nan
        )
    )

    # --------------------------------------------------------
    # Open interest
    # --------------------------------------------------------

    df["oi_change"] = (
        df["oi"]
        .diff()
    )

    df["oi_change_pct"] = (
        df["oi"]
        .pct_change()
    )

    # --------------------------------------------------------
    # Volatility
    # --------------------------------------------------------

    df["volatility_5"] = (
        df["return_1"]
        .rolling(5)
        .std()
    )

    df["volatility_20"] = (
        df["return_1"]
        .rolling(20)
        .std()
    )

    # --------------------------------------------------------
    # Trend score
    # --------------------------------------------------------

    df["trend_score"] = (
        (df["close"] > df["sma_20"]).astype(int)
        +
        (df["sma_5"] > df["sma_20"]).astype(int)
        +
        (df["ema_9"] > df["ema_21"]).astype(int)
    )

    return df


# ============================================================
# TARGET
# ============================================================

def create_target(
    df,
    horizon=3,
    threshold=0.001
):

    df = df.copy()

    future_return = (
        df["close"]
        .shift(-horizon) /
        df["close"] - 1
    )

    # 0 = DOWN
    # 1 = NEUTRAL
    # 2 = UP

    df["target"] = 1

    df.loc[
        future_return > threshold,
        "target"
    ] = 2

    df.loc[
        future_return < -threshold,
        "target"
    ] = 0

    return df