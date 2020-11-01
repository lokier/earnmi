

from abc import abstractmethod
from typing import Tuple, Sequence

from earnmi.data.SWImpl import SWImpl
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder
from vnpy.trader.object import BarData


class CoreEngineStrategy:

    """
    策略是否允许该维度下面的数据。
    """
    def isSupport(self, engine: CoreEngine, dimen:Dimension)->bool:
        return True
    """
    处理操作单
    0: 不处理
    1：做多
    2：做空
    3: 预测成功交割单
    4：预测失败交割单
    5：废弃改单
    """
    @abstractmethod
    def operatePredictOrder(self,engine:CoreEngine, order: PredictOrder,bar:BarData,isTodayLastBar:bool,debugParams:{}=None) ->int:
        pass



