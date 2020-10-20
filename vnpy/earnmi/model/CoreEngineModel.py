

"""
核心策略类。
作用：
1、根据维度Dimeniso负责收集模型基础数据：CollectData
2、生成特征数据，建立预测模型。

"""
from abc import abstractmethod
from typing import Tuple, Sequence

from earnmi.model.CollectData import CollectData
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder
from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.object import BarData


class CoreEngineModel:

    """
    开始新的股票遍历,如果需要忽略该code，返回false。
    """
    def onCollectStart(self, code: str) -> bool:
        return True

    """
    最终bar，如果需要开始收集，返回一个CollectData对象。
    """
    @abstractmethod
    def onCollectTrace(self, bar: BarData) -> CollectData:
        pass
    """
    收集对象。如果收集完成返回True
    """
    @abstractmethod
    def onCollect(self, data: CollectData, newBar: BarData):
        pass

    def onCollectEnd(self, code: str):
        pass



    """
      预处理样本数据，比如，拆减等。
    """
    def generateSampleData(self, engine,collectList: Sequence['CollectData']) -> Sequence['CollectData']:
        return collectList

    """
    生成X特征值。
    返回值为：[x1,x2,x3....]
    """
    @abstractmethod
    def generateXFeature(self, cData:CollectData)->[]:
        pass

    """
    返回Y标签价格值值。[sellPrice,buyPrice]
    通过getYBasePrice()，可以计算得出买方力量和卖方里的涨跌幅度标签值。
    """
    # def getYLabelPrice(self, cData:CollectData)->[float, float]:
    def getYLabelPct(self, cData:CollectData)->[float, float]:
        pass

    @abstractmethod
    def getYBasePrice(self, cData:CollectData)->float:
        pass

    def collectBars(self,barList: ['BarData'],symbol:str,dimensValue:[] = None) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector = self
        collector.onCollectStart(symbol)
        traceItems = []
        finishedData = []
        validData = []
        dimenValueMap = None
        if not dimensValue is None and len(dimensValue) > 0:
            dimenValueMap = {}
            for _v in dimensValue:
                dimenValueMap[_v] = True

        for bar in barList:
            toDeleteList = []
            newObject = collector.onCollectTrace(bar)
            for collectData in traceItems:
                collector.onCollect(collectData, bar)
                if collectData.isFinished():
                    toDeleteList.append(collectData)
                    finishedData.append(collectData)
                    _s,_b = self.getYLabelPct(collectData)
                    assert not _s is None
                    assert not _b is None
                elif not collectData.isValid():
                    toDeleteList.append(collectData)
            for collectData in toDeleteList:
                traceItems.remove(collectData)

            if newObject is None:
                continue
            if not dimenValueMap is None and dimenValueMap.get(newObject.dimen.value) != True:
                continue
            traceItems.append(newObject)

        ###将要结束，剩下的作为validData
        for traceObject in traceItems:
            if traceObject.isValid():
                xFeature = self.generateXFeature(traceObject)
                assert not xFeature is None
                validData.append(traceObject)
        collector.onCollectEnd(symbol)
        return finishedData,validData