# ============================================================
# TradingAI - INTRADAY OPTION HISTORY COLLECTOR
# ============================================================

from __future__ import annotations

import signal
import time
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

from data_engine.nse_option_chain import NseOptionChain


# ============================================================
# CONFIGURATION
# ============================================================

SYMBOL = "NIFTY"

INTERVAL_SECONDS = 300          # 5 minutes

MARKET_OPEN = dt_time(
    9,
    15
)

MARKET_CLOSE = dt_time(
    15,
    30
)

TIMEZONE = ZoneInfo(
    "Asia/Kolkata"
)


# ============================================================
# COLLECTOR
# ============================================================

class OptionHistoryCollector:

    def __init__(
        self,
        symbol=SYMBOL,
        interval_seconds=INTERVAL_SECONDS,
    ):

        self.symbol = (
            str(symbol)
            .strip()
            .upper()
        )

        self.interval_seconds = int(
            interval_seconds
        )

        self.running = True

        self.source = (
            NseOptionChain()
        )

        self.snapshot_count = 0

    # ========================================================
    # STOP
    # ========================================================

    def stop(
        self,
        *_args,
    ):

        if self.running:

            print(
                "\n[OPTION-HISTORY] "
                "Stopping collector..."
            )

        self.running = False

    # ========================================================
    # CURRENT TIME
    # ========================================================

    @staticmethod
    def now():

        return datetime.now(
            TIMEZONE
        )

    # ========================================================
    # MARKET STATUS
    # ========================================================

    def market_status(self):

        now = self.now()

        current_time = (
            now.time()
        )

        if current_time < MARKET_OPEN:

            return (
                "BEFORE_OPEN"
            )

        if current_time >= MARKET_CLOSE:

            return (
                "AFTER_CLOSE"
            )

        return (
            "OPEN"
        )

    # ========================================================
    # WAIT UNTIL OPEN
    # ========================================================

    def wait_until_open(self):

        while self.running:

            status = (
                self.market_status()
            )

            if status == "OPEN":

                return True

            if status == "AFTER_CLOSE":

                print(
                    "\n[OPTION-HISTORY] "
                    "Market closed."
                )

                return False

            now = self.now()

            market_open = (
                datetime.combine(
                    now.date(),
                    MARKET_OPEN,
                    tzinfo=TIMEZONE,
                )
            )

            seconds = (
                market_open - now
            ).total_seconds()

            wait_seconds = max(
                1,
                min(
                    60,
                    int(seconds),
                )
            )

            print(
                f"\r[OPTION-HISTORY] "
                f"Waiting for market open... "
                f"{seconds / 60:.1f} min",
                end="",
                flush=True,
            )

            time.sleep(
                wait_seconds
            )

        return False

    # ========================================================
    # FETCH SNAPSHOT
    # ========================================================

    def fetch_snapshot(self):

        print(
            "\n"
            + "-" * 70
        )

        print(
            f"[OPTION-HISTORY] "
            f"Fetching {self.symbol} snapshot..."
        )

        print(
            f"[OPTION-HISTORY] "
            f"Time: {self.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        try:

            df = (
                self.source.fetch_and_save(
                    symbol=self.symbol
                )
            )

            if df is None or df.empty:

                print(
                    "[OPTION-HISTORY] "
                    "Empty snapshot received."
                )

                return False

            self.snapshot_count += 1

            print(
                f"[OPTION-HISTORY] "
                f"Snapshot #{self.snapshot_count} "
                f"saved: {len(df)} rows"
            )

            return True

        except Exception as exc:

            print(
                "[OPTION-HISTORY] "
                f"Snapshot failed: {exc}"
            )

            return False

    # ========================================================
    # WAIT FOR NEXT 5-MINUTE BOUNDARY
    # ========================================================

    def wait_for_next_interval(self):

        now = self.now()

        elapsed = (
            now.minute * 60
            + now.second
        )

        remainder = (
            elapsed
            % self.interval_seconds
        )

        wait_seconds = (
            self.interval_seconds
            - remainder
        )

        if wait_seconds <= 0:

            wait_seconds = (
                self.interval_seconds
            )

        # Don't overshoot market close.
        remaining_to_close = (
            datetime.combine(
                now.date(),
                MARKET_CLOSE,
                tzinfo=TIMEZONE,
            )
            - now
        ).total_seconds()

        if remaining_to_close <= 0:

            return False

        wait_seconds = min(
            wait_seconds,
            max(
                1,
                int(
                    remaining_to_close
                ),
            ),
        )

        print(
            f"[OPTION-HISTORY] "
            f"Next snapshot in "
            f"{wait_seconds}s"
        )

        for _ in range(
            wait_seconds
        ):

            if not self.running:

                return False

            if (
                self.market_status()
                != "OPEN"
            ):

                return False

            time.sleep(1)

        return True

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        print("=" * 70)

        print(
            "TradingAI - "
            "INTRADAY OPTION HISTORY COLLECTOR"
        )

        print("=" * 70)

        print(
            f"Symbol: {self.symbol}"
        )

        print(
            f"Interval: "
            f"{self.interval_seconds // 60} minutes"
        )

        print(
            "Market window: "
            "09:15 - 15:30"
        )

        print(
            "Timezone: Asia/Kolkata"
        )

        print(
            "Press Ctrl+C to stop."
        )

        # ----------------------------------------------------
        # Wait for market
        # ----------------------------------------------------

        if not self.wait_until_open():

            return

        print(
            "\n[OPTION-HISTORY] "
            "Market is OPEN."
        )

        # ----------------------------------------------------
        # Immediate first snapshot
        # ----------------------------------------------------

        self.fetch_snapshot()

        # ----------------------------------------------------
        # Continuous collection
        # ----------------------------------------------------

        while self.running:

            if (
                self.market_status()
                != "OPEN"
            ):

                print(
                    "\n[OPTION-HISTORY] "
                    "Market closed."
                )

                break

            if not self.wait_for_next_interval():

                break

            if (
                self.market_status()
                != "OPEN"
            ):

                break

            self.fetch_snapshot()

        print(
            "\n[OPTION-HISTORY] "
            "Collector stopped."
        )

        print(
            f"[OPTION-HISTORY] "
            f"Snapshots collected: "
            f"{self.snapshot_count}"
        )

        try:

            self.source.close()

        except Exception:

            pass


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    collector = (
        OptionHistoryCollector()
    )

    signal.signal(
        signal.SIGINT,
        collector.stop,
    )

    signal.signal(
        signal.SIGTERM,
        collector.stop,
    )

    try:

        collector.run()

    except KeyboardInterrupt:

        collector.stop()

    finally:

        try:

            collector.source.close()

        except Exception:

            pass