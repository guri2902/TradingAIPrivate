from datetime import date

from data_engine.market_data import MarketData


def main():

    print("=" * 70)
    print("TradingAI - UNIFIED MARKET DATA TEST")
    print("=" * 70)

    market = MarketData()

    # ========================================================
    # TEST NIFTY
    # ========================================================

    print("\nTesting NIFTY 50...")

    nifty = market.get_index_history(
        symbol="NIFTY 50",
        from_date=date(2025, 1, 1),
        to_date=date(2026, 8, 17)
    )

    print("\n" + "=" * 70)
    print("NIFTY RESULT")
    print("=" * 70)

    print("\nRows:", len(nifty))

    print("\nColumns:")
    print(list(nifty.columns))

    print("\nFirst 5:")
    print(nifty.head())

    print("\nLast 5:")
    print(nifty.tail())

    # ========================================================
    # SAVE
    # ========================================================

    market.save(
        nifty,
        "nifty_test.csv"
    )

    print("\n" + "=" * 70)
    print("UNIFIED MARKET DATA TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()