# ============================================================
# TradingAI - MARKET CONTEXT MERGER
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from data_engine.instrument_registry import (
    InstrumentRegistry,
)
from data_engine.ai_option_chain_analyst import (
    AIOptionChainAnalyst,
)
from data_engine.nse_futures_history import NseFuturesHistory


class MarketContext:

    def __init__(
        self,
        market_data_root="market_data",
        option_analyst: Optional[
            AIOptionChainAnalyst
        ] = None,
    ):

        self.market_data_root = Path(
            market_data_root
        )

        self.registry = (
            InstrumentRegistry()
        )

        # Gemini analysis is optional at application startup.
        #
        # The deterministic market/options/futures engine must remain
        # usable even when GEMINI_API_KEY is not configured. Gemini
        # will be initialized later when Step 7 AI analysis is invoked.
        self.option_analyst = option_analyst
        self.gemini_available = (
            option_analyst is not None
        )
        self.gemini_error = None

        if self.option_analyst is None:
            try:
                self.option_analyst = (
                    AIOptionChainAnalyst()
                )
                self.gemini_available = True

            except Exception as exc:
                self.option_analyst = None
                self.gemini_available = False
                self.gemini_error = str(exc)

                print(
                    "[MARKET-CONTEXT] Gemini option analyst "
                    f"unavailable: {exc}"
                )

        self.futures_source = NseFuturesHistory()

    # ========================================================
    # PATH HELPERS
    # ========================================================

    def _option_candidates(
        self,
        option_underlying: str,
    ):

        symbol = (
            option_underlying
            .strip()
            .lower()
        )

        return [
            (
                self.market_data_root
                / "processed"
                / f"{symbol}_option_history.parquet"
            ),
            (
                self.market_data_root
                / "processed"
                / f"{symbol}_options_history.parquet"
            ),
            (
                self.market_data_root
                / "processed"
                / "options"
                / f"{symbol}_option_history.parquet"
            ),
            (
                self.market_data_root
                / "processed"
                / "options"
                / f"{symbol}_options.parquet"
            ),
        ]

    def _futures_candidates(
        self,
        futures_underlying: str,
    ):

        symbol = (
            futures_underlying
            .strip()
            .lower()
        )

        candidates = [
            (
                self.market_data_root
                / "processed"
                / f"{symbol}_futures.parquet"
            ),
            (
                self.market_data_root
                / "processed"
                / f"{symbol}_futures.csv"
            ),
            (
                self.market_data_root
                / "processed"
                / "futures"
                / f"{symbol}_futures.parquet"
            ),
            (
                self.market_data_root
                / "processed"
                / "futures"
                / f"{symbol}_futures.csv"
            ),
            (
                self.market_data_root
                / "raw"
                / "jugaad"
                / "futures"
                / f"{symbol}_futures.csv"
            ),
        ]

        # Also look for date-ranged futures files.
        futures_dirs = [
            self.market_data_root
            / "processed"
            / "futures",

            self.market_data_root
            / "raw"
            / "jugaad"
            / "futures",
        ]

        for directory in futures_dirs:

            if not directory.exists():
                continue

            for path in sorted(
                directory.glob(
                    f"{symbol}_futures_*.csv"
                )
            ):

                candidates.append(
                    path
                )

            for path in sorted(
                directory.glob(
                    f"{symbol}_futures_*.parquet"
                )
            ):

                candidates.append(
                    path
                )

        return candidates

    # ========================================================
    # LOAD OPTION HISTORY
    # ========================================================

    def load_options(
        self,
        instrument_symbol: str,
    ):

        config = self.registry.get(
            instrument_symbol
        )

        candidates = (
            self._option_candidates(
                config.option_underlying
            )
        )

        path = next(
            (
                candidate
                for candidate in candidates
                if candidate.exists()
            ),
            None,
        )

        if path is None:

            return {
                "available": False,
                "reason":
                    "OPTION_HISTORY_NOT_FOUND",
                "underlying":
                    config.option_underlying,
                "rows": 0,
            }

        try:

            df = pd.read_parquet(
                path
            )

        except Exception as exc:

            return {
                "available": False,
                "reason":
                    "OPTION_HISTORY_READ_ERROR",
                "error":
                    str(exc),
                "underlying":
                    config.option_underlying,
                "path":
                    str(path),
                "rows": 0,
            }

        if df.empty:

            return {
                "available": False,
                "reason":
                    "OPTION_HISTORY_EMPTY",
                "underlying":
                    config.option_underlying,
                "path":
                    str(path),
                "rows": 0,
            }

        # ----------------------------------------------------
        # Validate that the option data belongs to the
        # requested instrument.
        # ----------------------------------------------------

        if "symbol" in df.columns:

            symbols = (
                df["symbol"]
                .dropna()
                .astype(str)
                .str.upper()
                .unique()
                .tolist()
            )

            if symbols:

                expected = (
                    config.option_underlying
                    .upper()
                )

                if expected not in symbols:

                    return {
                        "available": False,
                        "reason":
                            "OPTION_UNDERLYING_MISMATCH",
                        "expected":
                            expected,
                        "found":
                            symbols,
                        "path":
                            str(path),
                        "rows": 0,
                    }

        # ----------------------------------------------------
        # Gemini is optional.
        #
        # If it is not configured, keep the deterministic option
        # history available instead of failing the entire engine.
        # ----------------------------------------------------

        if self.option_analyst is None:

            return {
                "available": True,
                "underlying":
                    config.option_underlying,
                "path":
                    str(path),
                "rows":
                    int(len(df)),
                "snapshots":
                    int(
                        df["timestamp"].nunique()
                    )
                    if "timestamp" in df.columns
                    else 0,
                "summary": {},
                "ai_available": False,
                "ai_reason":
                    "GEMINI_API_KEY_NOT_CONFIGURED",
                "ai_error":
                    self.gemini_error,
            }

        try:

            summary = (
                self.option_analyst.build_summary(
                    df
                )
            )

        except Exception as exc:

            return {
                "available": True,
                "underlying":
                    config.option_underlying,
                "path":
                    str(path),
                "rows":
                    int(len(df)),
                "snapshots":
                    int(
                        df["timestamp"].nunique()
                    )
                    if "timestamp" in df.columns
                    else 0,
                "summary": {},
                "ai_available": False,
                "ai_reason":
                    "OPTION_SUMMARY_ERROR",
                "ai_error":
                    str(exc),
            }

        return {
            "available": True,
            "underlying":
                config.option_underlying,
            "path":
                str(path),
            "rows":
                int(len(df)),
            "snapshots":
                int(
                    df["timestamp"].nunique()
                )
                if "timestamp" in df.columns
                else 0,
            "summary":
                summary,
        }

    # ========================================================
    # LOAD FUTURES
    # ========================================================

    def load_futures(
        self,
        instrument_symbol: str,
    ):

        config = self.registry.get(
            instrument_symbol
        )

        underlying = config.futures_underlying

        if not underlying:
            return {
                "available": False,
                "reason": "NO_FUTURES_UNDERLYING",
                "underlying": None,
                "rows": 0,
            }

        # The filesystem lookup used previously could not see the
        # directly verified Jugaad FUTIDX data. Use the adapter that
        # has already been validated independently.
        try:
            df = self.futures_source.get_history(
                symbol=underlying,
                from_date=pd.Timestamp("2026-01-01").date(),
                to_date=pd.Timestamp.now().date(),
            )

        except Exception as exc:
            return {
                "available": False,
                "reason": "FUTURES_HISTORY_READ_ERROR",
                "error": str(exc),
                "underlying": underlying,
                "rows": 0,
            }

        if df is None or df.empty:
            return {
                "available": False,
                "reason": "FUTURES_HISTORY_EMPTY",
                "underlying": underlying,
                "rows": 0,
            }

        df = df.copy()
        df.columns = [
            str(column).strip().lower().replace(" ", "_")
            for column in df.columns
        ]

        latest = self._latest_futures_row(df)

        return {
            "available": True,
            "underlying": underlying,
            "rows": int(len(df)),
            "columns": list(df.columns),
            "expiry": latest.get("expiry"),
            "source": "jugaad-data",
            "latest": latest,
        }

    # ========================================================
    # FUTURES LATEST ROW
    # ========================================================

    @staticmethod
    def _latest_futures_row(
        df: pd.DataFrame,
    ):

        if df.empty:

            return {}

        # ----------------------------------------------------
        # Try common timestamp columns.
        # ----------------------------------------------------

        timestamp_column = next(
            (
                column
                for column in [
                    "timestamp",
                    "datetime",
                    "date",
                ]
                if column in df.columns
            ),
            None,
        )

        if timestamp_column:

            work = df.copy()

            work[
                timestamp_column
            ] = pd.to_datetime(
                work[
                    timestamp_column
                ],
                errors="coerce",
            )

            work = (
                work
                .dropna(
                    subset=[
                        timestamp_column
                    ]
                )
                .sort_values(
                    timestamp_column
                )
            )

            if not work.empty:

                row = (
                    work.iloc[-1]
                    .to_dict()
                )

            else:

                row = (
                    df.iloc[-1]
                    .to_dict()
                )

        else:

            row = (
                df.iloc[-1]
                .to_dict()
            )

        return {
            key:
                MarketContext._clean_value(
                    value
                )
            for key, value in row.items()
        }

    # ========================================================
    # BUILD COMPLETE DERIVATIVE CONTEXT
    # ========================================================

    def build(
        self,
        instrument_symbol: str,
    ):

        config = self.registry.get(
            instrument_symbol
        )

        options = self.load_options(
            config.symbol
        )

        futures = self.load_futures(
            config.symbol
        )

        return {
            "instrument": {
                "symbol":
                    config.symbol,
                "display_name":
                    config.display_name,
                "market_symbol":
                    config.market_symbol,
                "option_underlying":
                    config.option_underlying,
                "futures_underlying":
                    config.futures_underlying,
                "segment":
                    config.segment,
                "asset_type":
                    config.asset_type,
            },

            "options":
                options,

            "futures":
                futures,
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
        context,
    ):

        if not isinstance(
            context,
            dict,
        ):

            raise TypeError(
                "Market context must be a dictionary."
            )

        required = [
            "instrument",
            "options",
            "futures",
        ]

        missing = [
            key
            for key in required
            if key not in context
        ]

        if missing:

            raise ValueError(
                f"Market context missing: {missing}"
            )

        instrument = (
            context["instrument"]
        )

        if not instrument.get(
            "symbol"
        ):

            raise ValueError(
                "Instrument mapping is missing."
            )

        return True

    # ========================================================
    # CLEAN
    # ========================================================

    @staticmethod
    def _clean_value(
        value,
    ):

        if pd.isna(value):
            return None

        if isinstance(
            value,
            pd.Timestamp,
        ):

            return value.isoformat()

        if hasattr(
            value,
            "item",
        ):

            try:
                return value.item()
            except Exception:
                pass

        return value