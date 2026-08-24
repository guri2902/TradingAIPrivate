import pandas as pd
import numpy as np

from engine.market_data import MarketData
from engine.analyzers.market_analyzer import MarketAnalyzer
from engine.smc_analyzer import SMCAnalyzer
from engine.trade_ranker import TradeRanker


class BacktestEngine:

    def __init__(self, ce_file, pe_file):

        self.ce_file = ce_file
        self.pe_file = pe_file

        self.market_analyzer = MarketAnalyzer()
        self.smc_analyzer = SMCAnalyzer()
        self.ranker = TradeRanker()

        self.ce = self._load(ce_file)
        self.pe = self._load(pe_file)

    # =========================================================
    # LOAD NSE CSV
    # =========================================================

    def _load(self, filename):

        df = pd.read_csv(filename)

        # Remove spaces from column names
        df.columns = df.columns.str.strip()

        # Convert "-" to NaN
        df = df.replace("-", np.nan)

        # Dates
        df["Date"] = pd.to_datetime(df["Date"])
        df["Expiry"] = pd.to_datetime(df["Expiry"])

        numeric_columns = [
            "Strike Price",
            "Open",
            "High",
            "Low",
            "Close",
            "LTP",
            "Settle Price",
            "No. of contracts",
            "Turnover * in  ₹ Lakhs",
            "Premium Turnover ** in   ₹ Lakhs",
            "Open Int",
            "Change in OI",
            "Underlying Value"
        ]

        for col in numeric_columns:

            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

        df = df.sort_values(
            ["Date", "Expiry", "Strike Price"]
        )

        return df

    # =========================================================
    # DELTA PROXY
    # =========================================================

    def delta_proxy(
        self,
        option_type,
        strike,
        spot
    ):

        """
        IMPORTANT:

        This is NOT a real option Greek.

        It is only being used because the NSE daily
        CSV does not contain historical Delta.

        Later we should replace this with actual
        historical IV/Delta.
        """

        distance = spot - strike

        if option_type == "PE":
            distance = -distance

        delta = 0.50 + (
            0.25 * np.tanh(distance / 100)
        )

        return round(
            float(np.clip(delta, 0.25, 0.75)),
            3
        )

    # =========================================================
    # MARKET ANALYSIS
    # =========================================================

    def get_market_context(
        self,
        date,
        underlying_history
    ):

        candles = underlying_history[
            underlying_history["Date"] <= date
        ].copy()

        if len(candles) < 200:
            return None

        candles = candles.set_index("Date")

        market = self.market_analyzer.analyze(
            candles
        )

        smc = self.smc_analyzer.analyze(
            candles
        )

        # -----------------------------------------------------
        # First version:
        # Daily trend represents the available timeframe.
        #
        # We do NOT pretend that daily data is real 5m/15m/1h.
        # -----------------------------------------------------

        multi_tf = {

            "overall": market["trend"],

            "confidence": 100,

            "bull": 1 if market["trend"] == "Bullish" else 0,

            "bear": 1 if market["trend"] == "Bearish" else 0,

            "sideways": (
                1
                if market["trend"] == "Sideways"
                else 0
            ),

            "frames": {

                "daily": market["trend"]

            }

        }

        return {
            "market": market,
            "smc": smc,
            "multi_tf": multi_tf,
            "candles": candles
        }

    # =========================================================
    # OPTION CHAIN FOR DATE
    # =========================================================

    def get_chain(
        self,
        date
    ):

        ce = self.ce[
            self.ce["Date"] == date
        ].copy()

        pe = self.pe[
            self.pe["Date"] == date
        ].copy()

        return ce, pe

    # =========================================================
    # FIND BEST OPTION
    # =========================================================

    def rank_options(
        self,
        date,
        market_context
    ):

        market = market_context["market"]
        smc = market_context["smc"]
        multi_tf = market_context["multi_tf"]

        spot = market["price"]

        ce, pe = self.get_chain(date)

        candidates = []

        # =====================================================
        # CE
        # =====================================================

        for _, row in ce.iterrows():

            strike = row["Strike Price"]
            premium = row["Close"]

            if pd.isna(strike) or pd.isna(premium):
                continue

            if premium <= 0:
                continue

            distance = abs(
                strike - spot
            )

            # Keep reasonably close strikes
            if distance > 200:
                continue

            delta = self.delta_proxy(
                "CE",
                strike,
                spot
            )

            option_data = {

                "ce_ltp": premium,

                "pe_ltp": 0,

                "ce_oi": (
                    row["Open Int"]
                    if not pd.isna(row["Open Int"])
                    else 0
                ),

                "pe_oi": 0,

                "ce_volume": (
                    row["No. of contracts"]
                    if not pd.isna(
                        row["No. of contracts"]
                    )
                    else 0
                )

            }

            greeks = {
                "delta": delta
            }

            ranking = self.ranker.rank_trade(

                option_type="CE",

                strike=strike,

                spot=spot,

                market=market,

                multi_tf=multi_tf,

                smc=smc,

                chain={},

                greeks=greeks,

                risk=None,

                option_data=option_data,

                flow=None
            )

            candidates.append({

                "date": date,

                "option_type": "CE",

                "strike": strike,

                "premium": premium,

                "delta": delta,

                "ranking": ranking,

                "row": row

            })

        # =====================================================
        # PE
        # =====================================================

        for _, row in pe.iterrows():

            strike = row["Strike Price"]
            premium = row["Close"]

            if pd.isna(strike) or pd.isna(premium):
                continue

            if premium <= 0:
                continue

            distance = abs(
                strike - spot
            )

            if distance > 200:
                continue

            delta = self.delta_proxy(
                "PE",
                strike,
                spot
            )

            option_data = {

                "ce_ltp": 0,

                "pe_ltp": premium,

                "ce_oi": 0,

                "pe_oi": (
                    row["Open Int"]
                    if not pd.isna(row["Open Int"])
                    else 0
                ),

                "pe_volume": (
                    row["No. of contracts"]
                    if not pd.isna(
                        row["No. of contracts"]
                    )
                    else 0
                )

            }

            greeks = {
                "delta": delta
            }

            ranking = self.ranker.rank_trade(

                option_type="PE",

                strike=strike,

                spot=spot,

                market=market,

                multi_tf=multi_tf,

                smc=smc,

                chain={},

                greeks=greeks,

                risk=None,

                option_data=option_data,

                flow=None
            )

            candidates.append({

                "date": date,

                "option_type": "PE",

                "strike": strike,

                "premium": premium,

                "delta": delta,

                "ranking": ranking,

                "row": row

            })

        if not candidates:
            return None

        # =====================================================
        # SORT BY AI SCORE
        # =====================================================

        candidates.sort(
            key=lambda x: x["ranking"]["score"],
            reverse=True
        )

        return candidates[0]

    # =========================================================
    # FIND NEXT DAY CONTRACT
    # =========================================================

    def get_next_day_row(
        self,
        trade,
        next_date
    ):

        df = (
            self.ce
            if trade["option_type"] == "CE"
            else self.pe
        )

        rows = df[
            (df["Date"] == next_date) &
            (df["Strike Price"] == trade["strike"]) &
            (df["Expiry"] == trade["row"]["Expiry"])
        ]

        if rows.empty:
            return None

        return rows.iloc[0]

    # =========================================================
    # SIMULATE TRADE
    # =========================================================

    def simulate_trade(
        self,
        trade,
        next_row
    ):

        entry = float(
            trade["premium"]
        )

        score = trade["ranking"]["score"]

        # Same SL/targets logic as your system
        stop_loss = entry * 0.85

        target1 = entry * 1.20

        target2 = entry * 1.40

        high = next_row["High"]
        low = next_row["Low"]
        close = next_row["Close"]

        if pd.isna(high):
            high = close

        if pd.isna(low):
            low = close

        result = "EXIT"

        exit_price = close

        # -----------------------------------------------------
        # Daily data cannot tell whether SL or target happened
        # first if BOTH occurred.
        #
        # Conservative assumption:
        # SL wins when both are hit.
        # -----------------------------------------------------

        if low <= stop_loss:

            result = "LOSS"

            exit_price = stop_loss

        elif high >= target2:

            result = "TARGET2"

            exit_price = target2

        elif high >= target1:

            result = "TARGET1"

            exit_price = target1

        pnl = exit_price - entry

        return {

            "entry": round(entry, 2),

            "exit": round(exit_price, 2),

            "stop_loss": round(
                stop_loss,
                2
            ),

            "target1": round(
                target1,
                2
            ),

            "target2": round(
                target2,
                2
            ),

            "result": result,

            "pnl": round(pnl, 2),

            "score": score,

            "probability": (
                trade["ranking"]["probability"]
            )

        }

    # =========================================================
    # RUN BACKTEST
    # =========================================================

    def run(self):

        # -----------------------------------------------------
        # Underlying daily data
        # -----------------------------------------------------

        underlying = pd.concat([

            self.ce[
                [
                    "Date",
                    "Underlying Value"
                ]
            ],

            self.pe[
                [
                    "Date",
                    "Underlying Value"
                ]
            ]

        ])

        underlying = (
            underlying
            .drop_duplicates("Date")
            .rename(
                columns={
                    "Underlying Value": "Close"
                }
            )
            .sort_values("Date")
        )

        underlying["Open"] = underlying["Close"]
        underlying["High"] = underlying["Close"]
        underlying["Low"] = underlying["Close"]
        underlying["Volume"] = 0

        dates = sorted(
            underlying["Date"].unique()
        )

        results = []

        # Need enough history for EMA200
        for i, date in enumerate(dates):

            if i < 200:
                continue

            # Need next trading day
            if i + 1 >= len(dates):
                break

            next_date = dates[i + 1]

            context = self.get_market_context(
                date,
                underlying
            )

            if context is None:
                continue

            trade = self.rank_options(
                date,
                context
            )

            if trade is None:
                continue

            # -------------------------------------------------
            # Only take meaningful signals
            # -------------------------------------------------

            if trade["ranking"]["score"] < 65:

                results.append({

                    "date": date,

                    "status": "NO TRADE",

                    "reason": "Score below 65",

                    "best_side":
                        trade["option_type"],

                    "strike":
                        trade["strike"],

                    "score":
                        trade["ranking"]["score"]

                })

                continue

            next_row = self.get_next_day_row(
                trade,
                next_date
            )

            if next_row is None:
                continue

            simulation = self.simulate_trade(
                trade,
                next_row
            )

            results.append({

                "date": date,

                "next_date": next_date,

                "option_type":
                    trade["option_type"],

                "strike":
                    trade["strike"],

                "spot":
                    context["market"]["price"],

                "score":
                    simulation["score"],

                "probability":
                    simulation["probability"],

                "entry":
                    simulation["entry"],

                "exit":
                    simulation["exit"],

                "stop_loss":
                    simulation["stop_loss"],

                "target1":
                    simulation["target1"],

                "target2":
                    simulation["target2"],

                "result":
                    simulation["result"],

                "pnl":
                    simulation["pnl"],

                "reasons":
                    " | ".join(
                        trade["ranking"]["reasons"]
                    )

            })

        return pd.DataFrame(results)