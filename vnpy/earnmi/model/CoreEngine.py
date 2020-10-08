
"""

核心引擎
"""
from abc import abstractmethod
from typing import Union, Tuple, Sequence

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

class BarDataSource:

    """
    返回下一批BarData数据。 返回[bars,code]
    """
    @abstractmethod
    def onNextBars(self) -> Tuple[Sequence['BarData'],str]:
        pass

class CoreEngine(object):

    """
    创建CoreEngine对象。
    """
    def create(dirName:str,collector:CoreCollector,dataSource:BarDataSource):
        pass

    """
    加载已经存在的CoreEngine对象
    """
    def load(dirName:str,collector:CoreCollector):
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
    def loadAllDimesion(self,type:int) -> Sequence['Dimension']:
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