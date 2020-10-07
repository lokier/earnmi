from dataclasses import dataclass

from earnmi.model.CollectData import CollectData
from earnmi.model.Dimension import Dimension

"""
 预测值数据
"""

@dataclass
class PredictData(object):
    """
        维度值
        """
    dimen: Dimension

    collectData:CollectData

    """
    卖方概率分布
    """
    sell_disbute:[]

    buy_disbute:[]

    def __post_init__(self):
        self.sell_disbute = []
        self.buy_disbute = []
        pass