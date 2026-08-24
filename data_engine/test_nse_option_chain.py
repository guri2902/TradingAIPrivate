from pathlib import Path

from data_engine.nse_option_chain import (
    NseOptionChain
)


print("=" * 70)
print("TradingAI - NSE OPTION CHAIN TEST")
print("=" * 70)


source = NseOptionChain(
    Path("market_data/raw/nse")
)


try:

    # ========================================================
    # RAW
    # ========================================================

    data = source.get_raw(
        symbol="NIFTY"
    )

    print()
    print("=" * 70)
    print("RAW OPTION CHAIN")
    print("=" * 70)

    records = data.get(
        "records",
        {}
    )

    rows = records.get(
        "data",
        []
    )

    expiries = records.get(
        "expiryDates",
        []
    )

    print(
        f"\nRows: {len(rows)}"
    )

    print(
        f"Expiry dates: {expiries[:10]}"
    )


    # ========================================================
    # NORMALIZE
    # ========================================================

    df = source.normalize(
        data,
        symbol="NIFTY"
    )

    print()
    print("=" * 70)
    print("NORMALIZED OPTION CHAIN")
    print("=" * 70)

    print(
        f"\nRows: {len(df)}"
    )

    print(
        "\nColumns:"
    )

    print(
        df.columns.tolist()
    )

    print(
        "\nFirst 10:"
    )

    print(
        df.head(10).to_string(
            index=False
        )
    )

    print(
        "\nOption types:"
    )

    print(
        df["option_type"]
        .value_counts()
        .to_dict()
    )

    print(
        "\nExpiry:"
    )

    print(
        df["expiry"]
        .unique()
        .tolist()
    )

    print(
        "\nMissing values:"
    )

    print(
        df.isna().sum()
    )


    # ========================================================
    # SAVE
    # ========================================================

    source.save_raw(
        data
    )

    source.save_normalized(
        df
    )


    print()
    print("=" * 70)
    print("NSE OPTION CHAIN TEST PASSED")
    print("=" * 70)


finally:

    source.close()