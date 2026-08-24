class SupportResistance:

    def analyze(self, rows):

        ce_sorted = sorted(
            rows,
            key=lambda x: x["ce_oi"],
            reverse=True
        )

        pe_sorted = sorted(
            rows,
            key=lambda x: x["pe_oi"],
            reverse=True
        )

        resistance = [
            {
                "strike": r["strike"],
                "oi": r["ce_oi"]
            }
            for r in ce_sorted[:3]
        ]

        support = [
            {
                "strike": r["strike"],
                "oi": r["pe_oi"]
            }
            for r in pe_sorted[:3]
        ]

        total_ce = sum(r["ce_oi"] for r in rows)
        total_pe = sum(r["pe_oi"] for r in rows)

        pcr = round(
            total_pe / total_ce,
            2
        ) if total_ce else 0

        max_pain = max(
            rows,
            key=lambda x: x["ce_oi"] + x["pe_oi"]
        )["strike"]

        return {

            "support": support,

            "resistance": resistance,

            "pcr": pcr,

            "max_pain": max_pain

        }