

"""
核心策略类。
作用：
1、根据维度Dimeniso负责收集模型基础数据：CollectData
2、生成特征数据，建立预测模型。

"""
from abc import abstractmethod
from typing import Tuple, Sequence

from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.model.CollectData2 import CollectData2
from earnmi.model.CollectModel import CollectModel
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder
from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.object import BarData
import numpy as np

class CoreEngineModel():


    @abstractmethod
    def getEngineName(self):
        return "unkonw"

    def getCollectModel(self)->CollectModel:
        pass

    def getPctEncoder1(self)->FloatEncoder:
        return FloatEncoder([-7, -5, -3, -2, -1, 0, 1, 2, 3, 5, 7], minValue=-10, maxValue=10)

    def getPctEncoder2(self)->FloatEncoder:
        return FloatEncoder([-7.5, -5.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 5.5, 7.5], minValue=-10,
                               maxValue=10)

    """
      预处理样本数据，比如，拆减等。
    """
    def generateSampleData(self, engine, collectList: Sequence['CollectData2']) -> Sequence['CollectData2']:
        return collectList

    """
    生成X特征值。
    返回值为：[x1,x2,x3....]
    """
    @abstractmethod
    def generateXFeature(self, cData:CollectData2)->[]:
        pass

    """
    返回Y标签价格值值。[sellPrice,buyPrice]
    通过getYBasePrice()，可以计算得出买方力量和卖方里的涨跌幅度标签值。
    """
    # def getYLabelPrice(self, cData:CollectData)->[float, float]:
    def getYLabelPct(self, cData:CollectData2)->[float, float]:
        pass

    @abstractmethod
    def getYBasePrice(self, cData:CollectData2)->float:
        pass

    """
    优化特征。（主要去重）
    """
    def optimize(self, x: [], y_sell_1: [], y_buy_1: [], y_sell_2: [], y_buy_2: []):
        return np.array(x),np.array(y_sell_1),np.array(y_buy_1),np.array(y_sell_2),np.array(y_buy_2)

    def isSupportBuildPredictModel(self, engine, dimen: Dimension) -> bool:
        return True

    """
    收集完成,isFinished表示是否正常结束
    """
    # def onCollectFinished(self,data:CollectData,isFinished:bool):
    #     if isFinished is True:
    #         _s,_b = self.getYLabelPct(data)
    #         assert not _s is None
    #         assert not _b is None
    #     else:
    #         xFeature = self.generateXFeature(data)
    #         assert not xFeature is None

    def collectBars(self,barList: ['BarData'],symbol:str,dimensValue:[] = None) -> Tuple[Sequence['CollectData2'], Sequence[
        'CollectData2']]:
        return CollectModel.collect(self.getCollectModel(),barList,symbol,dimensValue)