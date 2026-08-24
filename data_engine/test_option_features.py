# ============================================================
# TradingAI - OPTION FEATURE ENGINEERING TEST
# ============================================================

from pathlib import Path

import pandas as pd

from data_engine.unified_data import UnifiedMarketData
from data_engine.option_features import (
    OptionFeatureEngineering
)


print("=" * 70)
print("TradingAI - OPTION FEATURE ENGINEERING TEST")
print("=" * 70)


# ============================================================
# LOAD LIVE OPTION CHAIN
# ============================================================

market = UnifiedMarketData()

print("\n" + "=" * 70)
print("TEST 1 - LOAD OPTION CHAIN")
print("=" * 70)

options = market.get_option_chain(
    symbol="NIFTY"
)

print(
    f"Rows: {len(options)}"
)

print(
    f"Columns: {list(options.columns)}"
)


if options.empty:
    raise RuntimeError(
        "Option chain returned no data."
    )


# ============================================================
# BUILD FEATURES
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD OPTION FEATURES")
print("=" * 70)

engine = OptionFeatureEngineering()

features = engine.build_features(
    options
)

print(
    f"Feature rows: {len(features)}"
)

print(
    f"Feature columns: {len(features.columns)}"
)


# ============================================================
# IMPORTANT VALUES
# ============================================================

print("\n" + "=" * 70)
print("MARKET OPTION FEATURES")
print("=" * 70)

print(
    f"ATM Strike: "
    f"{features['atm_strike'].iloc[0]}"
)

print(
    f"Underlying: "
    f"{features['underlying_value'].iloc[0]}"
)

print(
    f"PCR: "
    f"{features['put_call_ratio'].iloc[0]:.4f}"
)

print(
    f"Volume PCR: "
    f"{features['volume_put_call_ratio'].iloc[0]:.4f}"
)

print(
    f"ATM IV Skew: "
    f"{features['atm_iv_skew'].iloc[0]:.4f}"
)

print(
    f"OI Support: "
    f"{features['oi_support'].iloc[0]}"
)

print(
    f"OI Resistance: "
    f"{features['oi_resistance'].iloc[0]}"
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - FEATURE VALIDATION")
print("=" * 70)

expected = [
    "atm_strike",
    "strike_distance",
    "strike_distance_pct",
    "distance_from_atm",
    "moneyness",
    "moneyness_type",
    "bid_ask_spread",
    "bid_ask_spread_pct",
    "bid_ask_imbalance",
    "buy_sell_imbalance",
    "buy_sell_ratio",
    "oi_change_pct",
    "oi_volume_ratio",
    "iv_decimal",
    "put_call_ratio",
    "volume_put_call_ratio",
    "oi_change_put_call_ratio",
    "atm_ce_iv",
    "atm_pe_iv",
    "atm_iv_skew",
    "atm_ce_oi",
    "atm_pe_oi",
    "strike_oi_pct",
    "strike_volume_pct",
    "oi_support",
    "oi_resistance",
    "distance_from_support",
    "distance_from_resistance",
    "max_ce_oi_strike",
    "max_pe_oi_strike",
    "max_ce_volume_strike",
    "max_pe_volume_strike",
]

missing = [
    column
    for column in expected
    if column not in features.columns
]

if missing:

    print(
        f"FAILED - Missing: {missing}"
    )

    raise SystemExit(1)

print(
    "All expected option features present."
)


# ============================================================
# SAMPLE
# ============================================================

print("\n" + "=" * 70)
print("OPTION FEATURE SAMPLE")
print("=" * 70)

sample_columns = [
    "strike",
    "option_type",
    "last_price",
    "oi",
    "volume",
    "iv",
    "atm_strike",
    "strike_distance",
    "put_call_ratio",
    "bid_ask_spread",
    "oi_support",
    "oi_resistance",
]

print(
    features[sample_columns].head(10)
)


# ============================================================
# SAVE
# ============================================================

output_path = Path(
    "market_data/processed/"
    "features_nifty_options.parquet"
)

engine.save_features(
    features,
    output_path
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("OPTION FEATURE ENGINEERING TEST PASSED")
print("=" * 70)