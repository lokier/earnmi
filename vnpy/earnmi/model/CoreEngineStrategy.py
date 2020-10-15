

from abc import abstractmethod
from typing import Tuple, Sequence
from earnmi.model.CollectData import CollectData
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder
from vnpy.trader.object import BarData


class CoreEngineStrategy:
    """
    --------------------------------------------------------------------
        根据预测对象，生成预测操作单
        """
    def generatePredictOrder(self, engine, predict: PredictData) -> PredictOrder:
        pass

    @abstractmethod
    def updatePredictOrder(self, order: PredictOrder,bar:BarData,isTodayLastBar:bool):
        pass

