from datetime import date

from data_engine.market_data import MarketData
from data_engine.normalizer import MarketDataNormalizer


def main():

    print("=" * 70)
    print("TradingAI - MARKET DATA NORMALIZER TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Get raw Jugaad data
    # --------------------------------------------------------

    market = MarketData()

    raw = market.get_index_history(
        symbol="NIFTY 50",
        from_date=date(2025, 1, 1),
        to_date=date(2026, 8, 17)
    )

    print("\nRaw rows:", len(raw))

    print("\nRaw columns:")
    print(list(raw.columns))

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    normalizer = MarketDataNormalizer()

    normalized = normalizer.normalize(
        raw,
        symbol="NIFTY 50",
        source="jugaad"
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("NORMALIZED DATA")
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

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    expected = [
        "timestamp",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "oi",
        "source",
    ]

    assert list(normalized.columns) == expected

    assert len(normalized) == len(raw)

    assert (
        normalized["open"]
        .notna()
        .all()
    )

    assert (
        normalized["high"]
        .notna()
        .all()
    )

    assert (
        normalized["low"]
        .notna()
        .all()
    )

    assert (
        normalized["close"]
        .notna()
        .all()
    )

    assert (
        normalized["source"]
        .eq("jugaad")
        .all()
    )

    print("\n" + "=" * 70)
    print("NORMALIZATION TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()