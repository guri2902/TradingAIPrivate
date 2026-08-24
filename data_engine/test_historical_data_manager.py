# ============================================================
# TradingAI - HISTORICAL DATA MANAGER TEST
# ============================================================

from data_engine.historical_data_manager import (
    HistoricalDataManager
)


print("=" * 70)
print("TradingAI - HISTORICAL DATA MANAGER TEST")
print("=" * 70)


manager = HistoricalDataManager(
    "market_data"
)


# ============================================================
# TEST 1 - STOCK
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - RELIANCE STOCK")
print("=" * 70)

stock = manager.get_stock(
    symbol="RELIANCE",
    from_date="2026-08-01",
    to_date="2026-08-14",
    source="eod2"
)

print(
    f"\nRows: {len(stock)}"
)

print(
    stock[
        [
            "timestamp",
            "symbol",
            "open",
            "high",
            "low",
            "close",
        ]
    ].head()
)


# ============================================================
# TEST 2 - INDEX
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - NIFTY 50 INDEX")
print("=" * 70)

index = manager.get_index(
    symbol="NIFTY 50",
    from_date="2026-08-01",
    to_date="2026-08-17",
    source="nse"
)

print(
    f"\nRows: {len(index)}"
)

print(
    index[
        [
            "timestamp",
            "symbol",
            "open",
            "high",
            "low",
            "close",
        ]
    ].head()
)


# ============================================================
# TEST 3 - OPTION CHAIN
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - NIFTY OPTION CHAIN")
print("=" * 70)

options = manager.get_option_chain(
    symbol="NIFTY"
)

print(
    f"\nRows: {len(options)}"
)

print(
    options[
        [
            "timestamp",
            "symbol",
            "expiry",
            "strike",
            "option_type",
            "last_price",
            "oi",
            "volume",
        ]
    ].head()
)


# ============================================================
# TEST 4 - CACHE
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - CACHE CHECK")
print("=" * 70)

stock_cached = manager.get_stock(
    symbol="RELIANCE",
    from_date="2026-08-01",
    to_date="2026-08-14",
    source="eod2"
)

print(
    f"\nCached rows: {len(stock_cached)}"
)


print("\n" + "=" * 70)
print("HISTORICAL DATA MANAGER TEST COMPLETE")
print("=" * 70)