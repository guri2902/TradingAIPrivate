# ============================================================
# TradingAI - EOD2 SOURCE TEST
# ============================================================

from datetime import date

from data_engine.eod2_source import EOD2Source


EOD2_DIR = (
    "market_data/raw/eod2_data"
)


print("=" * 70)
print("TradingAI - EOD2 DATA TEST")
print("=" * 70)


source = EOD2Source(
    EOD2_DIR
)


# ============================================================
# SYMBOL COUNT
# ============================================================

symbols = source.list_symbols()

print(
    "\nTotal symbols:",
    len(symbols)
)

print(
    "\nFirst 20 symbols:"
)

print(
    symbols[:20]
)


# ============================================================
# TEST STOCK
# ============================================================

symbol = "RELIANCE"

print(
    f"\nTesting {symbol}..."
)

try:

    df = source.get_stock(
        symbol=symbol,
        from_date=date(2025, 1, 1),
        to_date=date(2026, 8, 17)
    )

    print("\n" + "=" * 70)
    print("EOD2 RESULT")
    print("=" * 70)

    print(
        "\nRows:",
        len(df)
    )

    print(
        "\nColumns:"
    )

    print(
        list(df.columns)
    )

    print(
        "\nFirst 5:"
    )

    print(
        df.head()
    )

    print(
        "\nLast 5:"
    )

    print(
        df.tail()
    )

except Exception as e:

    print(
        "\nEOD2 TEST FAILED:"
    )

    print(
        type(e).__name__,
        str(e)
    )


print(
    "\n" + "=" * 70
)

print(
    "EOD2 TEST COMPLETE"
)

print(
    "=" * 70
)