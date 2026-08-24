from pathlib import Path
import ast

from data_engine.step9_backtest import (
    make_option_snapshot,
)


sample = __import__("pandas").DataFrame(
    [
        {
            "timestamp":
                "2026-08-20 10:00:00",
            "symbol":
                "NIFTY",
            "expiry":
                "2026-08-25",
            "strike":
                24250,
            "option_type":
                "CE",
            "last_price":
                100.0,
            "iv":
                12.0,
            "change":
                1.0,
            "percent_change":
                1.0,
            "volume":
                1000,
            "oi":
                10000,
            "oi_change":
                500,
            "bid_price":
                99.5,
            "ask_price":
                100.5,
            "bid_quantity":
                100,
            "ask_quantity":
                100,
            "total_buy_quantity":
                1000,
            "total_sell_quantity":
                900,
            "underlying_value":
                24230,
        },
        {
            "timestamp":
                "2026-08-20 10:00:00",
            "symbol":
                "NIFTY",
            "expiry":
                "2026-08-25",
            "strike":
                24250,
            "option_type":
                "PE",
            "last_price":
                110.0,
            "iv":
                13.0,
            "change":
                -1.0,
            "percent_change":
                -0.9,
            "volume":
                1200,
            "oi":
                11000,
            "oi_change":
                -300,
            "bid_price":
                109.5,
            "ask_price":
                110.5,
            "bid_quantity":
                120,
            "ask_quantity":
                120,
            "total_buy_quantity":
                1100,
            "total_sell_quantity":
                1000,
            "underlying_value":
                24230,
        },
    ]
)

snapshot = make_option_snapshot(
    sample
)

assert snapshot["spot"] == 24230.0
assert len(snapshot["rows"]) == 1

row = snapshot["rows"][0]

assert row["strike"] == 24250.0
assert row["ce_ltp"] == 100.0
assert row["pe_ltp"] == 110.0
assert row["ce_iv"] == 12.0
assert row["pe_iv"] == 13.0

# Import is intentionally validated here so the test fails early on
# syntax/import problems.
code = Path(
    __file__
).parent / "step9_backtest.py"

ast.parse(
    code.read_text(
        encoding="utf-8"
    )
)

print(
    "STEP 9 BACKTEST SNAPSHOT TEST PASSED"
)