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
    维度值bars
    """
    dimenBars:['BarData']

    """
      预测情况的bar值
    """
    predictBars:['BarData']

    def __post_init__(self):
        self.dimenBars = []
        self.predictBars = []
        pass