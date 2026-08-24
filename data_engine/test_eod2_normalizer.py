# ============================================================
# TradingAI - EOD2 NORMALIZER TEST
# ============================================================

from datetime import date

from data_engine.eod2_source import EOD2Source
from data_engine.normalizer import MarketDataNormalizer


EOD2_DIR = "market_data/raw/eod2_data"


print("=" * 70)
print("TradingAI - EOD2 NORMALIZER TEST")
print("=" * 70)


# ============================================================
# LOAD EOD2
# ============================================================

source = EOD2Source(
    EOD2_DIR
)

raw = source.get_stock(
    symbol="RELIANCE",
    from_date=date(2025, 1, 1),
    to_date=date(2026, 8, 17)
)


print("\nRaw rows:", len(raw))

print("\nRaw columns:")
print(list(raw.columns))


# ============================================================
# NORMALIZE
# ============================================================

normalized = MarketDataNormalizer.from_eod2(
    raw,
    symbol="RELIANCE"
)


# ============================================================
# RESULT
# ============================================================

print("\n" + "=" * 70)
print("NORMALIZED EOD2 DATA")
print("=" * 70)

print("\nRows:")
print(len(normalized))

print("\nColumns:")
print(list(normalized.columns))

print("\nFirst 5:")
print(normalized.head())

print("\nLast 5:")
print(normalized.tail())

print("\nData types:")
print(normalized.dtypes)

print("\nMissing values:")
print(normalized.isna().sum())


# ============================================================
# VALIDATION
# ============================================================

required = [
    "timestamp",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "oi",
    "total_trades",
    "qty_per_trade",
    "delivery_qty",
    "series",
    "source",
]

missing_columns = [
    column
    for column in required
    if column not in normalized.columns
]


if missing_columns:

    raise RuntimeError(
        f"Missing normalized columns: {missing_columns}"
    )


if normalized["source"].ne("eod2").any():

    raise RuntimeError(
        "EOD2 source column contains invalid values"
    )


if normalized["symbol"].ne("RELIANCE").any():

    raise RuntimeError(
        "Symbol normalization failed"
    )


print("\n" + "=" * 70)
print("EOD2 NORMALIZATION TEST PASSED")
print("=" * 70)