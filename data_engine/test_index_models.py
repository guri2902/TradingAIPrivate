# ============================================================
# TradingAI - NIFTY INDEX MODELS TEST
# ============================================================

from pathlib import Path
import json
import pickle

import pandas as pd


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

MODEL_DIR = (
    BASE_DIR
    / "market_data"
    / "models"
)


MODELS = [
    {
        "name": "DIRECTION",
        "model": "index_direction_model.pkl",
        "features": (
            "index_direction_model_features.parquet"
        ),
        "metadata": (
            "index_direction_model_metadata.json"
        ),
    },
    {
        "name": "REGIME",
        "model": "index_regime_model.pkl",
        "features": (
            "index_regime_model_features.parquet"
        ),
        "metadata": (
            "index_regime_model_metadata.json"
        ),
    },
    {
        "name": "VOLATILITY",
        "model": "index_volatility_model.pkl",
        "features": (
            "index_volatility_model_features.parquet"
        ),
        "metadata": (
            "index_volatility_model_metadata.json"
        ),
    },
]


print("=" * 70)
print(
    "TradingAI - NIFTY INDEX MODELS TEST"
)
print("=" * 70)


# ============================================================
# TEST 1 - FILES
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - MODEL FILES")
print("=" * 70)

for config in MODELS:

    for key in (
        "model",
        "features",
        "metadata",
    ):

        path = (
            MODEL_DIR
            / config[key]
        )

        if not path.exists():

            raise RuntimeError(
                f"Missing {config['name']} "
                f"{key}: {path}"
            )

        print(
            f"{config['name']} "
            f"{key}: OK"
        )


# ============================================================
# TEST 2 - LOAD MODELS
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - LOAD MODELS")
print("=" * 70)

loaded = {}

for config in MODELS:

    model_path = (
        MODEL_DIR
        / config["model"]
    )

    feature_path = (
        MODEL_DIR
        / config["features"]
    )

    metadata_path = (
        MODEL_DIR
        / config["metadata"]
    )

    with open(
        model_path,
        "rb",
    ) as file:

        model = (
            pickle.load(
                file
            )
        )

    feature_df = (
        pd.read_parquet(
            feature_path
        )
    )

    with open(
        metadata_path,
        "r",
        encoding="utf-8",
    ) as file:

        metadata = json.load(
            file
        )

    if "feature" not in (
        feature_df.columns
    ):

        raise RuntimeError(
            f"Invalid feature file for "
            f"{config['name']}"
        )

    features = (
        feature_df[
            "feature"
        ]
        .astype(str)
        .tolist()
    )

    loaded[
        config["name"]
    ] = {
        "model": model,
        "features": features,
        "metadata": metadata,
    }

    print(
        f"{config['name']}: "
        f"{len(features)} features"
    )


# ============================================================
# TEST 3 - FEATURE LEAKAGE
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - FEATURE LEAKAGE CHECK")
print("=" * 70)

for name, data in loaded.items():

    forbidden = {
        "future_close",
        "future_return",
        "future_return_5",
        "direction_target",
        "regime_target",
        "volatility_target",
        "total_trades",
        "qty_per_trade",
        "dlv_qty",
    }

    leakage = (
        set(
            data["features"]
        )
        & forbidden
    )

    if leakage:

        raise RuntimeError(
            f"{name} contains forbidden "
            f"features: {sorted(leakage)}"
        )

    print(
        f"{name}: no leakage detected"
    )


# ============================================================
# TEST 4 - METADATA
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 - METADATA")
print("=" * 70)

for name, data in loaded.items():

    metadata = (
        data["metadata"]
    )

    print(
        f"{name}:"
    )

    print(
        f"  Type: "
        f"{metadata.get('model_type')}"
    )

    print(
        f"  Features: "
        f"{metadata.get('feature_count')}"
    )

    print(
        f"  Chronological: "
        f"{metadata.get('chronological_split')}"
    )

    print(
        f"  Leakage protected: "
        f"{metadata.get('leakage_protection')}"
    )


# ============================================================
# TEST 5 - FEATURE CONSISTENCY
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 - FEATURE CONSISTENCY")
print("=" * 70)

feature_sets = [
    set(
        data["features"]
    )
    for data in loaded.values()
]

reference = feature_sets[0]

for index, features in enumerate(
    feature_sets[1:],
    start=2,
):

    if features != reference:

        raise RuntimeError(
            "Index models have "
            "inconsistent feature schemas."
        )

    print(
        f"Model {index}: "
        "feature schema matches"
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print(
    "NIFTY INDEX MODELS TEST PASSED"
)
print("=" * 70)