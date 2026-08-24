# ============================================================
# TradingAI - PARQUET STORE TEST
# ============================================================

import pandas as pd

from data_engine.parquet_store import ParquetStore


print("=" * 70)
print("TradingAI - PARQUET STORE TEST")
print("=" * 70)


# ============================================================
# CREATE TEST DATA
# ============================================================

df = pd.DataFrame({

    "timestamp": pd.date_range(
        "2026-08-17",
        periods=5,
        freq="D"
    ),

    "symbol": [
        "NIFTY",
        "NIFTY",
        "NIFTY",
        "NIFTY",
        "NIFTY"
    ],

    "close": [
        24000.0,
        24100.0,
        24200.0,
        24150.0,
        24300.0
    ],

    "volume": [
        100000,
        120000,
        150000,
        130000,
        160000
    ]
})


print("\nTEST DATA")
print(df)


# ============================================================
# STORE
# ============================================================

store = ParquetStore(
    "market_data/processed"
)


# ============================================================
# SAVE
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - SAVE")
print("=" * 70)

path = store.save(
    df,
    "test_nifty"
)

print(
    f"Saved path: {path}"
)


# ============================================================
# EXISTS
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - EXISTS")
print("=" * 70)

print(
    "Exists:",
    store.exists("test_nifty")
)


# ============================================================
# LOAD
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - LOAD")
print("=" * 70)

loaded = store.load(
    "test_nifty"
)

print(loaded)


# ============================================================
# VALIDATE
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - VALIDATION")
print("=" * 70)

assert len(loaded) == len(df)

assert list(loaded.columns) == list(
    df.columns
)

assert loaded["symbol"].tolist() == \
       df["symbol"].tolist()

assert loaded["close"].tolist() == \
       df["close"].tolist()

print("Data integrity: OK")


# ============================================================
# LIST
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - LIST DATASETS")
print("=" * 70)

print(
    store.list_datasets()
)


print("\n" + "=" * 70)
print("PARQUET STORE TEST PASSED")
print("=" * 70)