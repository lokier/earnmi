
"""

核心引擎
"""
from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
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
                ok_rate = 0
                if self.count > 0:
                    ok_rate = self.countOk / self.count
                return f"count:{self.count},ok:{self.countOk}(%.2f%%),earn:{self.eran_count},earn_pct:%.2f%%,loss_pct:%.2f%%" % (ok_rate*100,earn_pct, lost_pct)

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
        earn_pct = 0.0

        collectData = predict.collectData
        quantoEncoder = CoreEngine.quantFloatEncoder
        historyQunta = predict.historyData
        sampleQunta = predict.sampleData
        occurBar:BarData = collectData.occurBars[-2]
        skipBar:BarData = collectData.occurBars[-1]



        sell_pct,buy_pct = engine.getCoreStrategy().getSellBuyPctLabel(collectData)


        min1,max1 = PredictModel.PctEncoder1.parseEncode(predict.sellRange1[0].encode)
        min2,max2 = PredictModel.PctEncoder2.parseEncode(predict.sellRange2[0].encode)
        total_probal = predict.sellRange2[0].probal + predict.sellRange1[0].probal
        predict_sell_pct = (min1 + max1) / 2 * predict.sellRange1[0].probal /total_probal + (min2 + max2) / 2 * predict.sellRange2[0].probal /total_probal

        min1, max1 = PredictModel.PctEncoder1.parseEncode(predict.buyRange1[0].encode)
        min2, max2 = PredictModel.PctEncoder2.parseEncode(predict.buyRange2[0].encode)
        total_probal = predict.sellRange2[0].probal + predict.sellRange1[0].probal
        predict_buy_pct = (min1 + max1) / 2 * predict.buyRange1[0].probal /total_probal + (min2 + max2) / 2 * predict.buyRange2[0].probal /total_probal

        buy_price = skipBar.close_price
        buy_pct = (buy_price - occurBar.close_price) / occurBar.close_price  ##买入的价格

        if predict_buy_pct > 0.2 and predict_sell_pct > buy_pct:

            print(f"\nsmaple->sell{self.__getFloatRangeInfo(sampleQunta.sellRange, CoreEngine.quantFloatEncoder)}")
            print(f"smaple->buy{self.__getFloatRangeInfo(sampleQunta.buyRange, CoreEngine.quantFloatEncoder)}")
            print(f"history->sell{self.__getFloatRangeInfo(historyQunta.sellRange, CoreEngine.quantFloatEncoder)}")
            print(f"history->buy{self.__getFloatRangeInfo(historyQunta.buyRange, CoreEngine.quantFloatEncoder)}")
            print(f"probal_sell_1: {self.__getFloatRangeInfo(predict.sellRange1, PredictModel.PctEncoder1)}")
            print(f"probal_sell_2: {self.__getFloatRangeInfo(predict.sellRange2, PredictModel.PctEncoder2)}")
            print(f"probal_buy_1: {self.__getFloatRangeInfo(predict.buyRange1, PredictModel.PctEncoder1)}")
            print(f"probal_buy_2: {self.__getFloatRangeInfo(predict.buyRange2, PredictModel.PctEncoder2)}")
            print(f"predict->  sell:{predict_sell_pct}, buy:{predict_buy_pct} ")
            print(f"real   ->  sell:{sell_pct}, buy:{buy_pct} ")

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
                sell_price = occurBar.close_price * (1+predict_sell_pct)
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

    class Collector2KAgo1(CoreStrategy):

        def __init__(self):
            self.lasted3Bar = np.array([None,None,None])
            self.lasted3BarKdj = np.array([None,None,None])

        def onCollectStart(self, code: str) -> bool:
            from earnmi.chart.Indicator import Indicator
            self.indicator = Indicator(40)
            self.code = code
            return True

        def onCollectTrace(self, bar: BarData) -> CollectData:
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

        def onCollect(self, data: CollectData, newBar: BarData) -> bool:
            if len(data.occurBars) < 3:
                data.occurBars.append(self.lasted3Bar[-1])
                data.occurKdj.append(self.lasted3BarKdj[-1])
            else:
                data.predictBars.append(newBar)
            size = len(data.predictBars)
            return size >= 2

        def getSellBuyPctLabel(self, collectData: CollectData):
            bars: ['BarData'] = collectData.predictBars
            if len(bars) > 0:
                occurBar = collectData.occurBars[-2]
                startPrice = occurBar.close_price
                sell_pct = -99999
                buy_pct = 9999999
                for bar in bars:
                    __sell_pct = 100 * ((bar.high_price + bar.close_price) / 2 - startPrice) / startPrice
                    __buy_pct = 100 * ((bar.low_price + bar.close_price) / 2 - startPrice) / startPrice
                    sell_pct = max(__sell_pct, sell_pct)
                    buy_pct = min(__buy_pct, buy_pct)
                return sell_pct, buy_pct
            return None, None

        def __genereatePd(self, dataList: Sequence['CollectData']):
            trainDataSet = []
            for traceData in dataList:
                occurBar = traceData.occurBars[-2]
                assert len(traceData.predictBars) > 0
                skipBar = traceData.occurBars[-1]
                sell_pct = 100 * (
                        (skipBar.high_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price
                buy_pct = 100 * (
                        (skipBar.low_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price

                real_sell_pct, real_buy_pct = self.getSellBuyPctLabel(traceData)
                label_sell_1 = PredictModel.PctEncoder1.encode(real_sell_pct)
                label_sell_2 = PredictModel.PctEncoder2.encode(real_sell_pct)
                label_buy_1 = PredictModel.PctEncoder1.encode(real_buy_pct)
                label_buy_2 = PredictModel.PctEncoder2.encode(real_buy_pct)

                kdj = traceData.occurKdj[-1]

                data = []
                data.append(buy_pct)
                data.append(sell_pct)
                data.append(kdj[0])
                data.append(kdj[2])
                data.append(label_sell_1)
                data.append(label_buy_1)
                data.append(label_sell_2)
                data.append(label_buy_2)
                trainDataSet.append(data)
            cloumns = ["buy_pct",
                       "sell_pct",
                       "k",
                       "j",
                       "label_sell_1",
                       "label_buy_1",
                       "label_sell_2",
                       "label_buy_2",
                       ]
            orgin_pd = pd.DataFrame(trainDataSet, columns=cloumns)
            return orgin_pd

        """
        生成特征值。(有4个标签）
        返回值为：x, y_sell_1,y_buy_1,y_sell_2,y_buy_2
        """
        def generateFeature(self, engine, dataList: Sequence['CollectData']):
            engine.printLog(f"[SVMPredictModel]: generate feature")

            def set_0_between_100(x):
                if x > 100:
                    return 100
                if x < 0:
                    return 0
                return x

            def percent_to_one(x):
                return int(x * 100) / 1000.0

            def toInt(x):
                v = int(x + 0.5)
                if v > 10:
                    v = 10
                if v < -10:
                    v = -10
                return v

            d = self.__genereatePd(dataList)
            engine.printLog(f"   origin:\n{d.head()}")

            d['buy_pct'] = d.buy_pct.apply(percent_to_one)  # 归一化
            d['sell_pct'] = d.sell_pct.apply(percent_to_one)  # 归一化
            d.k = d.k.apply(set_0_between_100)
            d.j = d.j.apply(set_0_between_100)
            d.k = d.k / 100
            d.j = d.j / 100
            engine.printLog(f"   convert:\n{d.head()}")
            data = d.values
            x, y = np.split(data, indices_or_sections=(4,), axis=1)  # x为数据，y为标签
            y_1 = y[:, 0:1].flatten()  # 取第一列
            y_2 = y[:, 1:2].flatten()  # 取第一列
            y_3 = y[:, 2:3].flatten()  # 取第一列
            y_4 = y[:, 3:4].flatten()  # 取第一列

            engine.printLog(f"   y_1:\n{y_1}")
            engine.printLog(f"   y_2:\n{y_2}")
            engine.printLog(f"   y_3:\n{y_3}")
            engine.printLog(f"   y_4:\n{y_4}")

            engine.printLog(f"[SVMPredictModel]: generate feature end!!!")
            return x, y_1, y_2, y_3, y_4

    trainDataSouce = SWDataSource( start = datetime(2014, 2, 1),end = datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1),datetime(2020, 9, 1))


    dirName = "files/backtest"
    strategy = Collector2KAgo1()
    #engine = CoreEngine.create(dirName,strategy,trainDataSouce)
    engine = CoreEngine.load(dirName,strategy)
    backtest = CoreEngineBackTest(engine)

    backtest.backtest(testDataSouce,strategy,limit=1)


    pass