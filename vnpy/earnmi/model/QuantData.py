from dataclasses import dataclass

from earnmi.model.Dimension import Dimension

# @dataclass
# class Range(object):
#     min:float
#     max:float

@dataclass
class QuantData(object):
    """
    维度值
    """
    dimen: Dimension

    count:int

    """
    卖方力量分布
    """
    sellRangeCount:{}

    """
    买方力量分布
    """
    buyRangeCount: {}

    def __post_init__(self):
        pass

if __name__ == "__main__":
    import pickle
    from earnmi.model.CoreEngineImpl import CoreEngineImpl
    from earnmi.data.SWImpl import SWImpl


    def saveData(data:[]):

        fileName  = "files/testSaveQuantData.bin"
        with open(fileName, 'wb') as fp:
            pickle.dump(data, fp,-1)

    def loadData():
        bars = None
        fileName  = "files/testSaveQuantData.bin"
        with open(fileName, 'rb') as fp:
                bars = pickle.load(fp)
        return bars


    rangeCount1 = {}
    rangeCount1[1] = 34
    rangeCount1[2] =56
    rangeCount2 = {}
    rangeCount2[1] = 45
    rangeCount2[2] = 75
    rangeCount2[3] = 75


    quant1 = QuantData(dimen=Dimension(type=1,value=100),rangeCount= rangeCount1)
    quant2 = QuantData(dimen=Dimension(type=3,value=435),rangeCount= rangeCount2)

    data = [quant1,quant2]
    saveData(data)
    data2 = loadData()

    assert quant1.sellRangeCount != quant2.sellRangeCount

    assert  data == data2
    assert  len(data) == len(data) and len(data2) == 2
    assert  len(data2[0].rangeCount) == 2
    assert  len(data2[1].rangeCount) == 3
    assert  data2[0].rangeCount == data[0].sellRangeCount
