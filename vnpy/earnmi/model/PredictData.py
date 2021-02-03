from dataclasses import dataclass

from earnmi.chart.FloatEncoder import FloatRange2
from earnmi.model.CollectData2 import CollectData2
from earnmi.model.Dimension import Dimension
from earnmi.model.QuantData import QuantData

"""
 预测值数据
"""
@dataclass
class PredictRangeInfo(object):
    """
    FloatEncoder里的编码值
    """
    encode:int
    """
    概率或者分布概率
    """
    probal:float

@dataclass
class PredictData(object):
    """
        维度值
        """
    dimen: Dimension

    """
    训练样本的量化数据。
    """
    quantData:QuantData

    """
    测试特征值得原始数据。
    """
    collectData:CollectData2

    """
    卖方概率分布
    """
    sellRange1:['FloatRange2'] = None

    sellRange2: ['FloatRange2']= None

    """
     买方概率分布
    """
    buyRange1:['FloatRange2'] = None

    buyRange2:['FloatRange2']= None


    def getPredictSellPct(self,engineModel)->float:
        from earnmi.model.CoreEngineModel import CoreEngineModel
        model:CoreEngineModel = engineModel;
        min1, max1 = model.getPctEncoder1().parseEncode(self.sellRange1[0].encode)
        min2, max2 = model.getPctEncoder2().parseEncode(self.sellRange2[0].encode)
        total_probal = self.sellRange2[0].probal + self.sellRange1[0].probal
        predict_sell_pct = (min1 + max1) / 2 * self.sellRange1[0].probal / total_probal + (min2 + max2) / 2 * \
                                self.sellRange2[0].probal / total_probal
        return predict_sell_pct

    def getPredictSellProbal(self) -> float:
        from earnmi.model.CoreEngineModel import CoreEngineModel
        total_probal = self.sellRange2[0].probal + self.sellRange1[0].probal
        return total_probal / 2

    def getPredictBuyPct(self,engineModel)->float:
        from earnmi.model.CoreEngineModel import CoreEngineModel
        model: CoreEngineModel = engineModel;
        min1, max1 = model.getPctEncoder1().parseEncode(self.buyRange1[0].encode)
        min2, max2 = model.getPctEncoder2().parseEncode(self.buyRange2[0].encode)
        total_probal = self.buyRange1[0].probal + self.buyRange2[0].probal
        predict_buy_pct = (min1 + max1) / 2 * self.buyRange1[0].probal / total_probal + (min2 + max2) / 2 * \
                              self.buyRange2[0].probal / total_probal
        return predict_buy_pct

    """
        多空双方力量对比：
        0附近之间表示多空力量一直
        1左右表示,多方量比空方大一倍
        -1左右表示,空方量比多方大一倍
        """
    def getPowerRate(self,engineModel):
        buy_power_pct = self.getPredictBuyPct(engineModel)
        sell_power_pct = self.getPredictSellPct(engineModel)

        delta = abs(sell_power_pct) - abs(buy_power_pct)

        if abs(delta) < 0.05:
            # 多空力量差不多
            return 0
        if delta > 0:
            # 适合做多
            return (sell_power_pct + buy_power_pct) / sell_power_pct
        else:
            return - (sell_power_pct + buy_power_pct) / buy_power_pct

    def check(self):
        for i in range(1, len(self.sellRange1)):
            assert self.sellRange1[i].probal <= self.sellRange1[i - 1].probal
        for i in range(1, len(self.buyRange1)):
            assert self.buyRange1[i].probal <= self.buyRange1[i - 1].probal

    def __post_init__(self):
        pass