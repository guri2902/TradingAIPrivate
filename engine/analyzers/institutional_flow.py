class InstitutionalFlow:

    def analyze(self, row):

        reasons = []

        ce_flow = "Neutral"
        pe_flow = "Neutral"

        ce_change = row["ce_change_oi"]
        pe_change = row["pe_change_oi"]

        ce_volume = row["ce_volume"]
        pe_volume = row["pe_volume"]

        ce_price = row["ce_ltp"]
        pe_price = row["pe_ltp"]

        # =====================================
        # CALL SIDE
        # =====================================

        if ce_change > 10000 and ce_volume > 100000:

            if ce_price > 0:

                ce_flow = "Call Writing"

                reasons.append(
                    "Heavy Call Writing"
                )

        elif ce_change < -5000:

            ce_flow = "Call Unwinding"

            reasons.append(
                "Call Unwinding"
            )

        # =====================================
        # PUT SIDE
        # =====================================

        if pe_change > 10000 and pe_volume > 100000:

            if pe_price > 0:

                pe_flow = "Put Writing"

                reasons.append(
                    "Heavy Put Writing"
                )

        elif pe_change < -5000:

            pe_flow = "Put Unwinding"

            reasons.append(
                "Put Unwinding"
            )

        # =====================================

        if ce_flow == "Call Writing" and pe_flow == "Put Unwinding":

            bias = "Bearish"

        elif pe_flow == "Put Writing" and ce_flow == "Call Unwinding":

            bias = "Bullish"

        else:

            bias = "Neutral"

        return {

            "bias": bias,

            "ce_flow": ce_flow,

            "pe_flow": pe_flow,

            "reasons": reasons

        }