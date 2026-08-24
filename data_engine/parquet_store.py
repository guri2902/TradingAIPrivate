# ============================================================
# TradingAI - PARQUET DATA STORE
# ============================================================

from pathlib import Path
import pandas as pd


class ParquetStore:

    def __init__(self, base_dir="market_data/processed"):

        self.base_dir = Path(base_dir)

        self.base_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        df,
        name
    ):

        if df is None or df.empty:
            raise ValueError(
                "Cannot save empty DataFrame"
            )

        path = self.base_dir / f"{name}.parquet"

        df.to_parquet(
            path,
            engine="pyarrow",
            index=False
        )

        print(
            f"[PARQUET] Saved: {path}"
        )

        print(
            f"[PARQUET] Rows: {len(df)}"
        )

        return path

    # ========================================================
    # LOAD
    # ========================================================

    def load(
        self,
        name
    ):

        path = self.base_dir / f"{name}.parquet"

        if not path.exists():

            raise FileNotFoundError(
                f"Parquet dataset not found: {path}"
            )

        df = pd.read_parquet(
            path,
            engine="pyarrow"
        )

        print(
            f"[PARQUET] Loaded: {path}"
        )

        print(
            f"[PARQUET] Rows: {len(df)}"
        )

        return df

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        name
    ):

        path = self.base_dir / f"{name}.parquet"

        return path.exists()

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        name
    ):

        path = self.base_dir / f"{name}.parquet"

        if path.exists():

            path.unlink()

            print(
                f"[PARQUET] Deleted: {path}"
            )

            return True

        return False

    # ========================================================
    # LIST DATASETS
    # ========================================================

    def list_datasets(self):

        files = sorted(
            self.base_dir.glob("*.parquet")
        )

        datasets = [
            file.stem
            for file in files
        ]

        print(
            f"[PARQUET] Datasets: {len(datasets)}"
        )

        return datasets