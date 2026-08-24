class ChainAnalyzer:

    def analyze(self, rows):

        total_ce_oi = 0
        total_pe_oi = 0

        total_ce_volume = 0
        total_pe_volume = 0

        max_ce = None
        max_pe = None

        max_ce_oi = 0
        max_pe_oi = 0

        max_pain = None
        max_combined = 0

        for row in rows:

            ce_oi = row["ce_oi"]
            pe_oi = row["pe_oi"]

            total_ce_oi += ce_oi
            total_pe_oi += pe_oi

            total_ce_volume += row["ce_volume"]
            total_pe_volume += row["pe_volume"]

            if ce_oi > max_ce_oi:

                max_ce_oi = ce_oi
                max_ce = row["strike"]

            if pe_oi > max_pe_oi:

                max_pe_oi = pe_oi
                max_pe = row["strike"]

            combined = ce_oi + pe_oi

            if combined > max_combined:

                max_combined = combined
                max_pain = row["strike"]

        pcr = round(
            total_pe_oi / max(total_ce_oi, 1),
            2
        )

        if pcr > 1.1:

            bias = "Bullish"

        elif pcr < 0.9:

            bias = "Bearish"

        else:

            bias = "Neutral"

        return {

            "pcr": pcr,

            "bias": bias,

            "support": max_pe,

            "resistance": max_ce,

            "max_pain": max_pain,

            "total_ce_oi": total_ce_oi,

            "total_pe_oi": total_pe_oi,

            "total_ce_volume": total_ce_volume,

            "total_pe_volume": total_pe_volume

        }