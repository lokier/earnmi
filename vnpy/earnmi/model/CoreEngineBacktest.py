
"""

核心引擎
"""
from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
from functools import cmp_to_key
from typing import Union, Tuple, Sequence

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngine import CoreEngine, BarDataSource,PredictModel
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.Dimension import Dimension, TYPE_2KAGO1
from earnmi.model.PredictData import PredictData
from earnmi.model.QuantData import QuantData
from earnmi.model.CoreStrategy import CoreStrategy
from vnpy.trader.object import BarData
import numpy as np
import pandas as pd

"""
收集Collector数据。
"""




class CoreEngineBackTest():

    def __init__(self,engine:CoreEngine):
        self.coreEngine:CoreEngine = engine

    def backtest(self, soruce: BarDataSource, strategy:CoreStrategy, limit=9999999):
        bars, code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        while not bars is None:
            finished, stop = CoreStrategy.collectBars(bars, code, strategy)
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

        dimes = dataSet.keys()
        totalDeal = 0
        totalOccurPredict = 0

        @dataclass
        class DimenData(object):
            dimen:Dimension
            count = 0
            countOk = 0
            earn_pct = 0.0
            loss_pct = 0.0
            eran_count = 0
            sell_core = 0.0
            buy_core =0.0

            def getOkRate(self) ->float:
                if self.count > 0:
                   return self.countOk / self.count
                return 0

            def __str__(self) -> str:
                earn_pct = 0.0
                lost_pct = 0.0
                if self.eran_count > 0:
                    earn_pct = self.earn_pct / self.eran_count
                if self.count - self.eran_count > 0:
                    lost_pct = self.loss_pct / (self.count - self.eran_count)
                ok_rate = self.getOkRate()
                return f"count:{self.count},ok:{self.countOk}(%.2f%%),earn:{self.eran_count}" \
                       f",earn_pct:%.2f%%,loss_pct:%.2f%%, " \
                       f"模型能力:[sell_core: %.2f,buy_core:%.2f]" % \
                       (ok_rate*100,earn_pct, lost_pct,100*self.sell_core,100*self.buy_core)

        dimeDataList:['DimeData'] = []
        run_cnt = 0
        limit_size = min(limit,len(dataSet))
        for dimen, listData in dataSet.items():
            if run_cnt >= limit_size:
                continue
            model = self.coreEngine.loadPredictModel(dimen)
            if model is None:
                print(f"不支持的维度:{dimen}")
                continue
            run_cnt +=1
            print(f"开始回测维度:{dimen},进度:[{run_cnt}/{limit_size}]")
            sell_core,buy_core = model.selfTest()
            predictList: Sequence['PredictData'] = model.predict(listData)
            dimenData = DimenData(dimen=dimen)
            dimenData.sell_core = sell_core
            dimenData.buy_core = buy_core
            for predict in predictList:
                deal,success,pct = self.computePredict(predict)
                totalOccurPredict += 1
                if deal:
                    totalDeal += 1
                    dimenData.count +=1
                    if success:
                        dimenData.countOk +=1
                    if pct > 0.0:
                        dimenData.earn_pct += pct
                        dimenData.eran_count +=1
                    else:
                        dimenData.loss_pct += pct
            dimeDataList.append(dimenData)

        print("\n\n")
        total = DimenData(dimen=None)

        def diemdata_cmp(v1,v2):
            return v1.getOkRate() - v2.getOkRate()

        dimeDataList = sorted(dimeDataList, key=cmp_to_key(diemdata_cmp), reverse=False)
        for d in dimeDataList:
            total.loss_pct += d.loss_pct
            total.count += d.count
            total.eran_count += d.eran_count
            total.countOk += d.countOk
            total.earn_pct += d.earn_pct
            print(f"[{d.dimen.value}]: {d}")

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
        earn_pct = 0.0

        collectData = predict.collectData
        quantoEncoder = CoreEngine.quantFloatEncoder
        historyQunta = predict.historyData
        sampleQunta = predict.sampleData
        occurBar:BarData = collectData.occurBars[-2]
        skipBar:BarData = collectData.occurBars[-1]



        sell_pct,buy_pct = engine.getCoreStrategy().getSellBuyPctLabel(collectData)

        predict_sell_pct, predict_buy_pct = engine.getCoreStrategy().getSellBuyPctPredict(predict)
        buy_price = skipBar.close_price
        buy_pct = (buy_price - occurBar.close_price) / occurBar.close_price  ##买入的价格

        if predict_buy_pct > 0.2 and predict_sell_pct > buy_pct:

            # print(f"\nsmaple->sell{self.__getFloatRangeInfo(sampleQunta.sellRange, CoreEngine.quantFloatEncoder)}")
            # print(f"smaple->buy{self.__getFloatRangeInfo(sampleQunta.buyRange, CoreEngine.quantFloatEncoder)}")
            # print(f"history->sell{self.__getFloatRangeInfo(historyQunta.sellRange, CoreEngine.quantFloatEncoder)}")
            # print(f"history->buy{self.__getFloatRangeInfo(historyQunta.buyRange, CoreEngine.quantFloatEncoder)}")
            # print(f"probal_sell_1: {self.__getFloatRangeInfo(predict.sellRange1, PredictModel.PctEncoder1)}")
            # print(f"probal_sell_2: {self.__getFloatRangeInfo(predict.sellRange2, PredictModel.PctEncoder2)}")
            # print(f"probal_buy_1: {self.__getFloatRangeInfo(predict.buyRange1, PredictModel.PctEncoder1)}")
            # print(f"probal_buy_2: {self.__getFloatRangeInfo(predict.buyRange2, PredictModel.PctEncoder2)}")
            # print(f"predict->  sell:{predict_sell_pct}, buy:{predict_buy_pct} ")
            # print(f"real   ->  sell:{sell_pct}, buy:{buy_pct} ")

            deal = True
            max_price = -99999999
            min_price = 999999999
            for bar in collectData.predictBars:
                max_price = max(max_price,bar.high_price)
                min_price = min(min_price,bar.low_price)
            max_pct = 100 * (max_price - occurBar.close_price) /occurBar.close_price
            #"是否预测成功"
            success = predict_sell_pct <= max_pct

            sell_price = collectData.predictBars[-1].close_price
            if success:
                sell_price = occurBar.close_price * (1+predict_sell_pct / 100)
            earn_pct = 100 * (sell_price - buy_price) / buy_price

        return deal,success,earn_pct

    def collect(self, barList: ['BarData'], symbol:str, collector:CoreStrategy) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
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

    dirName = "files/backtest"


    trainDataSouce = SWDataSource( start = datetime(2014, 2, 1),end = datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1),datetime(2020, 9, 1))
    from earnmi.model.Strategy2kAlgo1 import Strategy2kAlgo1
    strategy = Strategy2kAlgo1()
    #engine = CoreEngine.create(dirName,strategy,trainDataSouce)
    engine = CoreEngine.load(dirName,strategy)
    backtest = CoreEngineBackTest(engine)

    backtest.backtest(testDataSouce,strategy,limit=99999)


    pass