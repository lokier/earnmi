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
    sellRange1:[]

    sellRange2: []

    """
     买方概率分布
    """
    buyRange1:[]

    buyRange2:[]


    def __post_init__(self):
        pass