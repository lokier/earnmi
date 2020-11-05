

"""
核心策略类。
作用：
1、根据维度Dimeniso负责收集模型基础数据：CollectData
2、生成特征数据，建立预测模型。

"""
from abc import abstractmethod
from typing import Tuple, Sequence

from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.model.CollectData import CollectData
from earnmi.model.CollectModel import CollectModel
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder
from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.object import BarData


class CoreEngineModel(CollectModel):


    def getPctEncoder1(self)->FloatEncoder:
        return FloatEncoder([-7, -5, -3, -2, -1, 0, 1, 2, 3, 5, 7], minValue=-10, maxValue=10)

    def getPctEncoder2(self)->FloatEncoder:
        return FloatEncoder([-7.5, -5.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 5.5, 7.5], minValue=-10,
                               maxValue=10)

    """
      预处理样本数据，比如，拆减等。
    """
    def generateSampleData(self, engine,collectList: Sequence['CollectData']) -> Sequence['CollectData']:
        return collectList

    """
    生成X特征值。
    返回值为：[x1,x2,x3....]
    """
    @abstractmethod
    def generateXFeature(self, cData:CollectData)->[]:
        pass

    """
    返回Y标签价格值值。[sellPrice,buyPrice]
    通过getYBasePrice()，可以计算得出买方力量和卖方里的涨跌幅度标签值。
    """
    # def getYLabelPrice(self, cData:CollectData)->[float, float]:
    def getYLabelPct(self, cData:CollectData)->[float, float]:
        pass

    @abstractmethod
    def getYBasePrice(self, cData:CollectData)->float:
        pass

    def isSupportBuildPredictModel(self, engine, dimen: Dimension) -> bool:
        return True

    """
    收集完成,isFinished表示是否正常结束
    """
    def onCollectFinished(self,data:CollectData,isFinished:bool):
        if isFinished is True:
            _s,_b = self.getYLabelPct(data)
            assert not _s is None
            assert not _b is None
        else:
            xFeature = self.generateXFeature(data)
            assert not xFeature is None

    def collectBars(self,barList: ['BarData'],symbol:str,dimensValue:[] = None) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        return CollectModel.collect(self,barList,symbol,dimensValue)