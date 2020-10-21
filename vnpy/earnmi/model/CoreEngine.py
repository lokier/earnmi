
"""

核心引擎
"""
from abc import abstractmethod, ABC
from typing import Union, Tuple, Sequence

from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.model.BarDataSource import BarDataSource
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngineModel import CoreEngineModel
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictAbilityData import PredictAbilityData
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder
from earnmi.model.QuantData import QuantData

from vnpy.trader.object import BarData





class PredictModel:

    PctEncoder1 = FloatEncoder([-7, -5, -3, -2, -1, 0, 1, 2,3, 5, 7],minValue= -10,maxValue=10)
    PctEncoder2 = FloatEncoder([-7.5, -5.5, -3.5, -2.5, -1.5, -0.5, 0.5,1.5,2.5, 3.5, 5.5, 7.5],minValue= -10,maxValue=10)


    @abstractmethod
    def predict(self, data: Union[CollectData, Sequence['CollectData']]) -> Union[PredictData, Sequence['PredictData']]:
        # 1、加载
        pass

    """
    返回预测结果是否匹配: isSellOk，isBuyOk
    """
    @abstractmethod
    def predictResult(self,data:PredictData) -> Union[bool, bool]:
        pass

    @abstractmethod
    def buildQuantData(self):
        pass

    @abstractmethod
    def buildPredictModel(self,split_rate=0.7,useSVM=True):
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
    def create(dirName:str, model:CoreEngineModel, dataSource:BarDataSource,split_rate = 0.7,limit_dimen_size = -1, build_quant_data_only=True,min_size = 300):
        from earnmi.model.CoreEngineImpl import CoreEngineImpl
        engine = CoreEngineImpl(dirName)
        engine.build(dataSource, model,split_rate,limit_dimen_size,onlyDimens = None,min_size = min_size,build_quant_data_only = build_quant_data_only)
        return engine

    """
    加载已经存在的CoreEngine对象
    """
    def load(dirName: str, model: CoreEngineModel):
        from earnmi.model.CoreEngineImpl import CoreEngineImpl
        engine = CoreEngineImpl(dirName)
        engine.load(model)
        return engine
    """
    创建预测模型。
    testDataSource数据源不能跟引擎的初始数据一样。
    """

    @abstractmethod
    def loadPredictModel(self, dimen:Dimension) ->PredictModel:
        pass

    @abstractmethod
    def getEngineModel(self) ->CoreEngineModel:
        pass

    @abstractmethod
    def isSupport(self,dimen:Dimension) ->bool:
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

    @abstractmethod
    def queryPredictAbilityData(self, dimen: Dimension) -> PredictAbilityData:
        pass

    """
    预测数据。
    """
    @abstractmethod
    def predict(self,data:Tuple[CollectData, Sequence['CollectData']])->Tuple[PredictData, Sequence['PredictData']]:
        pass


if __name__ == "__main__":
    pass