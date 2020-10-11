
"""

核心引擎
"""
from abc import abstractmethod, ABC
from typing import Union, Tuple, Sequence

from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.model.CollectData import CollectData
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictData import PredictData
from earnmi.model.QuantData import QuantData

from vnpy.trader.object import BarData


"""
收集Collector数据。
"""
class CoreCollector:


    def onCreate(self):
        pass

    """
    开始新的股票遍历,如果需要忽略该code，返回false。
    """

    def onStart(self, code: str) -> bool:
        return True

    """
    收集bar，如果需要开始追踪这个bar，返回TraceData对象。
    """

    @abstractmethod
    def collect(self, bar: BarData) -> CollectData:
        pass

    """
    追踪预测数据。 返回是否追踪完成。
    """
    @abstractmethod
    def onTrace(self, data: CollectData, newBar: BarData) ->bool:
        pass

    def onEnd(self, code: str):
        pass

    def onDestroy(self):
        pass

    def collectBars(barList: ['BarData'],symbol:str,collector) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector.onStart(symbol)
        traceItems = []
        finishedData = []
        stopData = []
        for bar in barList:
            toDeleteList = []
            newObject = collector.collect(bar)
            for collectData in traceItems:
                isFinished = collector.onTrace(collectData, bar)
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
        collector.onEnd(symbol)
        return finishedData,stopData


class BarDataSource:

    """
    返回下一批BarData数据。 返回[bars,code]
    """
    @abstractmethod
    def onNextBars(self) -> Tuple[Sequence['BarData'],str]:
        pass

class PredictModel:

    PctEncoder1 = FloatEncoder([-7, -5, -3, -2, -1, 0, 1, 2,3, 5, 7])
    PctEncoder2 = FloatEncoder([-7.5, -5.5, -3.5, -2.5, -1.5, -0.5, 0.5,1.5,2.5, 3.5, 5.5, 7.5])


    @abstractmethod
    def predict(self, data: Tuple[CollectData, Sequence['CollectData']]) -> Tuple[PredictData, Sequence['PredictData']]:
        # 1、加载
        pass


class CoreEngine():

    """
    创建CoreEngine对象。
    """
    def create(dirName:str,collector:CoreCollector,dataSource:BarDataSource):
        from earnmi.model.CoreEngineImpl import CoreEngineImpl
        engine = CoreEngineImpl(dirName)
        engine.build(dataSource, collector)
        return engine

    """
    加载已经存在的CoreEngine对象
    """
    def load(dirName: str, collector: CoreCollector):
        from earnmi.model.CoreEngineImpl import CoreEngineImpl
        engine = CoreEngineImpl(dirName)
        engine.load(collector)
        return engine

    @abstractmethod
    def loadPredictModel(self, dimen:Dimension) ->PredictModel:
        pass

    """
    收集ColletorData数据，返回已经完成的CollectData, 未完成的CollectData
    """
    @abstractmethod
    def collect(self,bars:['BarData']) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        pass

    """
    加载所有的维度
    """
    @abstractmethod
    def loadAllDimesion(self) -> Sequence['Dimension']:
        pass

    @abstractmethod
    def computeQuantData(self,data:Sequence['CollectData']) ->QuantData:
        pass

    @abstractmethod
    def loadCollectData(self, dimen: Dimension) -> Sequence['CollectData']:
        pass

    @abstractmethod
    def printLog(self,info:str,forcePrint = False):
        pass
    """
    加载某一维度的量化数据对象
    """
    @abstractmethod
    def queryQuantData(self,dimen:Dimension) ->QuantData:
        pass

    """
    预测数据。
    """
    @abstractmethod
    def predict(self,data:Tuple[CollectData, Sequence['CollectData']])->Tuple[PredictData, Sequence['PredictData']]:
        pass


if __name__ == "__main__":
    pass