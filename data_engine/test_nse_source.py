# ============================================================
# TradingAI - NSE SOURCE TEST
# ============================================================

from datetime import date
from pprint import pprint

from data_engine.nse_source import NseSource


print("=" * 70)
print("TradingAI - NSE DATA SOURCE TEST")
print("=" * 70)


source = NseSource(
    "market_data/raw/nse"
)


# ============================================================
# NIFTY HISTORY
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - NIFTY HISTORICAL DATA")
print("=" * 70)

data = source.get_index_history(
    "NIFTY 50",
    date(2026, 8, 1),
    date(2026, 8, 17)
)

print("\nRecords:", len(data))

if data:
    print("\nFirst record:")
    pprint(data[0])

    print("\nLast record:")
    pprint(data[-1])


# ============================================================
# LIVE QUOTE
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - RELIANCE LIVE QUOTE")
print("=" * 70)

quote = source.get_quote(
    "RELIANCE"
)

print(
    "\nQuote keys:",
    list(quote.keys())
)


# ============================================================
# OPTION CHAIN
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - NIFTY OPTION CHAIN")
print("=" * 70)

option_chain = source.get_option_chain(
    "NIFTY"
)

print(
    "\nOption-chain keys:",
    list(option_chain.keys())
)

records = option_chain.get(
    "records",
    {}
)

print(
    "Expiry dates:",
    len(
        records.get(
            "expiryDates",
            []
        )
    )
)

print(
    "Strike records:",
    len(
        records.get(
            "data",
            []
        )
    )
)


# ============================================================
# MARKET STATUS
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - MARKET STATUS")
print("=" * 70)

status = source.get_market_status()

print(
    "\nStatus keys:",
    list(status.keys())
)


print("\n" + "=" * 70)
print("NSE SOURCE TEST COMPLETE")
print("=" * 70)