# ============================================================
# TradingAI - UNIFIED DATA TEST
# ============================================================

from datetime import date

from data_engine.unified_data import UnifiedMarketData


print("=" * 70)
print("TradingAI - UNIFIED MARKET DATA TEST")
print("=" * 70)


market = UnifiedMarketData()


# ============================================================
# TEST 1 - EOD2 STOCK
# ============================================================

print("\n")
print("=" * 70)
print("TEST 1 - EOD2 RELIANCE")
print("=" * 70)

df = market.get_stock_history(
    symbol="RELIANCE",
    from_date=date(2025, 1, 1),
    to_date=date(2026, 8, 14),
    source="eod2"
)

print("\nRows:", len(df))
print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 3:")
print(df.head(3))

print("\nLast 3:")
print(df.tail(3))


# ============================================================
# TEST 2 - JUGAAD STOCK
# ============================================================

print("\n")
print("=" * 70)
print("TEST 2 - JUGAAD RELIANCE")
print("=" * 70)

df_jugaad = market.get_stock_history(
    symbol="RELIANCE",
    from_date=date(2026, 8, 1),
    to_date=date(2026, 8, 17),
    source="jugaad"
)

print("\nRows:", len(df_jugaad))

print("\nColumns:")
print(df_jugaad.columns.tolist())

print("\nFirst 3:")
print(df_jugaad.head(3))


# ============================================================
# TEST 3 - NSE INDEX
# ============================================================

print("\n")
print("=" * 70)
print("TEST 3 - NSE NIFTY 50")
print("=" * 70)

nifty = market.get_index_history_nse(
    symbol="NIFTY 50",
    from_date=date(2026, 8, 1),
    to_date=date(2026, 8, 17)
)

print("\nRows:", len(nifty))

print("\nColumns:")
print(nifty.columns.tolist())

print("\nFirst 3:")
print(nifty.head(3))

print("\nLast 3:")
print(nifty.tail(3))


# ============================================================
# TEST 4 - NSE OPTION CHAIN
# ============================================================

print("\n")
print("=" * 70)
print("TEST 4 - NIFTY OPTION CHAIN")
print("=" * 70)

options = market.get_option_chain(
    symbol="NIFTY"
)

print("\nRows:", len(options))

print("\nColumns:")
print(options.columns.tolist())

print("\nFirst 5:")
print(options.head(5))


# ============================================================
# COMPLETE
# ============================================================

print("\n")
print("=" * 70)
print("UNIFIED DATA TEST COMPLETE")
print("=" * 70)