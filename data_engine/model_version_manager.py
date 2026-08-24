# ============================================================
# TradingAI - MODEL VERSION MANAGER
# ============================================================

import json
import shutil
from datetime import datetime
from pathlib import Path


class ModelVersionManager:

    def __init__(
        self,
        model_dir="market_data/models",
        version_dir="market_data/models/versions",
    ):

        self.model_dir = Path(
            model_dir
        )

        self.version_dir = Path(
            version_dir
        )

        self.model_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.version_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.registry_file = (
            self.version_dir
            / "model_registry.json"
        )

    # ========================================================
    # MODEL FILES
    # ========================================================

    def discover_model_files(self):

        files = []

        for path in self.model_dir.iterdir():

            if not path.is_file():
                continue

            name = path.name

            if (
                name.startswith("direction_model")
                or name.startswith("regime_model")
                or name.startswith("volatility_model")
                or name.startswith("option_movement_model")
            ):

                if "backup" in name:
                    continue

                files.append(path)

        return sorted(
            files,
            key=lambda x: x.name,
        )

    # ========================================================
    # REGISTRY
    # ========================================================

    def load_registry(self):

        if not self.registry_file.exists():

            return {
                "active_version": None,
                "versions": [],
            }

        try:

            with open(
                self.registry_file,
                "r",
                encoding="utf-8",
            ) as file:

                registry = json.load(file)

            if not isinstance(
                registry,
                dict,
            ):

                return {
                    "active_version": None,
                    "versions": [],
                }

            registry.setdefault(
                "active_version",
                None,
            )

            registry.setdefault(
                "versions",
                [],
            )

            return registry

        except Exception:

            return {
                "active_version": None,
                "versions": [],
            }

    def save_registry(
        self,
        registry,
    ):

        with open(
            self.registry_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                registry,
                file,
                indent=4,
            )

    # ========================================================
    # CREATE VERSION
    # ========================================================

    def create_version(
        self,
        version_name=None,
        metrics=None,
    ):

        model_files = (
            self.discover_model_files()
        )

        if not model_files:

            raise RuntimeError(
                "No model files found."
            )

        timestamp = (
            datetime.now()
            .strftime("%Y%m%d_%H%M%S")
        )

        if not version_name:

            version_name = (
                f"v_{timestamp}"
            )

        version_path = (
            self.version_dir
            / version_name
        )

        if version_path.exists():

            raise FileExistsError(
                f"Version already exists: "
                f"{version_path}"
            )

        version_path.mkdir(
            parents=True,
            exist_ok=False,
        )

        copied_files = []

        for model_file in model_files:

            destination = (
                version_path
                / model_file.name
            )

            shutil.copy2(
                model_file,
                destination,
            )

            copied_files.append(
                model_file.name
            )

            # Copy related metadata if present.
            metadata_candidates = [
                model_file.with_name(
                    f"{model_file.stem}_features.parquet"
                ),
                model_file.with_name(
                    f"{model_file.stem}_metadata.json"
                ),
            ]

            for metadata in (
                metadata_candidates
            ):

                if metadata.exists():

                    shutil.copy2(
                        metadata,
                        version_path
                        / metadata.name,
                    )

                    copied_files.append(
                        metadata.name
                    )
                    copied_files = list(
                        dict.fromkeys(
                            copied_files
                        )
                    )
        metadata = {
            "version": version_name,
            "created_at":
                datetime.now().isoformat(),
            "models": copied_files,
            "metrics":
                metrics or {},
        }

        with open(
            version_path
            / "version_metadata.json",
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
            )

        registry = (
            self.load_registry()
        )

        registry[
            "versions"
        ].append(
            metadata
        )

        self.save_registry(
            registry
        )

        return {
            "version":
                version_name,
            "path":
                str(version_path),
            "models":
                copied_files,
        }

    # ========================================================
    # VALIDATE VERSION
    # ========================================================

    def validate_version(
        self,
        version_name,
    ):

        version_path = (
            self.version_dir
            / version_name
        )

        if not version_path.exists():

            return {
                "valid": False,
                "reason":
                    "VERSION_NOT_FOUND",
            }

        metadata_file = (
            version_path
            / "version_metadata.json"
        )

        if not metadata_file.exists():

            return {
                "valid": False,
                "reason":
                    "VERSION_METADATA_MISSING",
            }

        try:

            with open(
                metadata_file,
                "r",
                encoding="utf-8",
            ) as file:

                metadata = json.load(
                    file
                )

        except Exception:

            return {
                "valid": False,
                "reason":
                    "INVALID_METADATA",
            }

        missing = []

        for model_name in metadata.get(
            "models",
            [],
        ):

            model_file = (
                version_path
                / model_name
            )

            if not model_file.exists():

                missing.append(
                    model_name
                )

        if missing:

            return {
                "valid": False,
                "reason":
                    "MISSING_MODEL_FILES",
                "missing":
                    missing,
            }

        return {
            "valid": True,
            "reason":
                "VERSION_VALID",
            "metadata":
                metadata,
        }

    # ========================================================
    # ACTIVATE VERSION
    # ========================================================

    def activate_version(
        self,
        version_name,
    ):

        validation = (
            self.validate_version(
                version_name
            )
        )

        if not validation[
            "valid"
        ]:

            raise RuntimeError(
                f"Cannot activate version: "
                f"{validation}"
            )

        version_path = (
            self.version_dir
            / version_name
        )

        # ----------------------------------------------------
        # Backup current live models
        # ----------------------------------------------------

        backup_timestamp = (
            datetime.now()
            .strftime("%Y%m%d_%H%M%S")
        )

        live_backup = (
            self.version_dir
            / f"live_backup_{backup_timestamp}"
        )

        live_backup.mkdir(
            parents=True,
            exist_ok=False,
        )

        for live_file in (
            self.discover_model_files()
        ):

            shutil.copy2(
                live_file,
                live_backup
                / live_file.name,
            )

        # ----------------------------------------------------
        # Copy version into live model directory
        # ----------------------------------------------------

        for version_file in (
            version_path.iterdir()
        ):

            if not version_file.is_file():
                continue

            if version_file.name in (
                "version_metadata.json",
            ):

                continue

            destination = (
                self.model_dir
                / version_file.name
            )

            shutil.copy2(
                version_file,
                destination,
            )

        # ----------------------------------------------------
        # Update active version
        # ----------------------------------------------------

        registry = (
            self.load_registry()
        )

        registry[
            "active_version"
        ] = version_name

        registry[
            "last_activation"
        ] = {
            "version":
                version_name,
            "timestamp":
                datetime.now().isoformat(),
            "backup":
                str(live_backup),
        }

        self.save_registry(
            registry
        )

        return {
            "activated": True,
            "version":
                version_name,
            "backup":
                str(live_backup),
        }

    # ========================================================
    # ROLLBACK
    # ========================================================

    def rollback(
        self,
        backup_path,
    ):

        backup = Path(
            backup_path
        )

        if not backup.exists():

            raise FileNotFoundError(
                f"Backup not found: "
                f"{backup}"
            )

        restored = []

        for backup_file in (
            backup.iterdir()
        ):

            if not backup_file.is_file():
                continue

            destination = (
                self.model_dir
                / backup_file.name
            )

            shutil.copy2(
                backup_file,
                destination,
            )

            restored.append(
                backup_file.name
            )

        return {
            "rolled_back": True,
            "restored":
                restored,
        }

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        registry = (
            self.load_registry()
        )

        return {
            "active_version":
                registry.get(
                    "active_version"
                ),

            "version_count":
                len(
                    registry.get(
                        "versions",
                        [],
                    )
                ),

            "registry":
                registry,
        }