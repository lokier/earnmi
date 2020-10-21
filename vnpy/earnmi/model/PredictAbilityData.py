import math
from dataclasses import dataclass
from typing import Sequence

from earnmi.chart.FloatEncoder import FloatRange
from earnmi.uitl.utils import utils


@dataclass
class ModelAbilityData(object):
    count = 0
    scoreSell = 0.0
    scoreBuy = 0.0

    #正偏差
    biasSellWin = 0.0
    biasBuyWin = 0.0

    #负偏差
    biasSellLoss = 0.0
    biasBuyLoss = 0.0

    pass

@dataclass
class PredictAbilityData(object):

    trainData:ModelAbilityData = None
    testData:ModelAbilityData = None

    """
    预测值的pct值范围分布。
    """
    sellPctRnageList: Sequence["FloatRange"] = None
    buyPctRnageList: Sequence["FloatRange"] = None


    def getCount(self)->int:
        return int(self.trainData.count + self.testData.count)

    def getScoreSell(self)->float:
        return utils.keep_3_float((self.trainData.scoreSell + self.testData.scoreSell) / 2)

    def getScoreBuy(self)->float:
        return utils.keep_3_float((self.trainData.scoreBuy + self.testData.scoreBuy) / 2)

    """
    越低越好，最低为0
    """
    def getStabilitySell(self)->float:
        v1 = abs(self.trainData.scoreSell - self.testData.scoreSell)*10
        v2 = abs(self.trainData.biasSellWin - self.testData.biasSellWin)
        return math.sqrt(v1 * v1 * 0.7 + v2 * v2 * 0.3)

    def getStabilityBuy(self)->float:
        v1 = abs(self.trainData.scoreBuy - self.testData.scoreBuy) * 10
        v2 = abs(self.trainData.biasBuyLoss - self.testData.biasBuyLoss)
        return math.sqrt(v1 * v1 * 0.7 + v2 * v2 * 0.3)

    def getBiasSell(self,isWin:bool) -> float:
        if isWin:
            return utils.keep_3_float((self.trainData.biasSellWin + self.testData.biasSellWin) / 2)
        return utils.keep_3_float((self.trainData.biasSellLoss + self.testData.biasSellLoss) / 2)

    def getBiasBuy(self,isWin:bool) -> float:
        if isWin:
            return utils.keep_3_float((self.trainData.biasBuyWin + self.testData.biasBuyWin) / 2)
        return utils.keep_3_float((self.trainData.biasBuyLoss + self.testData.biasBuyLoss) / 2)

    def __post_init__(self):
        pass