

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
from vnpy.trader.object import BarData


class CoreStrategy:

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
    def onCollect(self, data: CollectData, newBar: BarData) ->bool:
        pass

    def onCollectEnd(self, code: str):
        pass


    """
    根据预测对象，生成预测操作单
    """
    @abstractmethod
    def generatePredictOrder(self,predict:PredictData)->PredictOrder:
        pass

    """
    是否可以预测
    """
    @abstractmethod
    def canPredict(self,collectData:CollectData)->bool:
        pass

    """
      返回收集对象的买与卖方的标签值。 是一个乘以100的百分比值。
    """
    @abstractmethod
    def getSellBuyPctLabel(self, collectData:CollectData)->Tuple[int,int]:
        pass

    """
    返回预测值的最终sell，buy预测结果。
    """
    def getSellBuyPctPredict(self,predict:PredictData) ->Tuple[float,float]:
        from earnmi.model.CoreEngine import PredictModel
        min1, max1 = PredictModel.PctEncoder1.parseEncode(predict.sellRange1[0].encode)
        min2, max2 = PredictModel.PctEncoder2.parseEncode(predict.sellRange2[0].encode)
        total_probal = predict.sellRange2[0].probal + predict.sellRange1[0].probal
        predict_sell_pct = (min1 + max1) / 2 * predict.sellRange1[0].probal / total_probal + (min2 + max2) / 2 * \
                           predict.sellRange2[0].probal / total_probal

        min1, max1 = PredictModel.PctEncoder1.parseEncode(predict.buyRange1[0].encode)
        min2, max2 = PredictModel.PctEncoder2.parseEncode(predict.buyRange2[0].encode)
        total_probal = predict.sellRange2[0].probal + predict.sellRange1[0].probal
        predict_buy_pct = (min1 + max1) / 2 * predict.buyRange1[0].probal / total_probal + (min2 + max2) / 2 * \
                          predict.buyRange2[0].probal / total_probal

        return predict_sell_pct, predict_buy_pct


    """
      预处理样本数据，比如，拆减等。
    """
    def generateSampleData(self, engine,collectList: Sequence['CollectData']) -> Sequence['CollectData']:
        return collectList

    """
    生成特征值。(有4个标签）
    返回值为：x, y_sell_1,y_buy_1,y_sell_2,y_buy_2
    """
    @abstractmethod
    def generateFeature(self, engine, dataList: Sequence['CollectData']):
        pass

    def collectBars(barList: ['BarData'],symbol:str,collector) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector.onCollectStart(symbol)
        traceItems = []
        finishedData = []
        stopData = []
        for bar in barList:
            toDeleteList = []
            newObject = collector.onCollectTrace(bar)
            for collectData in traceItems:
                isFinished = collector.onCollect(collectData, bar)
                if isFinished:
                    toDeleteList.append(collectData)
                    finishedData.append(collectData)
            for collectData in toDeleteList:
                traceItems.remove(collectData)
            if newObject is None:
                continue
            traceItems.append(newObject)

        ###将要结束，未追踪完的traceData
        for traceObject in traceItems:
            stopData.append(traceObject)
        collector.onCollectEnd(symbol)
        return finishedData,stopData