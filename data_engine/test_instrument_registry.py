# ============================================================
# TradingAI - INSTRUMENT REGISTRY TEST
# ============================================================

from data_engine.instrument_registry import (
    InstrumentConfig,
    InstrumentRegistry,
)


print("=" * 70)
print("TradingAI - INSTRUMENT REGISTRY TEST")
print("=" * 70)


registry = InstrumentRegistry()


# ============================================================
# TEST 1 - AVAILABLE INSTRUMENTS
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - AVAILABLE INSTRUMENTS")
print("=" * 70)

symbols = registry.symbols()

print(
    "Symbols:",
    symbols,
)

if not symbols:

    raise RuntimeError(
        "Instrument registry is empty."
    )


# ============================================================
# TEST 2 - NIFTY
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - NIFTY MAPPING")
print("=" * 70)

nifty = registry.get(
    "NIFTY"
)

print(
    nifty
)

if nifty.option_underlying != "NIFTY":

    raise RuntimeError(
        "NIFTY option mapping is incorrect."
    )

if nifty.futures_underlying != "NIFTY":

    raise RuntimeError(
        "NIFTY futures mapping is incorrect."
    )


# ============================================================
# TEST 3 - RELIANCE
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - RELIANCE MAPPING")
print("=" * 70)

reliance = registry.get(
    "reliance"
)

print(
    reliance
)

if reliance.market_symbol != "RELIANCE":

    raise RuntimeError(
        "RELIANCE market mapping is incorrect."
    )


# ============================================================
# TEST 4 - RELATIONSHIP VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - RELATIONSHIP VALIDATION")
print("=" * 70)

valid = registry.validate_relationship(
    market_symbol="NIFTY",
    option_underlying="NIFTY",
    futures_underlying="NIFTY",
)

print(
    f"Valid relationship: {valid}"
)

if not valid:

    raise RuntimeError(
        "Valid relationship was rejected."
    )


# ============================================================
# TEST 5 - INVALID RELATIONSHIP
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - INVALID RELATIONSHIP")
print("=" * 70)

try:

    registry.validate_relationship(
        market_symbol="RELIANCE",
        option_underlying="NIFTY",
        futures_underlying="RELIANCE",
    )

except ValueError as exc:

    print(
        f"Correctly rejected: {exc}"
    )

else:

    raise RuntimeError(
        "Invalid instrument relationship was accepted."
    )


# ============================================================
# TEST 6 - CUSTOM REGISTRATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 6 - CUSTOM INSTRUMENT")
print("=" * 70)

custom = InstrumentConfig(
    symbol="SBIN",
    display_name="STATE BANK OF INDIA",
    market_symbol="SBIN",
    market_source="eod2",
    option_underlying="SBIN",
    futures_underlying="SBIN",
    segment="EQUITY",
    asset_type="STOCK",
)

registry.register(
    custom
)

print(
    registry.get(
        "SBIN"
    )
)

if not registry.exists(
    "SBIN"
):

    raise RuntimeError(
        "Custom instrument was not registered."
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("INSTRUMENT REGISTRY TEST PASSED")
print("=" * 70)