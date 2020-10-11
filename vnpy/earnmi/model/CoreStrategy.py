

"""
核心策略类。
作用：
1、根据维度Dimeniso负责收集模型基础数据：CollectData
2、生成特征数据，建立预测模型。

"""
from abc import abstractmethod
from typing import Tuple, Sequence

from earnmi.model.CollectData import CollectData
from vnpy.trader.object import BarData


class CoreStrategy:

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
    生成特征值。(有4个标签）
    返回值为：x, y_sell_1,y_buy_1,y_sell_2,y_buy_2
    """
    @abstractmethod
    def generateFeature(self, engine, dataList: Sequence['CollectData']):
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