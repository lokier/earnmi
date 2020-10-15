

"""
核心策略类。
作用：
1、根据维度Dimeniso负责收集模型基础数据：CollectData
2、生成特征数据，建立预测模型。

"""
from abc import abstractmethod
from typing import Tuple, Sequence

from earnmi.model.CollectData import CollectData
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder
from vnpy.trader.object import BarData


class CoreEngineModel:

    """
    开始新的股票遍历,如果需要忽略该code，返回false。
    """
    def onCollectStart(self, code: str) -> bool:
        return True

    """
    最终bar，如果需要开始收集，返回一个CollectData对象。
    """
    @abstractmethod
    def onCollectTrace(self, bar: BarData) -> CollectData:
        pass
    """
    收集对象。如果收集完成返回True
    """
    @abstractmethod
    def onCollect(self, data: CollectData, newBar: BarData) ->bool:
        pass

    def onCollectEnd(self, code: str):
        pass


    """
      预处理样本数据，比如，拆减等。
    """
    def generateSampleData(self, engine,collectList: Sequence['CollectData']) -> Sequence['CollectData']:
        return collectList

    """
    生成X特征值。(有4个标签）
    返回值为：[[x1,x2,x3....],[x1,x2,x3..]...]
    """
    @abstractmethod
    def generateXFeature(self, engine, cData:CollectData)->[]:
        pass

    """
    返回Y标签值。[basePrice,sellPrice,buyPrice]
    通过三个值，可以计算得出买方力量和卖方里的涨跌幅度标签值。
    """
    @abstractmethod
    def generateYLabel(self, engine, cData:CollectData)->[float,float,float]:
        pass

    """
    --------------------------------------------------------------------
        根据预测对象，生成预测操作单
        """
    def generatePredictOrder(self, engine, predict: PredictData) -> PredictOrder:
        pass

    @abstractmethod
    def updatePredictOrder(self, order: PredictOrder,bar:BarData,isTodayLastBar:bool):
        pass

    def collectBars(barList: ['BarData'],symbol:str,collector) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector.onCollectStart(symbol)
        traceItems = []
        finishedData = []
        stopData = []
        for bar in barList:
            toDeleteList = []
            newObject = collector.onCollectTrace(bar)
            for collectData in traceItems:
                isFinished = collector.onCollect(collectData, bar)
                if isFinished:
                    toDeleteList.append(collectData)
                    finishedData.append(collectData)
            for collectData in toDeleteList:
                traceItems.remove(collectData)
            if newObject is None:
                continue
            traceItems.append(newObject)

        ###将要结束，未追踪完的traceData
        for traceObject in traceItems:
            stopData.append(traceObject)
        collector.onCollectEnd(symbol)
        return finishedData,stopData