# ============================================================
# TradingAI - DATA VALIDATOR TEST
# ============================================================

from datetime import date

from data_engine.unified_data import UnifiedMarketData
from data_engine.data_validator import MarketDataValidator


print("=" * 70)
print("TradingAI - DATA VALIDATION TEST")
print("=" * 70)


market = UnifiedMarketData()


# ============================================================
# TEST 1 - EOD2 STOCK
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - EOD2 RELIANCE")
print("=" * 70)

stock = market.get_stock_history(
    symbol="RELIANCE",
    from_date="2026-01-01",
    to_date="2026-08-14",
    source="eod2",
)

result = MarketDataValidator.validate_ohlcv(
    stock,
    symbol="RELIANCE",
)

print("Valid:", result["valid"])
print("Errors:", result["errors"])
print("Warnings:", result["warnings"])

assert result["valid"], result["errors"]


# ============================================================
# TEST 2 - NSE INDEX
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - NSE NIFTY 50")
print("=" * 70)

index = market.get_index_history_nse(
    symbol="NIFTY 50",
    from_date=date(2026, 8, 1),
    to_date=date(2026, 8, 17),
)

result = MarketDataValidator.validate_ohlcv(
    index,
    symbol="NIFTY 50",
)

print("Valid:", result["valid"])
print("Errors:", result["errors"])
print("Warnings:", result["warnings"])

assert result["valid"], result["errors"]


# ============================================================
# TEST 3 - NSE OPTION CHAIN
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - NIFTY OPTION CHAIN")
print("=" * 70)

options = market.get_option_chain(
    symbol="NIFTY"
)

result = MarketDataValidator.validate_option_chain(
    options,
    symbol="NIFTY",
)

print("Valid:", result["valid"])
print("Errors:", result["errors"])
print("Warnings:", result["warnings"])

assert result["valid"], result["errors"]


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("DATA VALIDATION TEST PASSED")
print("=" * 70)