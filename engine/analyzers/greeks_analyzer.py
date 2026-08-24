import math


class GreeksAnalyzer:

    def __init__(self):
        pass

    # -------------------------------------------------

    def _norm_cdf(self, x):
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    # -------------------------------------------------

    def analyze(
        self,
        spot,
        strike,
        iv,
        premium,
        days_to_expiry,
        option_type="CE",
        risk_free_rate=0.06
    ):

        try:

            if (
                premium <= 0
                or iv <= 0
                or days_to_expiry <= 0
            ):
                raise Exception()

            sigma = iv / 100

            t = days_to_expiry / 365

            d1 = (
                math.log(spot / strike)
                + (
                    risk_free_rate
                    + sigma ** 2 / 2
                ) * t
            ) / (sigma * math.sqrt(t))

            d2 = d1 - sigma * math.sqrt(t)

            pdf = (
                math.exp(-(d1 ** 2) / 2)
                / math.sqrt(2 * math.pi)
            )

            if option_type == "CE":

                delta = self._norm_cdf(d1)

                theta = (
                    -(spot * pdf * sigma)
                    / (2 * math.sqrt(t))
                )

            else:

                delta = self._norm_cdf(d1) - 1

                theta = (
                    -(spot * pdf * sigma)
                    / (2 * math.sqrt(t))
                )

            gamma = pdf / (
                spot
                * sigma
                * math.sqrt(t)
            )

            vega = (
                spot
                * pdf
                * math.sqrt(t)
            ) / 100

            return {

                "delta": round(delta, 3),

                "gamma": round(gamma, 4),

                "theta": round(theta, 2),

                "vega": round(vega, 2)

            }

        except:

            return {

                "delta": 0,

                "gamma": 0,

                "theta": 0,

                "vega": 0

            }