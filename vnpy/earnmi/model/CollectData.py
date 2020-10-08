from dataclasses import dataclass

from earnmi.model.Dimension import Dimension
from vnpy.trader.object import BarData


@dataclass
class CollectData(object):

    """
    维度值
    """
    dimen:Dimension

    """
    生成维度值bars
    """
    occurBars:['BarData'] = None

    """
      预测情况的bar值。
    """
    predictBars:['BarData'] = None

    def __post_init__(self):
        self.occurBars = []
        self.predictBars = []
        pass