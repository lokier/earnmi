from dataclasses import dataclass

from earnmi.model.CollectData import CollectData
from earnmi.model.Dimension import Dimension
from earnmi.model.QuantData import QuantData



@dataclass
class PredictOrder(object):
    """
        维度值
    """
    dimen: Dimension

    code:str

    name:str

    """
    多空力量比例
    """
    pow_rate:float

    #最佳卖出价
    suggestSellPrice:float

    #最佳买入价
    suggetsBuyPrice:float

    def __post_init__(self):
        pass