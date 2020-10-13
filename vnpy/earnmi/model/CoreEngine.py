
"""

核心引擎
"""
from abc import abstractmethod, ABC
from typing import Union, Tuple, Sequence

from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreStrategy import CoreStrategy
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictData import PredictData
from earnmi.model.QuantData import QuantData

from vnpy.trader.object import BarData



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

    """
    自我测试，返回sell_core,buy_score
    """
    @abstractmethod
    def selfTest(self) ->Tuple[float,float]:
        pass


class CoreEngine():

    """
    创建CoreEngine对象。
    """
    def create(dirName:str, strategy:CoreStrategy, dataSource:BarDataSource):
        from earnmi.model.CoreEngineImpl import CoreEngineImpl
        engine = CoreEngineImpl(dirName)
        engine.build(dataSource, strategy)
        return engine

    """
    加载已经存在的CoreEngine对象
    """
    def load(dirName: str, strategy: CoreStrategy):
        from earnmi.model.CoreEngineImpl import CoreEngineImpl
        engine = CoreEngineImpl(dirName)
        engine.load(strategy)
        return engine

    @abstractmethod
    def loadPredictModel(self, dimen:Dimension) ->PredictModel:
        pass

    @abstractmethod
    def getCoreStrategy(self) ->CoreStrategy:
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

    """
     评估盈利能力，并打印出来。
    """
    @abstractmethod
    def printTopDimension(self,pow_rate_limit = 1.0):
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