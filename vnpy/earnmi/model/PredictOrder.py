from dataclasses import dataclass
from enum import Enum

from earnmi.model.CollectData import CollectData
from earnmi.model.Dimension import Dimension
from earnmi.model.QuantData import QuantData

class PredictOrderStatus(Enum):
    """
    start of PredictOrder.
    """
    TRACE = "trace"  #正在追踪交易
    HOLD = "hold"   #已经持有筹码
    STOP = "stop"   #终止交易
    CROSS = "cross"   #交割完成

@dataclass
class PredictOrder(object):
    """
        维度值
    """
    dimen: Dimension

    code:str

    name:str

    status = PredictOrderStatus.TRACE

    """
    多空力量比例
    """
    pow_rate:float = 0.0

    #最佳卖出价
    suggestSellPrice:float = 0.0

    #最佳买入价
    suggestBuyPrice:float = 0.0

    max_hold_day = 0

    """
    """
    buyPrice:float = None


    sellPrice:float =None

    holdDay = 0


    def __post_init__(self):
        pass