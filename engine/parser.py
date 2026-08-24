class OptionParser:

    def parse(self, data):

        records = data["records"]["data"]

        strikes = []

        for row in records:

            strike = {
                "strike": row.get("strikePrice"),

                "ce": row.get("CE"),

                "pe": row.get("PE")
            }

            strikes.append(strike)

        return strikes