from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from earnmi.model.Dimension import Dimension
from vnpy.trader.object import BarData

class DataStatus(Enum):
    UNKONW = "vali"  # 正在追踪交易
    FINISHED = "finished"  # 收集完成,可作为预测和训练
    VALID = "predict_ok"

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

    occurKdj:[] = None

    """
      预测情况的bar值。
    """
    predictBars:['BarData'] = None

    """
    额外数据1
    """
    occurExtra:{} = None

    """
    额外数据2
    """
    predictExtra:{} = None

    """
       是否有效
       """

    def isValid(self) -> bool:
        return self.valid

    def setValid(self, isValid: bool):
        if self.isFinished():
            raise RuntimeError("can't set valid if is Finished")
        self.valid = isValid

    """
    是否完成,
    """
    def isFinished(self) -> bool:
        return self.finished

    def setFinished(self):
        self.finished = True

    def __post_init__(self):
        self.occurBars = []
        self.predictBars = []
        self.occurKdj = []
        self.occurExtra={}
        self.predictExtra={}
        self.valid = False
        self.finished = False

        pass



if __name__ == "__main__":
    import pickle
    from earnmi.model.CoreEngineImpl import CoreEngineImpl
    from earnmi.data.SWImpl import SWImpl


    def saveCollectData(bars:[]):

        fileName  = "files/testSaveCollectData.bin"
        with open(fileName, 'wb') as fp:
            pickle.dump(bars, fp,-1)

    def loadCollectData():
        bars = None
        fileName  = "files/testSaveCollectData.bin"
        with open(fileName, 'rb') as fp:
                bars = pickle.load(fp)
        return bars


    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)

    sw = SWImpl()

    code = sw.getSW2List()[3];
    bars = sw.getSW2Daily(code,start,end)
    #saveCollectData(bars)
    bars2 = loadCollectData()

    assert  bars == bars2
    assert  len(bars) == len(bars2) and len(bars2)!= 0
