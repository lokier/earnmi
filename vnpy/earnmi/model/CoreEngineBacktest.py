
"""

核心引擎
"""
from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Union, Tuple, Sequence

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngine import CoreEngine, CoreCollector, BarDataSource,PredictModel
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.CoreStrategy import CoreStrategy
from earnmi.model.Dimension import Dimension, TYPE_2KAGO1
from earnmi.model.PredictData import PredictData
from earnmi.model.QuantData import QuantData

from vnpy.trader.object import BarData
import numpy as np
import pandas as pd

"""
收集Collector数据。
"""




class CoreEngineBackTest():

    def __init__(self,engine:CoreEngine):
        self.coreEngine:CoreEngine = engine

    def backtest(self, soruce: BarDataSource,collector:CoreCollector,limit=9999999):
        collector.onCreate()
        bars, code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        while not bars is None:
            finished, stop = CoreCollector.collectBars(bars, code, collector)
            print(f"[backtest]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
            totalCount += len(finished)
            bars, code = soruce.onNextBars()
            for data in finished:
                ##收录
                listData: [] = dataSet.get(data.dimen)
                if listData is None:
                    listData = []
                    dataSet[data.dimen] = listData
                listData.append(data)
        collector.onDestroy()

        dimes = dataSet.keys()
        totalDeal = 0
        totalOccurPredict = 0

        @dataclass
        class DimenData(object):
            count = 0
            countOk = 0
            earn_pct = 0.0
            loss_pct = 0.0
            eran_count = 0

            def __str__(self) -> str:
                earn_pct = 0.0
                lost_pct = 0.0
                if self.eran_count > 0:
                    earn_pct = self.earn_pct / self.eran_count
                if self.count - self.eran_count > 0:
                    lost_pct = self.loss_pct / (self.count - self.eran_count)
                return f"count:{self.count},ok:{self.countOk},earn:{self.eran_count},earn_pct:%.2f%%,loss_pct:%.2f%%" % (earn_pct * 100, lost_pct * 100)

        dimeDataList:['DimeData'] = []
        run_cnt = 0
        limit_size = min(limit,len(dataSet))
        for dimen, listData in dataSet.items():
            if run_cnt >= limit_size:
                continue
            model = self.coreEngine.loadPredictModel(dimen)
            if model is None:
                print(f"不支持的维度:{dimen}")
            run_cnt +=1
            print(f"开始回测维度:{dimen},进度:[{run_cnt}/{limit_size}]")
            predictList: Sequence['PredictData'] = model.predict(listData)
            dimenData = DimenData()
            for predict in predictList:
                deal,success,pct = self.computePredict(predict)
                totalOccurPredict += 0
                if deal:
                    totalDeal += 0
                    dimenData.count +=1
                    if success:
                        dimenData.countOk +=1
                    if pct > 0.0:
                        dimenData.earn_pct += pct
                        dimenData.eran_count +=1
                    else:
                        dimenData.loss_pct += pct
            dimeDataList.append(dimenData)

        total = DimenData()
        for d in dimeDataList:
            total.loss_pct += d.loss_pct
            total.count += d.count
            total.eran_count += d.eran_count
            total.countOk += d.countOk
            total.earn_pct += d.earn_pct
            print(f"{d}")

        deal_rate = 0.0
        if totalOccurPredict > 0:
            deal_rate =  totalDeal / totalOccurPredict

        print(f"总共产生{totalOccurPredict}个预测,交易{totalDeal}个，交易率:%.2f%%" % (100 *deal_rate))
        print(f"total:{total}")

    def __getFloatRangeInfo(self,ranges:['FloatRange'],encoder:FloatEncoder):
        info = "["
        for i in range(0,len(ranges)):
            r:FloatRange = ranges[i]
            min,max = encoder.parseEncode(r.encode)
            info+=f"({min}:{max})=%.2f%%," % (100 * r.probal)
        return info +"]"

    def computePredict(self,predict:PredictData):
        deal = False
        success = False
        pct = 0.0

        collectData = predict.collectData
        quantoEncoder = CoreEngine.quantFloatEncoder
        historyQunta = predict.historyData
        sampleQunta = predict.sampleData
        print(f"\nsample: {sampleQunta.getInfo(quantoEncoder)}, history: {historyQunta.getInfo(quantoEncoder)}")
        print(f"probal_sell_1: {self.__getFloatRangeInfo(predict.sellRange1,PredictModel.PctEncoder1)}")
        print(f"probal_sell_2: {self.__getFloatRangeInfo(predict.sellRange2,PredictModel.PctEncoder2)}")
        print(f"probal_buy_1: {self.__getFloatRangeInfo(predict.buyRange1,PredictModel.PctEncoder1)}")
        print(f"probal_buy_2: {self.__getFloatRangeInfo(predict.buyRange2,PredictModel.PctEncoder2)}")

        occurBar:BarData = collectData.occurBars[-1]



        return deal,success,pct

    def collect(self, barList: ['BarData'],symbol:str,collector:CoreCollector) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector.onStart(symbol)
        traceItems = []
        finishedData = []
        stopData = []
        for bar in barList:
            toDeleteList = []
            newObject = collector.collect(bar)
            for collectData in traceItems:
                isFinished = collector.onTrace(collectData, bar)
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
        collector.onEnd(symbol)
        return finishedData,stopData


if __name__ == "__main__":

    class Collector2KAgo1(CoreCollector):

        def __init__(self):
            self.lasted3Bar = np.array([None,None,None])
            self.lasted3BarKdj = np.array([None,None,None])

        def onStart(self, code: str) -> bool:
            from earnmi.chart.Indicator import Indicator
            self.indicator = Indicator(40)
            self.code = code
            return True

        def collect(self, bar: BarData) -> CollectData:
            self.indicator.update_bar(bar)
            self.lasted3Bar[:-1] = self.lasted3Bar[1:]
            self.lasted3BarKdj[:-1] = self.lasted3BarKdj[1:]
            k, d, j = self.indicator.kdj(fast_period=9, slow_period=3)
            self.lasted3Bar[-1] = bar
            self.lasted3BarKdj[-1] = [k, d, j]
            if self.indicator.count >= 15:
                from earnmi.chart.KPattern import KPattern
                kPatternValue = KPattern.encode2KAgo1(self.indicator)
                if not kPatternValue is None :
                    dimen = Dimension(type=TYPE_2KAGO1,value=kPatternValue)
                    collectData = CollectData(dimen=dimen)
                    collectData.occurBars.append(self.lasted3Bar[-2])
                    collectData.occurBars.append(self.lasted3Bar[-1])

                    collectData.occurKdj.append(self.lasted3BarKdj[-2])
                    collectData.occurKdj.append(self.lasted3BarKdj[-1])

                    return collectData
            return None

        def onTrace(self, data: CollectData, newBar: BarData) -> bool:
            if len(data.occurBars) < 3:
                data.occurBars.append(self.lasted3Bar[-1])
                data.occurKdj.append(self.lasted3BarKdj[-1])
            else:
                data.predictBars.append(newBar)
            size = len(data.predictBars)
            return size >= 2


    trainDataSouce = SWDataSource( start = datetime(2014, 2, 1),end = datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1),datetime(2020, 9, 1))


    dirName = "files/backtest"
    colletor = Collector2KAgo1()
    #engine = CoreEngine.create(dirName,colletor,trainDataSouce)
    engine = CoreEngine.load(dirName,colletor)
    backtest = CoreEngineBackTest(engine)

    backtest.backtest(testDataSouce,colletor,limit=1)


    pass