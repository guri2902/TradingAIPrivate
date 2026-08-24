from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

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


def load_index_history(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Index history not found: {path}"
        )

    df = pd.read_csv(path)

    df = df.rename(
        columns={
            "Date": "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    required = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise RuntimeError(
            "Index history missing columns: "
            + ", ".join(missing)
        )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    for c in (
        "open",
        "high",
        "low",
        "close",
        "volume",
    ):
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce",
        )

    df = df.dropna(
        subset=required
    ).copy()

    # Keep BOTH schemas. This is intentional:
    # some existing analytics use Open/High/Low/Close/Volume,
    # while other feature code uses lowercase open/high/low/close/volume.
    df["Open"] = df["open"]
    df["High"] = df["high"]
    df["Low"] = df["low"]
    df["Close"] = df["close"]
    df["Volume"] = df["volume"]

    return (
        df.sort_values("timestamp")
        .reset_index(drop=True)
    )


def load_option_history(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Option history not found: {path}"
        )

    df = pd.read_parquet(path)

    required = [
        "timestamp",
        "symbol",
        "expiry",
        "strike",
        "option_type",
        "last_price",
        "underlying_value",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            "Option history missing columns: "
            + ", ".join(missing)
        )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    df["expiry"] = pd.to_datetime(
        df["expiry"],
        errors="coerce",
    )

    for column in (
        "strike",
        "last_price",
        "iv",
        "underlying_value",
    ):
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    df["option_type"] = (
        df["option_type"]
        .astype(str)
        .str.upper()
    )

    df = (
        df.dropna(
            subset=[
                "timestamp",
                "expiry",
                "strike",
                "option_type",
                "last_price",
                "underlying_value",
            ]
        )
        .sort_values(
            [
                "timestamp",
                "expiry",
                "strike",
                "option_type",
            ]
        )
        .reset_index(drop=True)
    )

    return df


def make_option_snapshot(
    snapshot: pd.DataFrame,
) -> Dict[str, Any]:

    if snapshot.empty:
        raise RuntimeError(
            "Cannot build snapshot from empty option data."
        )

    expiry = snapshot["expiry"].iloc[0]
    expiry_text = (
        pd.Timestamp(expiry).strftime("%Y-%m-%d")
    )

    spot = float(
        snapshot["underlying_value"]
        .dropna()
        .iloc[0]
    )

    wide: Dict[float, Dict[str, Any]] = {}

    for row in snapshot.to_dict(
        orient="records"
    ):

        strike = float(
            row["strike"]
        )

        option_type = str(
            row["option_type"]
        ).upper()

        item = wide.setdefault(
            strike,
            {
                "strike": strike,
            },
        )

        prefix = (
            "ce"
            if option_type == "CE"
            else "pe"
        )

        # Canonical fields used by TradeEngine.
        item[f"{prefix}_ltp"] = float(
            row["last_price"]
        )

        item[f"{prefix}_iv"] = float(
            row.get("iv", 0.0)
            or 0.0
        )

        # Add every common alias already used by different versions
        # of the option analyzers/parser. Values all come from the
        # SAME historical snapshot; no synthetic market data.
        alias_map = {
            "change": (
                f"{prefix}_change",
                f"{prefix}_pchange",
            ),
            "percent_change": (
                f"{prefix}_percent_change",
                f"{prefix}_pChange",
            ),
            "volume": (
                f"{prefix}_volume",
                f"{prefix}_total_traded_volume",
            ),
            "oi": (
                f"{prefix}_oi",
                f"{prefix}_open_interest",
            ),
            "oi_change": (
                f"{prefix}_change_oi",
                f"{prefix}_oi_change",
            ),
            "bid_price": (
                f"{prefix}_bid_price",
            ),
            "ask_price": (
                f"{prefix}_ask_price",
            ),
            "bid_quantity": (
                f"{prefix}_bid_quantity",
            ),
            "ask_quantity": (
                f"{prefix}_ask_quantity",
            ),
            "total_buy_quantity": (
                f"{prefix}_total_buy_quantity",
            ),
            "total_sell_quantity": (
                f"{prefix}_total_sell_quantity",
            ),
            "underlying_value": (
                f"{prefix}_underlying_value",
            ),
        }

        for source, targets in alias_map.items():
            value = row.get(source)

            for target in targets:
                item[target] = value

    rows = [
        value
        for value in wide.values()
        if (
            value.get("ce_ltp", 0) > 0
            or value.get("pe_ltp", 0) > 0
        )
    ]

    if not rows:
        raise RuntimeError(
            "Historical option snapshot contains no usable CE/PE prices."
        )

    return {
        "spot": spot,
        "expiry": expiry_text,
        "rows": rows,
    }


