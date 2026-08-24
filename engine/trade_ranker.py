class TradeRanker:

    def rank_trade(
        self,
        option_type,
        strike,
        spot,
        market,
        multi_tf,
        smc,
        chain,
        greeks,
        risk=None,
        option_data=None,
        flow=None,
        unified_context=None,
    ):

        score = 0
        reasons = []
        warnings = []

        unified_context = (
            unified_context
            if isinstance(
                unified_context,
                dict,
            )
            else {}
        )

        # ==================================================
        # 1. MARKET DIRECTION — 20 POINTS
        # ==================================================

        trend = market.get("trend")

        if option_type == "CE":

            if trend == "Bullish":
                score += 20
                reasons.append(
                    "Market trend supports CE"
                )

            elif trend == "Bearish":
                score -= 15
                warnings.append(
                    "Market trend is bearish"
                )

            else:
                score += 8

        else:

            if trend == "Bearish":
                score += 20
                reasons.append(
                    "Market trend supports PE"
                )

            elif trend == "Bullish":
                score -= 15
                warnings.append(
                    "Market trend is bullish"
                )

            else:
                score += 8

        # ==================================================
        # 2. MULTI TIMEFRAME — 15 POINTS
        # ==================================================

        overall = (
            multi_tf.get("overall")
            if multi_tf
            else None
        )

        if option_type == "CE":

            if overall == "Bullish":
                score += 15
                reasons.append(
                    "Multiple timeframes bullish"
                )

            elif overall == "Bearish":
                score -= 10
                warnings.append(
                    "Higher timeframes bearish"
                )

            else:
                score += 5

        else:

            if overall == "Bearish":
                score += 15
                reasons.append(
                    "Multiple timeframes bearish"
                )

            elif overall == "Bullish":
                score -= 10
                warnings.append(
                    "Higher timeframes bullish"
                )

            else:
                score += 5

        # ==================================================
        # 3. EMA — 10 POINTS
        # ==================================================

        ema20 = market.get("ema20")
        ema50 = market.get("ema50")
        ema200 = market.get("ema200")

        if None not in (
            ema20,
            ema50,
            ema200,
        ):

            if (
                option_type == "CE"
                and ema20 > ema50
            ):
                score += 10
                reasons.append(
                    "EMA momentum bullish"
                )

            elif (
                option_type == "PE"
                and ema20 < ema50
            ):
                score += 10
                reasons.append(
                    "EMA momentum bearish"
                )

        # ==================================================
        # 4. RSI — 5 POINTS
        # ==================================================

        rsi = market.get("rsi")

        if rsi is not None:

            if (
                option_type == "CE"
                and 50 <= rsi <= 68
            ):
                score += 5
                reasons.append(
                    "RSI supports bullish momentum"
                )

            elif (
                option_type == "PE"
                and 32 <= rsi <= 50
            ):
                score += 5
                reasons.append(
                    "RSI supports bearish momentum"
                )

        # ==================================================
        # 5. MACD — 10 POINTS
        # ==================================================

        macd = market.get("macd")
        signal = market.get("signal")

        if (
            macd is not None
            and signal is not None
        ):

            if (
                option_type == "CE"
                and macd > signal
            ):
                score += 10
                reasons.append(
                    "MACD bullish"
                )

            elif (
                option_type == "PE"
                and macd < signal
            ):
                score += 10
                reasons.append(
                    "MACD bearish"
                )

        # ==================================================
        # 6. OPTION DELTA — 10 POINTS
        # ==================================================

        delta = abs(
            greeks.get(
                "delta",
                0
            )
        )

        if 0.45 <= delta <= 0.60:

            score += 10

            reasons.append(
                "Delta near ideal directional range"
            )

        elif (
            0.35 <= delta < 0.45
            or 0.60 < delta <= 0.70
        ):

            score += 6

        elif delta < 0.25:

            score -= 5

            warnings.append(
                "Very low delta"
            )

        # ==================================================
        # 7. DISTANCE FROM ATM — 10 POINTS
        # ==================================================

        distance = abs(
            strike - spot
        )

        if distance <= 50:

            score += 10

            reasons.append(
                "Strike close to ATM"
            )

        elif distance <= 100:

            score += 7

        elif distance <= 150:

            score += 4

        else:

            score -= 3

            warnings.append(
                "Strike far from spot"
            )

        # ==================================================
        # 8. PREMIUM — 5 POINTS
        # ==================================================

        premium = 0

        if option_data:

            premium = (
                option_data.get(
                    "ce_ltp",
                    0
                )
                if option_type == "CE"
                else option_data.get(
                    "pe_ltp",
                    0
                )
            )

        if premium > 0:

            if premium >= 50:

                score += 5

                reasons.append(
                    "Premium suitable for directional trade"
                )

            elif premium >= 20:

                score += 3

            else:

                score -= 2

                warnings.append(
                    "Very low premium"
                )

        # ==================================================
        # 9. OPEN INTEREST — 5 POINTS
        # ==================================================

        if option_data:

            oi = (
                option_data.get(
                    "ce_oi",
                    0
                )
                if option_type == "CE"
                else option_data.get(
                    "pe_oi",
                    0
                )
            )

            if oi > 0:

                score += 5

                reasons.append(
                    "Open interest available"
                )

        # ==================================================
        # 10. SMC — 10 POINTS
        # ==================================================

        structure = (
            smc.get(
                "structure"
            )
            if smc
            else None
        )

        if option_type == "CE":

            if structure == "Bullish Breakout":

                score += 10

                reasons.append(
                    "SMC bullish breakout"
                )

            elif structure == "Bearish Breakdown":

                score -= 10

                warnings.append(
                    "SMC bearish structure"
                )

        else:

            if structure == "Bearish Breakdown":

                score += 10

                reasons.append(
                    "SMC bearish breakdown"
                )

            elif structure == "Bullish Breakout":

                score -= 10

                warnings.append(
                    "SMC bullish structure"
                )

        # ==================================================
        # 11. UNIFIED ML — 15 POINTS
        #
        # Uses the already-trained unified ML output.
        # This is a SCORE contribution, not a probability
        # calibration.
        # ==================================================

        ml = (
            unified_context.get(
                "ml",
                {}
            )
            if unified_context
            else {}
        )

        ml_direction = str(
            ml.get(
                "signal",
                ""
            )
        ).upper()

        ml_direction_probability = 0.0

        if option_type == "CE":

            ml_direction_probability = float(
                ml.get(
                    "up_probability",
                    0.0
                )
                or 0.0
            )

        else:

            ml_direction_probability = float(
                ml.get(
                    "down_probability",
                    0.0
                )
                or 0.0
            )

        ml_score = 0

        # Strong directional ML support.
        if ml_direction_probability >= 0.60:

            ml_score += 8

            reasons.append(
                "Unified ML supports option direction"
            )

        elif ml_direction_probability >= 0.50:

            ml_score += 4

        elif (

            ml_direction
            and ml_direction != "UNAVAILABLE"
            and ml_direction_probability <= 0.40
        ):
            ml_score -= 5

            warnings.append(
                "Unified ML conflicts with option direction"
            )

        # Regime confirmation.
        regime = str(
            ml.get(
                "regime_prediction",
                ""
            )
        ).upper()

        if option_type == "CE":

            if regime == "BULL":
                ml_score += 4

            elif regime == "BEAR":
                ml_score -= 4

        else:

            if regime == "BEAR":
                ml_score += 4

            elif regime == "BULL":
                ml_score -= 4

        # Keep ML contribution bounded.
        ml_score = max(
            -12,
            min(
                12,
                ml_score
            )
        )

        score += ml_score

        # ==================================================
        # 12. FUTURES CONFIRMATION — 10 POINTS
        # ==================================================

        futures = (
            unified_context.get(
                "futures",
                {}
            )
            if unified_context
            else {}
        )

        futures_latest = (
            futures.get(
                "latest",
                {}
            )
            if isinstance(
                futures,
                dict
            )
            else {}
        )

        futures_score = 0

        if (
            futures.get(
                "available",
                False
            )
            and isinstance(
                futures_latest,
                dict
            )
        ):

            futures_open = futures_latest.get(
                "open"
            )

            futures_close = futures_latest.get(
                "close"
            )

            futures_oi_change = futures_latest.get(
                "oi_change"
            )

            try:

                futures_open = float(
                    futures_open
                )

                futures_close = float(
                    futures_close
                )

                futures_oi_change = float(
                    futures_oi_change
                    or 0
                )

                futures_direction = (
                    "BULLISH"
                    if futures_close > futures_open
                    else (
                        "BEARISH"
                        if futures_close < futures_open
                        else "NEUTRAL"
                    )
                )

                if (
                    option_type == "CE"
                    and futures_direction == "BULLISH"
                ):

                    futures_score += 5

                    reasons.append(
                        "Futures price supports CE"
                    )

                elif (
                    option_type == "PE"
                    and futures_direction == "BEARISH"
                ):

                    futures_score += 5

                    reasons.append(
                        "Futures price supports PE"
                    )

                elif (
                    option_type == "CE"
                    and futures_direction == "BEARISH"
                ):

                    futures_score -= 5

                    warnings.append(
                        "Futures price conflicts with CE"
                    )

                elif (
                    option_type == "PE"
                    and futures_direction == "BULLISH"
                ):

                    futures_score -= 5

                    warnings.append(
                        "Futures price conflicts with PE"
                    )

                # OI confirmation.
                #
                # Positive OI change with the day's price direction
                # is treated as additional directional confirmation.
                if (
                    futures_direction == "BULLISH"
                    and futures_oi_change > 0
                    and option_type == "CE"
                ):

                    futures_score += 3

                elif (
                    futures_direction == "BEARISH"
                    and futures_oi_change > 0
                    and option_type == "PE"
                ):

                    futures_score += 3

            except (
                TypeError,
                ValueError,
            ):

                pass

        futures_score = max(
            -8,
            min(
                8,
                futures_score
            )
        )

        score += futures_score

        # ==================================================
        # FINAL SCORE
        # ==================================================

        score = max(
            0,
            min(
                100,
                score
            )
        )

        # ==================================================
        # ESTIMATED PROBABILITY
        # ==================================================
        #
        # IMPORTANT:
        # This remains the existing heuristic probability.
        # Step 8 will later calibrate it against real outcomes.
        # Unified ML/Futures are NOT used to silently alter it.
        # ==================================================

        probability = round(
            45 + (
                score * 0.35
            )
        )

        probability = max(
            45,
            min(
                80,
                probability
            )
        )

        return {

            "score":
                round(
                    score,
                    2
                ),

            "probability":
                probability,

            "reasons":
                reasons,

            "warnings":
                warnings,

            # Useful for debugging / transparency.
            "unified_components": {

                "ml_score":
                    ml_score,

                "ml_direction_probability":
                    round(
                        ml_direction_probability,
                        4
                    ),

                "ml_signal":
                    ml_direction,

                "ml_regime":
                    regime,

                "futures_score":
                    futures_score,

            },

        }