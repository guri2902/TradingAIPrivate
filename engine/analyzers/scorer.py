from engine.analyzers.volume import VolumeAnalyzer
from engine.analyzers.oi import OIAnalyzer
from engine.analyzers.iv import IVAnalyzer


class AIScorer:

    def __init__(self):

        self.volume = VolumeAnalyzer()

        self.oi = OIAnalyzer()

        self.iv = IVAnalyzer()

    def score(self, strike):

        volume_score = self.volume.score(strike)

        oi_score = self.oi.score(strike)

        iv_score = self.iv.score(strike)

        total = (
            volume_score
            + oi_score
            + iv_score
        )

        return {

            "strike": strike["strike"],

            "ce_ltp": strike["ce_ltp"],

            "score": total,

            "volume": volume_score,

            "oi": oi_score,

            "iv": iv_score
        }