def candles_until(
    index_df: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> pd.DataFrame:

    candles = index_df[
        index_df["timestamp"] <= timestamp
    ].copy()

    return candles.reset_index(
        drop=True
    )


def score_outcome(
    trade: Dict[str, Any],
    future_snapshots,
    trade_timestamp: pd.Timestamp,
    expiry: pd.Timestamp,
) -> Dict[str, Any]:
    """
    Follow one generated trade through all later historical snapshots.

    No future value is used during trade generation. This function is only
    called after the trade has already been generated from the current
    snapshot. The first terminal event wins:
        TARGET 2 -> TARGET 1 -> STOP LOSS -> EXPIRY/END
    """

    strike = trade.get("strike")
    option_type = str(
        trade.get("type")
        or ""
    ).upper()

    try:
        strike = float(strike)
    except (
        TypeError,
        ValueError,
    ):
        return {
            "outcome": "INVALID_STRIKE",
            "outcome_price": None,
            "closed_at": None,
            "r_multiple": None,
        }

    risk = trade.get("risk") or {}

    entry = _number(
        (
            risk.get("entry")
            if risk.get("entry") is not None
            else trade.get("premium")
        )
    )
    target2 = _number(
        risk.get("target2")
    )
    target1 = _number(
        risk.get("target1")
    )
    stop = _number(
        risk.get("sl")
    )

    risk_per_unit = max(
        entry - stop,
        0.0,
    )

    # Process only snapshots AFTER the prediction timestamp.
    candidates = []

    for snapshot_timestamp, snapshot_df in future_snapshots:

        snapshot_timestamp = pd.Timestamp(
            snapshot_timestamp
        )

        if snapshot_timestamp <= trade_timestamp:
            continue

        candidates.append(
            (
                snapshot_timestamp,
                snapshot_df,
            )
        )

    if not candidates:
        return {
            "outcome": "OPEN",
            "outcome_price": None,
            "closed_at": None,
            "r_multiple": None,
        }

    last_price = None
    last_timestamp = None

    for snapshot_timestamp, snapshot_df in candidates:

        matches = snapshot_df[
            snapshot_df["strike"]
            .astype(float)
            .eq(strike)
        ]

        matches = matches[
            matches["option_type"]
            .astype(str)
            .str.upper()
            .eq(option_type)
        ]

        if matches.empty:
            continue

        price = _number(
            matches.iloc[0]["last_price"]
        )

        if price <= 0:
            continue

        last_price = price
        last_timestamp = snapshot_timestamp

        # For long options, the higher target is more selective.
        if (
            target2 > 0
            and price >= target2
        ):
            r = (
                (target2 - entry)
                / risk_per_unit
                if risk_per_unit > 0
                else None
            )

            return {
                "outcome": "TARGET_2",
                "outcome_price": price,
                "closed_at": snapshot_timestamp.isoformat(),
                "r_multiple": r,
            }

        if (
            target1 > 0
            and price >= target1
        ):
            r = (
                (target1 - entry)
                / risk_per_unit
                if risk_per_unit > 0
                else None
            )

            return {
                "outcome": "TARGET_1",
                "outcome_price": price,
                "closed_at": snapshot_timestamp.isoformat(),
                "r_multiple": r,
            }

        if (
            stop > 0
            and price <= stop
        ):
            r = (
                (stop - entry)
                / risk_per_unit
                if risk_per_unit > 0
                else None
            )

            return {
                "outcome": "STOP_LOSS",
                "outcome_price": price,
                "closed_at": snapshot_timestamp.isoformat(),
                "r_multiple": r,
            }

        # End-of-expiry handling. Do not use snapshots after expiry.
        if snapshot_timestamp.normalize() >= pd.Timestamp(
            expiry
        ).normalize():
            r = (
                (price - entry)
                / risk_per_unit
                if risk_per_unit > 0
                else None
            )

            return {
                "outcome": "EXPIRY",
                "outcome_price": price,
                "closed_at": snapshot_timestamp.isoformat(),
                "r_multiple": r,
            }

    # Data ended before a terminal event.
    if last_price is not None:
        r = (
            (last_price - entry)
            / risk_per_unit
            if risk_per_unit > 0
            else None
        )

        return {
            "outcome": "END_OF_DATA",
            "outcome_price": last_price,
            "closed_at": (
                last_timestamp.isoformat()
                if last_timestamp is not None
                else None
            ),
            "r_multiple": r,
        }

    return {
        "outcome": "NO_FUTURE_CONTRACT",
        "outcome_price": None,
        "closed_at": None,
        "r_multiple": None,
    }


def _number(
    value,
    default=0.0,
):
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def run_backtest(
    selected_index: str,
    index_path: Path,
    option_path: Path,
    max_snapshots: Optional[int] = None,
) -> Dict[str, Any]:

    index_df = load_index_history(
        index_path
    )

    options_df = load_option_history(
        option_path
    )

    # One historical option snapshot per timestamp/expiry.
    snapshots = list(
        options_df.groupby(
            [
                "timestamp",
                "expiry",
            ],
            sort=True,
        )
    )

    if max_snapshots is not None:
        snapshots = snapshots[
            :max_snapshots
        ]

    if not snapshots:
        raise RuntimeError(
            "No historical option snapshots available."
        )

    engine = TradeEngine()

    results: List[Dict[str, Any]] = []

    print("=" * 70)
    print("TradingAI - STEP 9 HISTORICAL REPLAY")
    print("=" * 70)
    print(
        f"Index: {selected_index}"
    )
    print(
        f"Index history: {len(index_df)} rows"
    )
    print(
        f"Option snapshots: {len(snapshots)}"
    )
    print("=" * 70)

    for number, (
        (timestamp, expiry),
        snapshot_df,
    ) in enumerate(
        snapshots,
        start=1,
    ):

        timestamp = pd.Timestamp(
            timestamp
        )

        candles = candles_until(
            index_df,
            timestamp,
        )

        # Technical indicators such as SMA200/EMA21 require enough
        # history. Skip early snapshots rather than inventing values.
        if len(candles) < 200:
            print(
                f"[{number}] SKIP "
                f"{timestamp} - only "
                f"{len(candles)} candles"
            )
            continue

        option_snapshot = make_option_snapshot(
            snapshot_df
        )

        expiry_date = pd.Timestamp(
            expiry
        ).date()

        try:

            trade_result = (
                engine.generate_trades_from_snapshot(
                    selected_index=selected_index,
                    candles=candles,
                    option_snapshot=option_snapshot,
                    expiry=expiry_date,
                    # Backtest MUST NOT pull live MTF/ML context.
                    # Step 10 can add historical model replay.
                    multi_tf={},
                    unified_context={
                        "available": False,
                        "ml": {},
                        "options": {},
                        "futures": {},
                        "mode": "backtest",
                    },
                )
            )

        except Exception as exc:

            print(
                f"[{number}] ERROR "
                f"{timestamp}: {exc}"
            )

            print(
                "[REPLAY DEBUG] Candle columns:",
                list(candles.columns),
            )

            print(
                "[REPLAY DEBUG] Option row sample:",
                (
                    option_snapshot.get("rows", [{}])[0]
                    if isinstance(option_snapshot, dict)
                    and option_snapshot.get("rows")
                    else {}
                ),
            )

            print("[TRACEBACK]")
            traceback.print_exc()

            results.append(
                {
                    "timestamp":
                        timestamp.isoformat(),
                    "expiry":
                        expiry.isoformat(),
                    "status":
                        "ERROR",
                    "error":
                        str(exc),
                }
            )

            continue

        trades = (
            trade_result.get(
                "trades"
            )
            or []
        )

        # Follow every generated trade through all subsequent historical
        # option snapshots. This is the critical Step 9 fix: a trade is
        # not resolved by looking only one snapshot ahead.
        future_snapshots = [
            (
                pd.Timestamp(key[0]),
                future_df,
            )
            for key, future_df in snapshots
            if pd.Timestamp(key[0]) > timestamp
        ]

        evaluated = []

        for trade in trades:
            outcome = score_outcome(
                trade,
                future_snapshots,
                trade_timestamp=timestamp,
                expiry=pd.Timestamp(expiry),
            )

            evaluated.append(
                {
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
                        ).get(
                            "entry"
                        ),
                    "stop_loss":
                        (
                            trade.get("risk")
                            or {}
                        ).get(
                            "sl"
                        ),
                    "target1":
                        (
                            trade.get("risk")
                            or {}
                        ).get(
                            "target1"
                        ),
                    "target2":
                        (
                            trade.get("risk")
                            or {}
                        ).get(
                            "target2"
                        ),
                    "rr":
                        (
                            trade.get("risk")
                            or {}
                        ).get(
                            "rr"
                        ),
                    "outcome":
                        outcome["outcome"],
                    "outcome_price":
                        outcome["outcome_price"],
                    "closed_at":
                        outcome.get("closed_at"),
                    "r_multiple":
                        outcome.get("r_multiple"),
                }
            )

        results.append(
            {
                "timestamp":
                    timestamp.isoformat(),
                "expiry":
                    expiry.isoformat(),
                "status":
                    "OK",
                "trade_count":
                    len(evaluated),
                "trades":
                    evaluated,
            }
        )

        print(
            f"[{number}] {timestamp.date()} "
            f"| trades={len(evaluated)}"
        )

    completed = [
        item
        for item in results
        if item.get("status") == "OK"
    ]

    flat_trades = [
        trade
        for item in completed
        for trade in item.get("trades", [])
    ]

    resolved = [
        trade
        for trade in flat_trades
        if trade.get("outcome")
        in (
            "TARGET_1",
            "TARGET_2",
            "STOP_LOSS",
        )
    ]

    wins = [
        trade
        for trade in resolved
        if trade.get("outcome")
        in (
            "TARGET_1",
            "TARGET_2",
        )
    ]

    losses = [
        trade
        for trade in resolved
        if trade.get("outcome")
        == "STOP_LOSS"
    ]

    expiry_outcomes = [
        trade
        for trade in flat_trades
        if trade.get("outcome")
        == "EXPIRY"
    ]

    end_of_data = [
        trade
        for trade in flat_trades
        if trade.get("outcome")
        == "END_OF_DATA"
    ]

    target1_hits = [
        trade
        for trade in wins
        if trade.get("outcome") == "TARGET_1"
    ]

    target2_hits = [
        trade
        for trade in wins
        if trade.get("outcome") == "TARGET_2"
    ]

    all_r = [
        float(trade["r_multiple"])
        for trade in flat_trades
        if trade.get("r_multiple") is not None
    ]

    avg_r = (
        sum(all_r) / len(all_r)
        if all_r
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
        "index_rows":
            len(index_df),
        "option_snapshot_count":
            len(snapshots),
        "processed_snapshots":
            len(completed),
        "trade_candidates":
            len(flat_trades),
        "resolved_trade_candidates":
            len(resolved),
        "target_hits":
            len(wins),
        "target1_hits":
            len(target1_hits),
        "target2_hits":
            len(target2_hits),
        "stop_losses":
            len(losses),
        "expiry_outcomes":
            len(expiry_outcomes),
        "end_of_data":
            len(end_of_data),
        "average_r":
            round(
                avg_r,
                4,
            ),
        "win_rate":
            round(
                win_rate,
                2,
            ),
        "results":
            results,
    }

    output = (
        BASE_DIR
        / "market_data"
        / "processed"
        / "step9_backtest_report.json"
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
    print("STEP 9 REPLAY COMPLETE")
    print("=" * 70)
    print(
        f"Processed snapshots: "
        f"{report['processed_snapshots']}"
    )
    print(
        f"Trade candidates: "
        f"{report['trade_candidates']}"
    )
    print(
        f"Resolved: "
        f"{report['resolved_trade_candidates']}"
    )
    print(
        f"Targets: "
        f"{report['target_hits']}"
    )
    print(
        f"Target 1: "
        f"{report['target1_hits']}"
    )
    print(
        f"Target 2: "
        f"{report['target2_hits']}"
    )
    print(
        f"Stop losses: "
        f"{report['stop_losses']}"
    )
    print(
        f"Expiry outcomes: "
        f"{report['expiry_outcomes']}"
    )
    print(
        f"End of data: "
        f"{report['end_of_data']}"
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

    parser = argparse.ArgumentParser(
        description=(
            "TradingAI Step 9 historical replay"
        )
    )

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
        "--max-snapshots",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    run_backtest(
        selected_index=args.index,
        index_path=args.index_history,
        option_path=args.option_history,
        max_snapshots=args.max_snapshots,
    )


if __name__ == "__main__":
    main()