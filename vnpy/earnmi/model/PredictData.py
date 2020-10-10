from dataclasses import dataclass

from earnmi.model.CollectData import CollectData
from earnmi.model.Dimension import Dimension
from earnmi.model.QuantData import QuantData

"""
 预测值数据
"""

@dataclass
class PredictData(object):
    """
        维度值
        """
    dimen: Dimension

    """
    历史记录的量化数据
    """
    historyData:QuantData

    """
    训练样本的量化数据。
    """
    sampleData:QuantData

    """
    测试特征值得原始数据。
    """
    collectData:CollectData

    """
    卖方概率分布
    """
    sellRange1:[] = None

    sellRange2: [] = None

    """
     买方概率分布
    """
    buyRange1:[] = None

    buyRange2:[] = None


    def __post_init__(self):
        pass