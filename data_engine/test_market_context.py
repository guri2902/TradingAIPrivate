# ============================================================
# TradingAI - MARKET CONTEXT TEST
# ============================================================

from data_engine.market_context import (
    MarketContext,
)


print("=" * 70)
print("TradingAI - MARKET CONTEXT MERGE TEST")
print("=" * 70)


context_engine = MarketContext()


# ============================================================
# TEST 1 - NIFTY
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - NIFTY CONTEXT")
print("=" * 70)

nifty = (
    context_engine.build(
        "NIFTY"
    )
)

context_engine.validate(
    nifty
)

print(
    "Instrument:"
)

print(
    nifty["instrument"]
)

print(
    "\nOPTIONS:"
)

print(
    "Available:",
    nifty["options"]["available"]
)

print(
    "Rows:",
    nifty["options"]["rows"]
)

if nifty["options"]["available"]:

    summary = nifty[
        "options"
    ]["summary"]

    print(
        "Underlying:",
        summary.get(
            "underlying"
        ),
    )

    print(
        "ATM:",
        summary.get(
            "atm_strike"
        ),
    )

    print(
        "PCR:",
        summary.get(
            "put_call_oi_ratio"
        ),
    )

    print(
        "Support:",
        summary.get(
            "support"
        ),
    )

    print(
        "Resistance:",
        summary.get(
            "resistance"
        ),
    )

print(
    "\nFUTURES:"
)

print(
    "Available:",
    nifty["futures"]["available"]
)

print(
    "Reason:",
    nifty["futures"].get(
        "reason"
    ),
)


# ============================================================
# TEST 2 - RELIANCE
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - RELIANCE CONTEXT")
print("=" * 70)

reliance = (
    context_engine.build(
        "RELIANCE"
    )
)

context_engine.validate(
    reliance
)

print(
    "Instrument:"
)

print(
    reliance["instrument"]
)

print(
    "\nOptions available:",
    reliance["options"]["available"]
)

print(
    "Futures available:",
    reliance["futures"]["available"]
)


# ============================================================
# TEST 3 - NO DATA MUST NOT FAKE VALUES
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - MISSING DATA SAFETY")
print("=" * 70)

if not reliance["options"]["available"]:

    print(
        "Options unavailable correctly reported:"
    )

    print(
        reliance["options"]["reason"]
    )

else:

    print(
        "RELIANCE option history is available."
    )

if not reliance["futures"]["available"]:

    print(
        "Futures unavailable correctly reported:"
    )

    print(
        reliance["futures"]["reason"]
    )

else:

    print(
        "RELIANCE futures history is available."
    )


# ============================================================
# TEST 4 - NO CROSS-INSTRUMENT MIXING
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - INSTRUMENT CONSISTENCY")
print("=" * 70)

nifty_instrument = (
    nifty["instrument"]
)

if (
    nifty_instrument[
        "option_underlying"
    ]
    != "NIFTY"
):

    raise RuntimeError(
        "NIFTY option mapping is incorrect."
    )

if (
    nifty_instrument[
        "futures_underlying"
    ]
    != "NIFTY"
):

    raise RuntimeError(
        "NIFTY futures mapping is incorrect."
    )

print(
    "NIFTY derivatives correctly mapped."
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("MARKET CONTEXT TEST PASSED")
print("=" * 70)