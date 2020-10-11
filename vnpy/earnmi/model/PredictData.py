from dataclasses import dataclass

from earnmi.model.CollectData import CollectData
from earnmi.model.Dimension import Dimension
from earnmi.model.QuantData import QuantData

"""
 预测值数据
"""
@dataclass
class PredictRangeInfo(object):
    """
    FloatEncoder里的编码值
    """
    encode:int
    """
    概率或者分布概率
    """
    probal:float

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
    sellRange1:['FloatRange'] = None

    sellRange2: ['FloatRange']= None

    """
     买方概率分布
    """
    buyRange1:['FloatRange'] = None

    buyRange2:['FloatRange']= None



    def __post_init__(self):
        pass