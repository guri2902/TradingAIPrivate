# ============================================================
# TradingAI - MODEL VERSION MANAGER TEST
# ============================================================

from pathlib import Path
import tempfile

from data_engine.model_version_manager import (
    ModelVersionManager,
)


print("=" * 70)
print("TradingAI - MODEL VERSION MANAGER TEST")
print("=" * 70)


# ============================================================
# USE TEMP DIRECTORY
# ============================================================

with tempfile.TemporaryDirectory() as temp_dir:

    root = Path(
        temp_dir
    )

    model_dir = (
        root / "models"
    )

    version_dir = (
        root / "versions"
    )

    model_dir.mkdir()
    version_dir.mkdir()


    # ========================================================
    # TEST 1 - CREATE FAKE CURRENT MODELS
    # ========================================================

    print("\n" + "=" * 70)
    print("TEST 1 - CREATE CURRENT MODEL SET")
    print("=" * 70)

    model_files = [
        "direction_model.pkl",
        "regime_model.pkl",
        "regime_model_features.parquet",
        "volatility_model.pkl",
        "volatility_model_features.parquet",
    ]

    for filename in model_files:

        (
            model_dir
            / filename
        ).write_text(
            f"CURRENT-{filename}",
            encoding="utf-8",
        )

    manager = ModelVersionManager(
        model_dir=model_dir,
        version_dir=version_dir,
    )

    discovered = (
        manager.discover_model_files()
    )

    print(
        "Discovered:",
        [
            p.name
            for p in discovered
        ],
    )

    expected_files = {
        "direction_model.pkl",
        "regime_model.pkl",
        "regime_model_features.parquet",
        "volatility_model.pkl",
        "volatility_model_features.parquet",
    }

    discovered_names = {
        p.name
        for p in discovered
    }

    if discovered_names != expected_files:

        raise RuntimeError(
            "Unexpected model file set.\n"
            f"Expected: {sorted(expected_files)}\n"
            f"Found: {sorted(discovered_names)}"
        )

    # ========================================================
    # TEST 2 - CREATE VERSION
    # ========================================================

    print("\n" + "=" * 70)
    print("TEST 2 - CREATE VERSION")
    print("=" * 70)

    created = (
        manager.create_version(
            version_name="v_1_0_0",
            metrics={
                "accuracy": 0.60,
            },
        )
    )

    print(
        created
    )

    version_path = Path(
        created["path"]
    )

    if not version_path.exists():

        raise RuntimeError(
            "Version directory was not created."
        )


    # ========================================================
    # TEST 3 - VALIDATE
    # ========================================================

    print("\n" + "=" * 70)
    print("TEST 3 - VALIDATE VERSION")
    print("=" * 70)

    validation = (
        manager.validate_version(
            "v_1_0_0"
        )
    )

    print(
        validation
    )

    if not validation[
        "valid"
    ]:

        raise RuntimeError(
            "Created version failed validation."
        )


    # ========================================================
    # TEST 4 - ACTIVATE
    # ========================================================

    print("\n" + "=" * 70)
    print("TEST 4 - ACTIVATE VERSION")
    print("=" * 70)

    activated = (
        manager.activate_version(
            "v_1_0_0"
        )
    )

    print(
        activated
    )

    if not activated[
        "activated"
    ]:

        raise RuntimeError(
            "Version activation failed."
        )

    if not Path(
        activated["backup"]
    ).exists():

        raise RuntimeError(
            "Live model backup was not created."
        )


    # ========================================================
    # TEST 5 - STATUS
    # ========================================================

    print("\n" + "=" * 70)
    print("TEST 5 - REGISTRY STATUS")
    print("=" * 70)

    status = (
        manager.status()
    )

    print(
        status
    )

    if status[
        "active_version"
    ] != "v_1_0_0":

        raise RuntimeError(
            "Active version was not recorded."
        )

    if status[
        "version_count"
    ] != 1:

        raise RuntimeError(
            "Registry version count is incorrect."
        )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("MODEL VERSION MANAGER TEST PASSED")
print("=" * 70)