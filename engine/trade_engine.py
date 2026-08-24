from __future__ import annotations

from typing import Any, Dict, List, Optional
import math

from engine.option_chain import OptionChain
from engine.option_parser import OptionParser

from engine.scoring import AIScore
from engine.analyzers.market_analyzer import MarketAnalyzer
from engine.analyzers.multi_timeframe import MultiTimeframeAnalyzer
from engine.analyzers.option_analyzer import OptionAnalyzer
from engine.analyzers.chain_analyzer import ChainAnalyzer
from engine.analyzers.institutional_flow import InstitutionalFlow
from engine.analyzers.risk_engine import RiskEngine
from engine.analyzers.support_resistance import SupportResistance
from engine.analyzers.smc_analyzer import SMCAnalyzer
from engine.strategy_engine import StrategyEngine
from engine.market_data import MarketData
from engine.analyzers.pattern_analyzer import PatternAnalyzer
from engine.analyzers.volume_profile import VolumeProfile
from engine.analyzers.greeks_analyzer import GreeksAnalyzer
from engine.trade_ranker import TradeRanker
from data_engine.tradingai_engine import TradingAIEngine


class TradeEngine:

    INDEX_CONFIG = {
        "NIFTY 50": {
            "symbol": "NIFTY",
            "candle_methods": [
                "get_nifty_candles",
            ],
        },

        "BANK NIFTY": {
            "symbol": "BANKNIFTY",
            "candle_methods": [
                "get_banknifty_candles",
                "get_bank_nifty_candles",
            ],
        },

        "FINNIFTY": {
            "symbol": "FINNIFTY",
            "candle_methods": [
                "get_finnifty_candles",
                "get_fin_nifty_candles",
            ],
        },

        "MIDCAP NIFTY": {
            "symbol": "MIDCPNIFTY",
            "candle_methods": [
                "get_midcapnifty_candles",
                "get_midcap_nifty_candles",
                "get_midcpnifty_candles",
            ],
        },
    }
    CAPITAL = 50_000
    RISK_PERCENT = 1.0

    DAYS_TO_EXPIRY = 5
    NEARBY_STRIKES = 5
    TOP_TRADES = 5

    def __init__(self):

        self.market = MarketData()
        self.pattern_ai = PatternAnalyzer()

        self.chain = OptionChain()
        self.parser = OptionParser()

        self.smc_ai = SMCAnalyzer()
        self.market_ai = MarketAnalyzer()
        self.multi_tf = MultiTimeframeAnalyzer()

        self.option_ai = OptionAnalyzer()
        self.chain_ai = ChainAnalyzer()
        self.flow_ai = InstitutionalFlow()

        self.risk_ai = RiskEngine()
        self.sr_ai = SupportResistance()

        self.volume_profile = VolumeProfile()
        self.greeks_ai = GreeksAnalyzer()

        self.strategy = StrategyEngine()
        self.ranker = TradeRanker()

        # --------------------------------------------------------
        # STEP 3 - UNIFIED DATA / ML / OPTIONS / FUTURES
        # --------------------------------------------------------
        self.unified_ai = TradingAIEngine()

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def num(value, default=0.0):

        try:
            if value is None:
                return default

            value = float(value)

            if not math.isfinite(value):
                return default

            return value

        except (TypeError, ValueError):
            return default

    @staticmethod
    def pcr_bias(pcr):

        if pcr < 0.90:
            return "Bearish"

        if pcr > 1.10:
            return "Bullish"

        return "Neutral"

    @staticmethod
    def direction_alignment(option_type, bias):

        bias = str(bias).lower()

        if option_type == "PE":

            if bias == "bearish":
                return 12

            if bias == "bullish":
                return -12

        else:

            if bias == "bullish":
                return 12

            if bias == "bearish":
                return -12

        return 0

    def get_nearby(
        self,
        rows,
        spot,
        count=None
    ):

        count = (
            self.NEARBY_STRIKES
            if count is None
            else count
        )

        rows = [
            r for r in rows
            if isinstance(r, dict)
            and r.get("strike") is not None
        ]

        rows.sort(
            key=lambda x: abs(
                self.num(x.get("strike")) - spot
            )
        )

        return rows[:count * 2 + 1]

    # ============================================================
    # MARKET SCORE
    # ============================================================

    def _load_unified_context(
        self,
        symbol,
    ):
        """
        Load the already-built unified TradingAI state.

        The unified engine is the source of truth for the combined
        ML/options/futures context. No new numeric scoring formula is
        introduced here.
        """

        try:
            result = self.unified_ai.analyze(
                symbol
            )

            if not isinstance(
                result,
                dict,
            ):
                raise RuntimeError(
                    "Unified TradingAI result is not a dictionary."
                )

            return result

        except Exception as exc:

            print(
                "[TRADE ENGINE] Unified context unavailable:",
                exc,
            )

            return {
                "available": False,
                "error": str(exc),
                "ml": {},
                "options": {},
                "futures": {},
            }

    @staticmethod
    def _merge_unified_context(
        market,
        unified_context,
    ):
        """
        Keep the existing market-analysis values intact and attach
        the authoritative unified context for downstream consumers.
        """

        if not isinstance(
            market,
            dict,
        ):
            market = {}

        if not isinstance(
            unified_context,
            dict,
        ):
            unified_context = {}

        market["tradingai_context"] = unified_context
        market["tradingai_ml"] = unified_context.get(
            "ml",
            {},
        )
        market["tradingai_options"] = unified_context.get(
            "options",
            {},
        )
        market["tradingai_futures"] = unified_context.get(
            "futures",
            {},
        )

        return market

    def calculate_market_score(
        self,
        market,
        chain,
        pcr,
        multi_tf
    ):

        data = {
            "ema20": market.get("ema20"),
            "ema50": market.get("ema50"),
            "ema200": market.get("ema200"),

            "rsi": market.get("rsi"),

            "macd": market.get("macd"),

            "signal": market.get("signal"),

            "trend": market.get("trend"),

            "pcr": pcr,

            "oi_bias": chain.get("bias"),

            "mtf": multi_tf.get("overall")
        }

        raw = AIScore.calculate(data) or {}

        bull = self.num(raw.get("bull"))
        bear = self.num(raw.get("bear"))

        total = bull + bear

        if total > 0:

            separation = (
                abs(bull - bear) / total
            )

            confidence = (
                50 +
                separation * 45
            )

        else:

            confidence = 50

        technical_bias = raw.get(
            "bias",
            "Neutral"
        )

        pcr_bias = self.pcr_bias(pcr)

        if (
            technical_bias == pcr_bias
            and technical_bias != "Neutral"
        ):
            confidence += 5

        mtf = str(
            multi_tf.get(
                "overall",
                ""
            )
        ).lower()

        if (
            technical_bias != "Neutral"
            and technical_bias.lower() in mtf
        ):
            confidence += 3

        confidence = max(
            50,
            min(95, confidence)
        )

        return {
            "bull": bull,
            "bear": bear,
            "bias": technical_bias,
            "confidence": round(
                confidence,
                1
            ),
            "reasons": list(
                raw.get("reasons") or []
            )
        }

    # ============================================================
    # TRADE QUALITY
    # ============================================================

    def improve_trade_score(
        self,
        trade,
        market_score,
        chain,
        smc
    ):

        option_type = trade["type"]

        score = self.num(
            trade.get("ai_score")
        )

        adjustment = 0

        # --------------------------------------------------------
        # MARKET DIRECTION
        # --------------------------------------------------------

        adjustment += self.direction_alignment(
            option_type,
            market_score["bias"]
        )

        # --------------------------------------------------------
        # PCR
        # --------------------------------------------------------

        pcr = self.num(
            chain.get("pcr"),
            1
        )

        adjustment += (
            self.direction_alignment(
                option_type,
                self.pcr_bias(pcr)
            ) * 0.35
        )

        # --------------------------------------------------------
        # DELTA
        # --------------------------------------------------------

        delta = self.num(
            trade.get(
                "greeks",
                {}
            ).get("delta")
        )

        abs_delta = abs(delta)

        if 0.40 <= abs_delta <= 0.60:
            adjustment += 3

        elif (
            abs_delta < 0.25
            or abs_delta > 0.75
        ):
            adjustment -= 3

        # --------------------------------------------------------
        # SMC
        # --------------------------------------------------------

        smc_bias = str(
            smc.get(
                "bias",
                ""
            )
        ).lower()

        if option_type == "PE":

            if smc_bias == "bearish":
                adjustment += 5

            elif smc_bias == "bullish":
                adjustment -= 5

        else:

            if smc_bias == "bullish":
                adjustment += 5

            elif smc_bias == "bearish":
                adjustment -= 5

        # --------------------------------------------------------
        # FINAL SCORE
        # --------------------------------------------------------

        score = max(
            0,
            min(
                100,
                score + adjustment
            )
        )

        trade["ai_score"] = round(
            score,
            1
        )

        # Probability is intentionally NOT modified here.
        # It remains the authoritative value produced by TradeRanker.

        reasons = list(
            trade.get(
                "reasons"
            ) or []
        )

        warnings = list(
            trade.get(
                "warnings"
            ) or []
        )

        if adjustment >= 7:

            if (
                "Market bias supports option direction"
                not in reasons
            ):
                reasons.insert(
                    0,
                    "Market bias supports option direction"
                )

        if adjustment <= -7:

            warning = (
                "Option direction conflicts "
                "with market bias"
            )

            if warning not in warnings:
                warnings.append(warning)

        trade["reasons"] = reasons
        trade["warnings"] = warnings

    # ============================================================
    # RECOMMENDATION
    # ============================================================

    @staticmethod
    def recommendation(
        score,
        probability,
        warnings
    ):

        conflict = any(
            "conflicts"
            in str(w).lower()
            for w in warnings
        )

        if conflict and score < 70:
            return "⚠ AVOID"

        if (
            score >= 82
            and probability >= 70
        ):
            return "⭐⭐⭐⭐ STRONG SETUP"

        if (
            score >= 72
            and probability >= 65
        ):
            return "⭐⭐⭐ TRADEABLE SETUP"

        if (
            score >= 62
            and probability >= 60
        ):
            return "⭐⭐ WATCH"

        return "⚠ WEAK SETUP"

    # ============================================================
    # MAIN ENGINE
    # ============================================================

    def generate_trades(
        self,
        selected_index="NIFTY 50",
        expiry=None,
        *,
        candles=None,
        option_snapshot=None,
        multi_tf=None,
        unified_context=None,
        data_mode="live",
    ):
        """
        Run the same trade-analysis pipeline for live or historical data.

        Live mode preserves the existing NSE/MarketData behavior.
        Backtest mode accepts historical candles and an option snapshot,
        then runs the same market analysis, option analysis, Greeks,
        risk, ranking, probability and recommendation logic.
        """


        selected_index = self.normalize_index(
            selected_index
        )

        symbol = self.INDEX_CONFIG[
            selected_index
        ]["symbol"]
        print(
            f"Generating trades for: "
            f"{selected_index} | Expiry: {expiry}"
        )

        # ========================================================
        # MARKET
        # ========================================================

        if candles is None:
            candles = (
                self.get_candles_for_index(
                    selected_index
                )
            )

        if (
            candles is None
            or candles.empty
        ):
            raise RuntimeError(
                "Unable to fetch market candles."
            )

        market = (
            self.market_ai.analyze(
                candles
            )
            or {}
        )

        volume_profile = (
            self.volume_profile.analyze(
                candles
            )
            or {}
        )

        if multi_tf is None:
            multi_tf = (
                self.multi_tf.analyze()
                or {}
            )

        market["multi_tf"] = multi_tf

        smc = (
            self.smc_ai.analyze(
                candles
            )
            or {}
        )

        patterns = (
            self.pattern_ai.analyze(
                candles
            )
            or {}
        )

        strategy = (
            self.strategy.analyse(
                market
            )
            or {}
        )

        # --------------------------------------------------------
        # STEP 3 - MERGE UNIFIED ML / OPTIONS / FUTURES CONTEXT
        # --------------------------------------------------------
        if unified_context is None:
            unified_context = (
                self._load_unified_context(
                    symbol
                )
            )

        market = self._merge_unified_context(
            market,
            unified_context,
        )

        # ========================================================
        # OPTION CHAIN
        # ========================================================

        if option_snapshot is None:

            # LIVE: existing NSE option-chain path.
            data = self.chain.get_chain(
                symbol=selected_index,
                expiry=expiry
            )

            if not data:
                raise RuntimeError(
                    f"Unable to fetch {selected_index} option chain."
                )

            records = (
                data.get("records")
                or {}
            )

            spot = self.num(
                records.get(
                    "underlyingValue"
                )
            )

            if spot <= 0:
                raise RuntimeError(
                    f"Invalid {selected_index} spot price."
                )

            rows = (
                self.parser.parse(
                    data
                )
                or []
            )

        else:

            # BACKTEST / REPLAY: no NSE call.
            data = option_snapshot

            if (
                isinstance(
                    option_snapshot,
                    dict,
                )
                and "rows" in option_snapshot
            ):

                rows = list(
                    option_snapshot.get(
                        "rows"
                    )
                    or []
                )

                spot = self.num(
                    option_snapshot.get(
                        "spot"
                    ),
                    0,
                )

            elif isinstance(
                option_snapshot,
                dict,
            ):

                # Also accept a previously saved raw OptionChain
                # response and parse it with the existing parser.
                records = (
                    option_snapshot.get(
                        "records"
                    )
                    or {}
                )

                spot = self.num(
                    records.get(
                        "underlyingValue"
                    )
                )

                rows = (
                    self.parser.parse(
                        option_snapshot
                    )
                    or []
                )

            else:

                rows = []
                spot = 0

            if spot <= 0:
                raise RuntimeError(
                    f"Invalid {selected_index} "
                    f"historical option spot."
                )

        if not rows:
            raise RuntimeError(
                "Option chain returned no strikes."
            )

        chain = (
            self.chain_ai.analyze(
                rows
            )
            or {}
        )

        sr = (
            self.sr_ai.analyze(
                rows
            )
            or {}
        )

        pcr = self.num(
            sr.get("pcr"),
            self.num(
                chain.get("pcr"),
                1
            )
        )

        # ========================================================
        # MARKET SCORE
        # ========================================================

        market_score = (
            self.calculate_market_score(
                market,
                chain,
                pcr,
                multi_tf
            )
        )

        direction = market_score[
            "bias"
        ]

        if direction not in (
            "Bullish",
            "Bearish",
            "Neutral"
        ):
            direction = self.pcr_bias(
                pcr
            )

        # ========================================================
        # OPTIONS
        # ========================================================

        nearby = self.get_nearby(
            rows,
            spot
        )

        trades = []

        for strike_data in nearby:

            strike = self.num(
                strike_data.get(
                    "strike"
                )
            )

            if strike <= 0:
                continue

            for option_type in (
                "CE",
                "PE"
            ):

                if option_type == "CE":

                    premium = self.num(
                        strike_data.get(
                            "ce_ltp"
                        )
                    )

                    iv = self.num(
                        strike_data.get(
                            "ce_iv"
                        )
                    )

                else:

                    premium = self.num(
                        strike_data.get(
                            "pe_ltp"
                        )
                    )

                    iv = self.num(
                        strike_data.get(
                            "pe_iv"
                        )
                    )

                if premium <= 0:
                    continue

                # ------------------------------------------------
                # OPTION ANALYSIS
                # ------------------------------------------------

                trade = (
                    self.option_ai.analyze(
                        strike_data
                    )
                    or {}
                )

                trade["type"] = option_type
                trade["strike"] = strike
                trade["premium"] = premium

                # ------------------------------------------------
                # STEP 3 - UNIFIED CONTEXT
                # ------------------------------------------------
                trade["unified_context"] = unified_context

                # ------------------------------------------------
                # GREEKS
                # ------------------------------------------------

                greeks = (
                    self.greeks_ai.analyze(
                        spot=spot,
                        strike=strike,
                        iv=iv,
                        premium=premium,
                        days_to_expiry=self.DAYS_TO_EXPIRY,
                        option_type=option_type
                    )
                    or {}
                )

                trade["greeks"] = greeks

                # ------------------------------------------------
                # FLOW
                # ------------------------------------------------

                trade["flow"] = (
                    self.flow_ai.analyze(
                        strike_data
                    )
                    or {}
                )

                # ------------------------------------------------
                # RISK
                # ------------------------------------------------

                trade["risk"] = (
                    self.risk_ai.calculate(
                        trade,
                        spot,
                        capital=self.CAPITAL,
                        risk_percent=self.RISK_PERCENT
                    )
                    or {}
                )

                # ------------------------------------------------
                # RANKING
                # ------------------------------------------------

                ranking = (
                    self.ranker.rank_trade(
                        option_type=option_type,
                        strike=strike,
                        spot=spot,
                        market=market,
                        multi_tf=multi_tf,
                        smc=smc,
                        chain=chain,
                        greeks=greeks,
                        unified_context=unified_context,
                        risk=trade["risk"],
                        option_data=strike_data,
                        flow=trade["flow"]
                    )
                    or {}
                )

                trade["ai_score"] = self.num(
                    ranking.get("score")
                )

                trade["probability"] = self.num(
                    ranking.get(
                        "probability"
                    ),
                    50
                )

                # ------------------------------------------------
                # AUTHORITATIVE PROBABILITY
                #
                # TradeRanker is the single source of the initial
                # probability. Final quality adjustment may refine
                # ai_score, but must not silently mutate probability.
                # ------------------------------------------------
                trade["probability"] = round(
                    max(
                        0.0,
                        min(
                            100.0,
                            self.num(
                                trade.get(
                                    "probability",
                                    50
                                ),
                                50
                            )
                        )
                    ),
                    1
                )

                trade["reasons"] = list(
                    ranking.get(
                        "reasons"
                    )
                    or []
                )

                trade["warnings"] = list(
                    ranking.get(
                        "warnings"
                    )
                    or []
                )
                trade["unified_components"] = (
                    ranking.get(
                        "unified_components",
                        {}
                    )
                    or {}
                )

                # ------------------------------------------------
                # FINAL QUALITY
                # ------------------------------------------------

                self.improve_trade_score(
                    trade,
                    market_score,
                    chain,
                    smc
                )

                trade["support"] = (
                    sr["support"][0]["strike"]
                    if sr.get("support")
                    else None
                )

                trade["resistance"] = (
                    sr["resistance"][0]["strike"]
                    if sr.get("resistance")
                    else None
                )

                trade["max_pain"] = (
                    sr.get("max_pain")
                )

                trade["pcr"] = pcr
                trade["market_bias"] = direction

                trade["recommendation"] = (
                    self.recommendation(
                        trade["ai_score"],
                        trade["probability"],
                        trade["warnings"]
                    )
                )

                trades.append(
                    trade
                )

        if not trades:
            raise RuntimeError(
                "No valid CE/PE opportunities found."
            )

        # ========================================================
        # SORT
        # ========================================================

        trades.sort(
            key=lambda x: (
                self.num(
                    x.get("ai_score")
                ),
                self.num(
                    x.get("probability")
                )
            ),
            reverse=True
        )

        # ========================================================
        # RESULT
        # ========================================================

        return {

            "selected_index": selected_index,

            "symbol": symbol,

            "expiry": expiry,

            "spot": spot,

            "market": market,

            "multi_tf": multi_tf,

            "chain": chain,

            "smc": smc,

            "patterns": patterns,

            "strategy": strategy,

            "support_resistance": sr,

            "volume_profile": volume_profile,

            "unified_context": unified_context,

            "direction": direction,

            "confidence": market_score[
                "confidence"
            ],

            "bull_score": market_score[
                "bull"
            ],

            "bear_score": market_score[
                "bear"
            ],

            "reasons": market_score[
                "reasons"
            ],

            "trades": trades[
                :self.TOP_TRADES
            ],

            "all_trades": trades,

            # Informational only. Analysis/ranking/risk behavior is
            # identical in live and backtest modes.
            "data_mode": (
                str(data_mode)
                if data_mode
                else "live"
            ),
        }

    def generate_trades_from_snapshot(
        self,
        selected_index,
        candles,
        option_snapshot,
        expiry=None,
        multi_tf=None,
        unified_context=None,
    ):
        """
        Backtest/replay entry point.

        The exact same generate_trades() pipeline is used; only the
        input data is injected instead of fetched from the live sources.
        """
        return self.generate_trades(
            selected_index=selected_index,
            expiry=expiry,
            candles=candles,
            option_snapshot=option_snapshot,
            multi_tf=multi_tf,
            unified_context=unified_context,
            data_mode="backtest",
        )

    def normalize_index(self, selected_index):

        selected_index = str(
            selected_index or "NIFTY 50"
        ).strip().upper()

        aliases = {
            "NIFTY": "NIFTY 50",
            "NIFTY50": "NIFTY 50",
            "NIFTY 50": "NIFTY 50",

            "BANKNIFTY": "BANK NIFTY",
            "BANK NIFTY": "BANK NIFTY",

            "FINNIFTY": "FINNIFTY",
            "FIN NIFTY": "FINNIFTY",

            "MIDCAP NIFTY": "MIDCAP NIFTY",
            "MIDCAPNIFTY": "MIDCAP NIFTY",
            "MIDCPNIFTY": "MIDCAP NIFTY",
        }

        return aliases.get(
            selected_index,
            "NIFTY 50"
        )


    def get_candles_for_index(
        self,
        selected_index
    ):

        selected_index = self.normalize_index(
            selected_index
        )

        config = self.INDEX_CONFIG.get(
            selected_index
        )

        if not config:
            raise RuntimeError(
                f"Unsupported index: {selected_index}"
            )

        for method_name in config["candle_methods"]:

            method = getattr(
                self.market,
                method_name,
                None
            )

            if not callable(method):
                continue

            try:

                candles = method()

                if (
                    candles is not None
                    and not candles.empty
                ):

                    return candles

            except Exception as e:

                print(
                    f"{method_name} failed: {e}"
                )

        raise RuntimeError(
            f"MarketData does not currently provide "
            f"candles for {selected_index}."
        )