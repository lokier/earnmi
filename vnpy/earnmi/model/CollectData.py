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


if __name__ == "__main__":
    import pickle
    from earnmi.model.CoreEngineImpl import CoreEngineImpl


    def testSaveCollectData():
        pass


    pickle.dump(self.data_x, fp, -1)

    d1 = Dimension(type=1,value =34)
    d2 = Dimension(type=1,value =34)
    d3=d2
    assert  d1 == d2
    assert  d1 == d3