# ============================================================
# TradingAI - RETRAINING MANAGER
# ============================================================

from datetime import datetime
from pathlib import Path
import shutil
import json


class RetrainingManager:

    def __init__(
        self,
        model_dir="market_data/models",
        minimum_training_samples=500,
        minimum_new_samples=100,
    ):

        self.model_dir = Path(
            model_dir
        )

        self.model_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.minimum_training_samples = int(
            minimum_training_samples
        )

        self.minimum_new_samples = int(
            minimum_new_samples
        )

        self.retraining_log = (
            self.model_dir
            / "retraining_log.json"
        )

    # ========================================================
    # SAMPLE CHECK
    # ========================================================

    def check_data(
        self,
        total_samples,
        new_samples,
    ):

        total_samples = int(
            total_samples
        )

        new_samples = int(
            new_samples
        )

        if (
            total_samples
            < self.minimum_training_samples
        ):

            return {
                "eligible": False,
                "reason":
                    "INSUFFICIENT_TOTAL_SAMPLES",
                "total_samples":
                    total_samples,
                "new_samples":
                    new_samples,
            }

        if (
            new_samples
            < self.minimum_new_samples
        ):

            return {
                "eligible": False,
                "reason":
                    "INSUFFICIENT_NEW_SAMPLES",
                "total_samples":
                    total_samples,
                "new_samples":
                    new_samples,
            }

        return {
            "eligible": True,
            "reason": "ENOUGH_DATA",
            "total_samples":
                total_samples,
            "new_samples":
                new_samples,
        }

    # ========================================================
    # WEAKNESS CHECK
    # ========================================================

    def check_weakness(
        self,
        weakness_report,
    ):

        if not isinstance(
            weakness_report,
            dict,
        ):

            return {
                "eligible": False,
                "reason":
                    "INVALID_WEAKNESS_REPORT",
            }

        status = weakness_report.get(
            "status"
        )

        weaknesses = weakness_report.get(
            "total_weaknesses",
            0,
        )

        if status == "INSUFFICIENT_EVIDENCE":

            return {
                "eligible": False,
                "reason":
                    "INSUFFICIENT_WEAKNESS_EVIDENCE",
            }

        if not weaknesses:

            return {
                "eligible": False,
                "reason":
                    "NO_CONFIRMED_WEAKNESS",
            }

        return {
            "eligible": True,
            "reason":
                "CONFIRMED_WEAKNESS",
        }

    # ========================================================
    # RETRAIN ELIGIBILITY
    # ========================================================

    def can_retrain(
        self,
        total_samples,
        new_samples,
        weakness_report,
    ):

        data_check = self.check_data(
            total_samples=total_samples,
            new_samples=new_samples,
        )

        if not data_check["eligible"]:

            return {
                "eligible": False,
                "reason": data_check["reason"],
                "data_check": data_check,
            }

        weakness_check = (
            self.check_weakness(
                weakness_report
            )
        )

        if not weakness_check["eligible"]:

            return {
                "eligible": False,
                "reason":
                    weakness_check["reason"],
                "data_check":
                    data_check,
                "weakness_check":
                    weakness_check,
            }

        return {
            "eligible": True,
            "reason":
                "RETRAINING_ELIGIBLE",
            "data_check":
                data_check,
            "weakness_check":
                weakness_check,
        }

    # ========================================================
    # BACKUP CURRENT MODEL
    # ========================================================

    def backup_model(
        self,
        model_name,
    ):

        source = (
            self.model_dir
            / model_name
        )

        if not source.exists():

            raise FileNotFoundError(
                f"Model not found: {source}"
            )

        timestamp = (
            datetime.now()
            .strftime("%Y%m%d_%H%M%S")
        )

        backup_name = (
            f"{source.stem}"
            f"_backup_{timestamp}"
            f"{source.suffix}"
        )

        destination = (
            self.model_dir
            / backup_name
        )

        shutil.copy2(
            source,
            destination,
        )

        return destination

    # ========================================================
    # VALIDATE CANDIDATE
    # ========================================================

    def validate_candidate(
        self,
        current_metrics,
        candidate_metrics,
    ):

        if not isinstance(
            current_metrics,
            dict,
        ) or not isinstance(
            candidate_metrics,
            dict,
        ):

            return {
                "approved": False,
                "reason":
                    "INVALID_METRICS",
            }

        current_accuracy = (
            current_metrics.get(
                "accuracy"
            )
        )

        candidate_accuracy = (
            candidate_metrics.get(
                "accuracy"
            )
        )

        current_mae = (
            current_metrics.get(
                "mae"
            )
        )

        candidate_mae = (
            candidate_metrics.get(
                "mae"
            )
        )

        # ----------------------------------------------------
        # Accuracy model
        # ----------------------------------------------------

        if (
            candidate_accuracy is not None
            and current_accuracy is not None
        ):

            if (
                candidate_accuracy
                < current_accuracy
            ):

                return {
                    "approved": False,
                    "reason":
                        "CANDIDATE_ACCURACY_WORSE",
                }

        # ----------------------------------------------------
        # Regression model
        # ----------------------------------------------------

        if (
            candidate_mae is not None
            and current_mae is not None
        ):

            if (
                candidate_mae
                > current_mae
            ):

                return {
                    "approved": False,
                    "reason":
                        "CANDIDATE_MAE_WORSE",
                }

        return {
            "approved": True,
            "reason":
                "CANDIDATE_VALIDATED",
        }

    # ========================================================
    # PROMOTE CANDIDATE
    # ========================================================

    def promote_candidate(
        self,
        candidate_path,
        model_name,
    ):

        candidate = Path(
            candidate_path
        )

        if not candidate.exists():

            raise FileNotFoundError(
                f"Candidate model not found: "
                f"{candidate}"
            )

        current = (
            self.model_dir
            / model_name
        )

        backup_path = None

        if current.exists():

            backup_path = (
                self.backup_model(
                    model_name
                )
            )

        shutil.copy2(
            candidate,
            current,
        )

        self._log(
            {
                "timestamp":
                    datetime.now().isoformat(),

                "model":
                    model_name,

                "action":
                    "PROMOTE",

                "candidate":
                    str(candidate),

                "backup":
                    str(backup_path)
                    if backup_path
                    else None,
            }
        )

        return {
            "promoted": True,
            "model":
                str(current),
            "backup":
                str(backup_path)
                if backup_path
                else None,
        }

    # ========================================================
    # LOGGING
    # ========================================================

    def _log(
        self,
        entry,
    ):

        history = []

        if self.retraining_log.exists():

            try:

                with open(
                    self.retraining_log,
                    "r",
                    encoding="utf-8",
                ) as file:

                    data = json.load(
                        file
                    )

                    if isinstance(
                        data,
                        list,
                    ):

                        history = data

            except Exception:
                history = []

        history.append(
            entry
        )

        with open(
            self.retraining_log,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                history,
                file,
                indent=4,
            )

    # ========================================================
    # STATUS
    # ========================================================

    def status(
        self,
        total_samples,
        new_samples,
        weakness_report,
    ):

        return self.can_retrain(
            total_samples=
                total_samples,

            new_samples=
                new_samples,

            weakness_report=
                weakness_report,
        )