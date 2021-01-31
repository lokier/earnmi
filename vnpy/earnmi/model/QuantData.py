from dataclasses import dataclass

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange2
from earnmi.model.Dimension import Dimension

# @dataclass
# class Range(object):
#     min:float
#     max:float
from earnmi.model.PredictAbilityData import ModelAbilityData


@dataclass
class QuantData(object):
    """
    维度值
    """
    # dimen: Dimension

    count:int

    """
    卖方中间值pct，该中间值把概率分布分成50%
    """
    sellCenterPct:float

    buyCenterPct:float

    """
    卖方力量分布，没有排好序
    """
    sellRange:['FloatRange2']

    """
    买方力量分布，没有排好序
    """
    buyRange:['FloatRange2']

    sellSplits:['float']

    buySplits:['float']

    """
    量化预测能力
    """
    abilityData: ModelAbilityData = None

    def __post_init__(self):
        pass

    """
    多空双方力量对比：
    0附近之间表示多空力量一直
    1左右表示,多方量比空方大一倍
    -1左右表示,空方量比多方大一倍
    """
    def getPowerRate(self):
        sellMin, sellMax = self.getSellFloatEncoder().parseEncode(self.sellRange[0].encode)
        buyMin, buyMax = self.getBuyFloatEncoder().parseEncode(self.buyRange[0].encode)

        if sellMin is None:
            sellMin = self.sellSplits[0] -1
        if sellMax is None:
            sellMax = self.sellSplits[-1]+1
        if buyMin is None:
            buyMin = self.buySplits[0] -1
        if buyMax is None:
            buyMax = self.buySplits[-1]+1

        buy_power_pct = (buyMax + buyMin) / 2    # 买方力量的主力值越高，说明看多情况更好（大于0是铁定赚钱）
        sell_power_pct = (sellMax + sellMin) / 2   # 越高说明赚钱效益更好

        delta =  abs(sell_power_pct) - abs(buy_power_pct)

        if abs(delta) < 0.05:
            #多空力量差不多
            return 0
        if delta > 0:
            #适合做多
            return  (sell_power_pct + buy_power_pct) / sell_power_pct
        else:
            return - (sell_power_pct + buy_power_pct) / buy_power_pct

    """
    多空双方的力量概率
    """
    def getPowerProbal(self, isSell:bool)->float:

        if isSell:
            encoder = self.getSellFloatEncoder()
            sellMin, sellMax = encoder.parseEncode(self.sellRange[0].encode)
            probal = 0.0
            for fRange in self.sellRange:
                _min, _max = encoder.parseEncode(fRange.encode)
                if (_min >= sellMin):
                    probal += fRange.probal
            return probal
        else:
            encoder = self.getBuyFloatEncoder()
            sellMin, sellMax = encoder.parseEncode(self.buyRange[0].encode)
            probal = 0.0
            for fRange in self.sellRange:
                _min, _max = encoder.parseEncode(fRange.encode)
                if (_max <= sellMax):
                    probal += fRange.probal
            return probal


    def parseSellFactor(self):
        encoder = self.getSellFloatEncoder()
        sellMin, sellMax = encoder.parseEncode(self.sellRange[0].encode)

        probal = 0.0
        for fRange in self.sellRange:
            _min, _max = encoder.parseEncode(fRange.encode)
            if (_min >= sellMin):
                probal += fRange.probal

        buyMin, buyMax = self.getBuyFloatEncoder().parseEncode(self.buyRange[0].encode)
        buy_power_pct = (buyMax + buyMin) / 2  # 买方力量的主力值越高，说明看多情况更好（大于0是铁定赚钱）
        sell_power_pct = (sellMax + sellMin) / 2  # 越高说明赚钱效益更好
        dist = sell_power_pct - buy_power_pct  # 卖方力量与买方力量距离越靠近，说明力量越统一

        return sell_power_pct,buy_power_pct,dist,probal

    def check(self):
        for i in range(1, len(self.sellRange)):
            assert self.sellRange[i].probal <=self.sellRange[i - 1].probal
        for i in range(1, len(self.buyRange)):
            assert self.buyRange[i].probal <= self.buyRange[i - 1].probal


    def getSellFloatEncoder(self) ->FloatEncoder:
        return FloatEncoder(self.sellSplits)

    def getBuyFloatEncoder(self) ->FloatEncoder:
        return FloatEncoder(self.buySplits)

if __name__ == "__main__":
    import pickle
    from earnmi.model.CoreEngineImpl import CoreEngineImpl
    from earnmi.data.SWImpl import SWImpl


    def saveData(data:[]):

        fileName  = "files/testSaveQuantData.bin"
        with open(fileName, 'wb') as fp:
            pickle.dump(data, fp,-1)

    def loadData():
        bars = None
        fileName  = "files/testSaveQuantData.bin"
        with open(fileName, 'rb') as fp:
                bars = pickle.load(fp)
        return bars


    rangeCount1 = {}
    rangeCount1[1] = 34
    rangeCount1[2] =56
    rangeCount2 = {}
    rangeCount2[1] = 45
    rangeCount2[2] = 75
    rangeCount2[3] = 75


    quant1 = QuantData(dimen=Dimension(type=1,value=100),rangeCount= rangeCount1)
    quant2 = QuantData(dimen=Dimension(type=3,value=435),rangeCount= rangeCount2)

    data = [quant1,quant2]
    saveData(data)
    data2 = loadData()

    assert quant1.sellRangeCount != quant2.sellRangeCount

    assert  data == data2
    assert  len(data) == len(data) and len(data2) == 2
    assert  len(data2[0].rangeCount) == 2
    assert  len(data2[1].rangeCount) == 3
    assert  data2[0].rangeCount == data[0].sellRangeCount
