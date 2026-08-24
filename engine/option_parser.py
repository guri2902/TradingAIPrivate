class OptionParser:

    def parse(self, data):

        parsed = []

        rows = data["records"]["data"]

        for row in rows:

            strike = row["strikePrice"]

            ce = row.get("CE", {})
            pe = row.get("PE", {})

            parsed.append({

                "strike": strike,

                # CALL
                "ce_ltp": ce.get("lastPrice", 0),
                "ce_oi": ce.get("openInterest", 0),
                "ce_change_oi": ce.get("changeinOpenInterest", 0),
                "ce_volume": ce.get("totalTradedVolume", 0),
                "ce_iv": ce.get("impliedVolatility", 0),

                # PUT
                "pe_ltp": pe.get("lastPrice", 0),
                "pe_oi": pe.get("openInterest", 0),
                "pe_change_oi": pe.get("changeinOpenInterest", 0),
                "pe_volume": pe.get("totalTradedVolume", 0),
                "pe_iv": pe.get("impliedVolatility", 0),

            })

        return parsed