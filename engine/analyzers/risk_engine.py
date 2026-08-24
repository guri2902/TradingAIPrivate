class RiskEngine:

    def calculate(

        self,

        trade,

        spot,

        capital=50000,

        risk_percent=1

    ):

        premium = trade["premium"]

        # -----------------------------
        # Stop Loss
        # -----------------------------

        sl = premium * 0.85

        # -----------------------------
        # Targets
        # -----------------------------

        target1 = premium * 1.20
        target2 = premium * 1.40
        target3 = premium * 1.70

        # -----------------------------
        # Risk Reward
        # -----------------------------

        risk = premium - sl
        reward = target2 - premium

        if risk == 0:
            rr = 0
        else:
            rr = reward / risk

        # -----------------------------
        # Max Loss
        # -----------------------------

        max_loss = capital * (risk_percent / 100)

        # -----------------------------
        # Position Size
        # -----------------------------

        if risk > 0:

            qty = int(max_loss / risk)

        else:

            qty = 0

        return {

            "entry": round(premium, 2),

            "sl": round(sl, 2),

            "target1": round(target1, 2),

            "target2": round(target2, 2),

            "target3": round(target3, 2),

            "rr": round(rr, 2),

            "position_size": qty,

            "max_loss": round(max_loss, 2)

        }