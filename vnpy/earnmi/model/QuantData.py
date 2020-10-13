from dataclasses import dataclass

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange
from earnmi.model.Dimension import Dimension

# @dataclass
# class Range(object):
#     min:float
#     max:float

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
    卖方力量分布
    """
    sellRange:['FloatRange']

    """
    买方力量分布
    """
    buyRange:['FloatRange']

    sellSplits:['float']

    buySplits:['float']

    def __post_init__(self):
        pass

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
    """
    """
    def factor(self, isSell, eran=0.4, probal=0.3) -> float:
        #卖方力量与买方力量越靠近，说明力量越统一
        #买方的最低值越高，说明看多情况更好
        #卖方的概率值越大，赚钱效率更高


        pass


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
