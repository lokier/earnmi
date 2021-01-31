import math
from dataclasses import dataclass
from typing import Sequence

from earnmi.chart.FloatEncoder import FloatRange2
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


    def getBiasSell(self,isWin:bool) -> float:
        if isWin:
            return utils.keep_3_float((self.biasSellWin) / 2)
        return utils.keep_3_float((self.biasSellLoss) / 2)

    def getBiasBuy(self,isWin:bool) -> float:
        if isWin:
            return utils.keep_3_float(( self.biasBuyWin) / 2)
        return utils.keep_3_float(( self.biasBuyLoss) / 2)


    def toStr(self)->str:
        return f"count = {self.count}"\
                      f",s_得分={self.scoreSell}"\
                      f",b_得分={self.scoreBuy}"\
                      f",sell：正方差|负方差={self.getBiasSell(True)}|{self.getBiasSell(True)}"\
                      f",buy：正方差|负方差={self.getBiasBuy(True)}|{self.getBiasBuy(True)}"

    pass

@dataclass
class PredictAbilityData(object):

    trainData:ModelAbilityData = None
    testData:ModelAbilityData = None

    """
    预测值的pct值范围分布。
    """
    sellPctRnageList: Sequence["FloatRange2"] = None
    buyPctRnageList: Sequence["FloatRange2"] = None

    """
    返回卖方的预测能力值，对做多来说，越大越好。
    """
    def getSellAbility(self,encoder):
        ability = 0
        for i in range(0, len(self.sellPctRnageList)):
            r: FloatRange2 = self.sellPctRnageList[i]
            _min, _max = encoder.parseEncode(r.encode)
            if _min is None:
                _min = _max
            if _max is None:
                _max = _min
            ability += (_min + _max) / 2 * r.probal
        return ability

    """
       返回买方的预测能力值，对做多来说，越大越好。
    """
    def getBuyAbility(self,encoder):
        ability = 0
        for i in range(0, len(self.buyPctRnageList)):
            r: FloatRange2 = self.buyPctRnageList[i]
            _min, _max = encoder.parseEncode(r.encode)
            if _min is None:
                _min = _max
            if _max is None:
                _max = _min
            ability += (_min + _max) / 2 * r.probal
        return ability

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

    def toStr(self)->str:
        return f"count = {self.getCount()}"\
                      f",s_得分={self.getScoreSell()}"\
                      f",b_得分={self.getScoreBuy()}"\
                      f",s_稳定性={self.getStabilitySell()}"\
                      f",b_稳定性={self.getStabilityBuy()}"\
                      f",sell：正方差|负方差={self.getBiasSell(True)}|{self.getBiasSell(True)}"\
                      f",buy：正方差|负方差={self.getBiasBuy(True)}|{self.getBiasBuy(True)}"


    def __post_init__(self):
        pass