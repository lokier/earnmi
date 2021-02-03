

"""
核心策略类。
作用：
1、根据维度Dimeniso负责收集模型基础数据：CollectData
2、生成特征数据，建立预测模型。

"""
from abc import abstractmethod
from typing import Tuple, Sequence
from earnmi.model.CollectData2 import CollectData2
from vnpy.trader.object import BarData


class CollectModel:

    """
    开始新的股票遍历,如果需要忽略该code，返回false。
    """
    def onCollectStart(self, code: str) -> bool:
        return True

    """
    最终bar，如果需要开始收集，返回一个CollectData对象。
    """
    @abstractmethod
    def onCollectTrace(self, bar: BarData) -> CollectData2:
        pass
    """
    收集对象。如果收集完成,得把CollectData.isFinished();
    """
    @abstractmethod
    def onCollect(self, data: CollectData2, newBar: BarData):
        pass

    def onCollectEnd(self, code: str):
        pass

    """
    收集完成,isFinished表示是否正常结束
    """
    def onCollectFinished(self, data:CollectData2, isFinished:bool):
        pass

    @staticmethod
    def collect(model,barList: ['BarData'],symbol:str,dimensValue:[] = None) -> Tuple[Sequence['CollectData2'], Sequence[
        'CollectData2']]:
        collector = model
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
                    if collectData.isValid():
                        finishedData.append(collectData)
                        model.onCollectFinished(collectData,True)
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
                model.onCollectFinished(traceObject, False)
                validData.append(traceObject)
        collector.onCollectEnd(symbol)
        return finishedData,validData