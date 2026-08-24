from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from data_engine.step9_backtest import (
    load_index_history,
    load_option_history,
    make_option_snapshot,
    candles_until,
    score_outcome,
)
from engine.trade_engine import TradeEngine


BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_INDEX_PATH = (
    BASE_DIR
    / "market_data"
    / "raw"
    / "eod2"
    / "daily"
    / "nifty 50.csv"
)

DEFAULT_OPTION_PATH = (
    BASE_DIR
    / "market_data"
    / "processed"
    / "nifty_option_history.parquet"
)


def run_walk_forward(
    selected_index: str,
    index_path: Path,
    option_path: Path,
    train_snapshots: int,
    test_snapshots: int | None = None,
    max_windows: int | None = None,
) -> Dict[str, Any]:

    index_df = load_index_history(
        index_path
    )

    options_df = load_option_history(
        option_path
    )

    grouped = list(
        options_df.groupby(
            [
                "timestamp",
                "expiry",
            ],
            sort=True,
        )
    )

    if len(grouped) <= train_snapshots:
        raise RuntimeError(
            "Not enough historical snapshots for "
            f"train_snapshots={train_snapshots}. "
            f"Available={len(grouped)}."
        )

    if test_snapshots is None:
        test_snapshots = 1

    windows = []

    start_test = train_snapshots
    window_number = 0

    while start_test < len(grouped):

        if (
            max_windows is not None
            and window_number >= max_windows
        ):
            break

        train = grouped[:start_test]

        end_test = min(
            start_test + test_snapshots,
            len(grouped),
        )

        test = grouped[
            start_test:end_test
        ]

        windows.append(
            {
                "train": train,
                "test": test,
            }
        )

        start_test = end_test
        window_number += 1

    engine = TradeEngine()

    all_trades: List[Dict[str, Any]] = []
    window_reports: List[Dict[str, Any]] = []

    print("=" * 70)
    print(
        "TradingAI - STEP 10 WALK-FORWARD BACKTEST"
    )
    print("=" * 70)
    print(
        f"Index: {selected_index}"
    )
    print(
        f"Index history: {len(index_df)} rows"
    )
    print(
        f"Total option snapshots: {len(grouped)}"
    )
    print(
        f"Initial train snapshots: {train_snapshots}"
    )
    print(
        f"Test snapshots/window: {test_snapshots}"
    )
    print(
        f"Windows: {len(windows)}"
    )
    print("=" * 70)

    for window_index, window in enumerate(
        windows,
        start=1,
    ):

        train_grouped = window[
            "train"
        ]

        test_grouped = window[
            "test"
        ]

        # ----------------------------------------------------------
        # The "train" portion is intentionally used only as historical
        # context. No future test snapshot is ever included in the
        # candles or option snapshot used to generate a test trade.
        # ----------------------------------------------------------

        first_test_timestamp = pd.Timestamp(
            test_grouped[0][0][0]
        )

        training_candles = candles_until(
            index_df,
            first_test_timestamp,
        )

        # Need enough history for the existing technical analyzers.
        if len(training_candles) < 200:
            print(
                f"[WINDOW {window_index}] SKIP - "
                f"only {len(training_candles)} candles"
            )
            continue

        window_trades = []

        for test_position, (
            (timestamp, expiry),
            snapshot_df,
        ) in enumerate(
            test_grouped
        ):

            timestamp = pd.Timestamp(
                timestamp
            )
            expiry = pd.Timestamp(
                expiry
            )

            candles = candles_until(
                index_df,
                timestamp,
            )

            if len(candles) < 200:
                continue

            option_snapshot = (
                make_option_snapshot(
                    snapshot_df
                )
            )

            try:

                trade_result = (
                    engine.generate_trades_from_snapshot(
                        selected_index=selected_index,
                        candles=candles,
                        option_snapshot=option_snapshot,
                        expiry=expiry.date(),
                        multi_tf={},
                        unified_context={
                            "available": False,
                            "ml": {},
                            "options": {},
                            "futures": {},
                            "mode": "walk_forward",
                            "train_snapshot_count": len(
                                train_grouped
                            ),
                        },
                    )
                )

            except Exception as exc:

                print(
                    f"[WINDOW {window_index}] "
                    f"{timestamp} ERROR: {exc}"
                )

                continue

            trades = (
                trade_result.get(
                    "trades"
                )
                or []
            )

            # ------------------------------------------------------
            # IMPORTANT:
            # evaluate only AFTER the test snapshot.
            # ------------------------------------------------------

            future_snapshots = [
                (
                    pd.Timestamp(
                        future_key[0]
                    ),
                    future_df,
                )
                for future_key, future_df in grouped
                if pd.Timestamp(
                    future_key[0]
                ) > timestamp
            ]

            for trade in trades:

                outcome = score_outcome(
                    trade,
                    future_snapshots,
                    trade_timestamp=timestamp,
                    expiry=expiry,
                )

                row = {
                    "window":
                        window_index,
                    "train_snapshot_count":
                        len(train_grouped),
                    "test_snapshot_index":
                        test_position,
                    "timestamp":
                        timestamp.isoformat(),
                    "expiry":
                        expiry.isoformat(),
                    "strike":
                        trade.get("strike"),
                    "type":
                        trade.get("type"),
                    "ai_score":
                        trade.get("ai_score"),
                    "probability":
                        trade.get("probability"),
                    "entry":
                        (
                            trade.get("risk")
                            or {}
                        ).get("entry"),
                    "stop_loss":
                        (
                            trade.get("risk")
                            or {}
                        ).get("sl"),
                    "target1":
                        (
                            trade.get("risk")
                            or {}
                        ).get("target1"),
                    "target2":
                        (
                            trade.get("risk")
                            or {}
                        ).get("target2"),
                    "rr":
                        (
                            trade.get("risk")
                            or {}
                        ).get("rr"),
                    "outcome":
                        outcome.get("outcome"),
                    "outcome_price":
                        outcome.get("outcome_price"),
                    "closed_at":
                        outcome.get("closed_at"),
                    "r_multiple":
                        outcome.get("r_multiple"),
                }

                window_trades.append(
                    row
                )
                all_trades.append(
                    row
                )

        resolved = [
            row
            for row in window_trades
            if row.get("outcome")
            in (
                "TARGET_1",
                "TARGET_2",
                "STOP_LOSS",
            )
        ]

        wins = [
            row
            for row in resolved
            if row.get("outcome")
            in (
                "TARGET_1",
                "TARGET_2",
            )
        ]

        losses = [
            row
            for row in resolved
            if row.get("outcome")
            == "STOP_LOSS"
        ]

        rs = [
            float(row["r_multiple"])
            for row in window_trades
            if row.get(
                "r_multiple"
            ) is not None
        ]

        report = {
            "window":
                window_index,
            "train_snapshots":
                len(train_grouped),
            "test_snapshots":
                len(test_grouped),
            "trade_count":
                len(window_trades),
            "resolved":
                len(resolved),
            "wins":
                len(wins),
            "losses":
                len(losses),
            "average_r":
                (
                    sum(rs) / len(rs)
                    if rs
                    else 0.0
                ),
        }

        window_reports.append(
            report
        )

        print(
            f"[WINDOW {window_index}] "
            f"train={len(train_grouped)} "
            f"test={len(test_grouped)} "
            f"trades={len(window_trades)} "
            f"resolved={len(resolved)} "
            f"wins={len(wins)} "
            f"losses={len(losses)}"
        )

    resolved = [
        row
        for row in all_trades
        if row.get("outcome")
        in (
            "TARGET_1",
            "TARGET_2",
            "STOP_LOSS",
        )
    ]

    wins = [
        row
        for row in resolved
        if row.get("outcome")
        in (
            "TARGET_1",
            "TARGET_2",
        )
    ]

    losses = [
        row
        for row in resolved
        if row.get("outcome")
        == "STOP_LOSS"
    ]

    end_of_data = [
        row
        for row in all_trades
        if row.get("outcome")
        == "END_OF_DATA"
    ]

    expiry = [
        row
        for row in all_trades
        if row.get("outcome")
        == "EXPIRY"
    ]

    r_values = [
        float(row["r_multiple"])
        for row in all_trades
        if row.get("r_multiple") is not None
    ]

    average_r = (
        sum(r_values) / len(r_values)
        if r_values
        else 0.0
    )

    win_rate = (
        len(wins)
        / len(resolved)
        * 100
        if resolved
        else 0.0
    )

    report = {
        "selected_index":
            selected_index,
        "historical_index_rows":
            len(index_df),
        "total_snapshots":
            len(grouped),
        "initial_train_snapshots":
            train_snapshots,
        "test_snapshots_per_window":
            test_snapshots,
        "windows_processed":
            len(window_reports),
        "trade_candidates":
            len(all_trades),
        "resolved":
            len(resolved),
        "wins":
            len(wins),
        "losses":
            len(losses),
        "target1_hits":
            sum(
                1
                for row in wins
                if row.get("outcome")
                == "TARGET_1"
            ),
        "target2_hits":
            sum(
                1
                for row in wins
                if row.get("outcome")
                == "TARGET_2"
            ),
        "expiry_outcomes":
            len(expiry),
        "end_of_data":
            len(end_of_data),
        "average_r":
            round(
                average_r,
                4,
            ),
        "win_rate":
            round(
                win_rate,
                2,
            ),
        "windows":
            window_reports,
        "trades":
            all_trades,
    }

    output = (
        BASE_DIR
        / "market_data"
        / "processed"
        / "step10_walk_forward_report.json"
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print("=" * 70)
    print("STEP 10 WALK-FORWARD COMPLETE")
    print("=" * 70)
    print(
        f"Windows: {report['windows_processed']}"
    )
    print(
        f"Trade candidates: "
        f"{report['trade_candidates']}"
    )
    print(
        f"Resolved: "
        f"{report['resolved']}"
    )
    print(
        f"Wins: "
        f"{report['wins']}"
    )
    print(
        f"Losses: "
        f"{report['losses']}"
    )
    print(
        f"Average R: "
        f"{report['average_r']}"
    )
    print(
        f"Win rate: "
        f"{report['win_rate']}%"
    )
    print(
        f"Saved: {output}"
    )

    return report


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--index",
        default="NIFTY 50",
    )

    parser.add_argument(
        "--index-history",
        type=Path,
        default=DEFAULT_INDEX_PATH,
    )

    parser.add_argument(
        "--option-history",
        type=Path,
        default=DEFAULT_OPTION_PATH,
    )

    parser.add_argument(
        "--train-snapshots",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--test-snapshots",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--max-windows",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    run_walk_forward(
        selected_index=args.index,
        index_path=args.index_history,
        option_path=args.option_history,
        train_snapshots=args.train_snapshots,
        test_snapshots=args.test_snapshots,
        max_windows=args.max_windows,
    )


if __name__ == "__main__":
    main()