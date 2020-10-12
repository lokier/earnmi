
"""

核心引擎
"""
from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime, timedelta
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
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData
import numpy as np
import pandas as pd

"""
收集Collector数据。
"""




class CoreEngineRunner():

    def __init__(self,engine:CoreEngine):
        self.coreEngine:CoreEngine = engine
    """
    计算未来两天最有可能涨的股票SW指数。
    """
    def computeSWLatestTop(self, strategy:CoreStrategy,dimenValues:[]= None):
        end = utils.to_end_date(datetime.now() - timedelta(days=1))  ##昨天数据集
        start = end - timedelta(days=60)
        soruce = SWDataSource(start, end)

        print(f"computeSWLatestTop: end : {end},dimenValues:{dimenValues}")
        dataSet = {}
        canPredicCount = 0
        bars, code = soruce.onNextBars()
        while not bars is None:
            finished, stop = CoreStrategy.collectBars(bars, code, strategy)
            print(f"[computeSWLatestTop]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
            bars, code = soruce.onNextBars()
            for data in stop:
                if not strategy.canPredict(data):
                    continue
                allow_predict = True
                if len(dimenValues) > 0:
                    allow_predict = False
                    for value in dimenValues:
                        if value == data.dimen.value:
                            allow_predict = True
                if not allow_predict:
                    continue
                ##收录
                canPredicCount +=1
                listData: [] = dataSet.get(data.dimen)
                if listData is None:
                    listData = []
                    dataSet[data.dimen] = listData
                listData.append(data)
        print(f"收集到{canPredicCount}个预测对象,维度{len(dataSet)}个")

        @dataclass
        class TopItem(object):
            predict_price:float = 0
            duration_day = 0
            code:str = 0
            name:str = 0
            end_date:datetime = None

            def __str__(self) -> str:
                predict_price = int(self.predict_price * 100) / 100
                return f"code:{self.code},name:{self.name},day:{self.duration_day},predict_price:{predict_price},end_date:{self.end_date}"


        from earnmi.data.SWImpl import SWImpl
        sw = SWImpl()
        engine = self.coreEngine
        run_cnt = 0
        limit_size  = len(dataSet.items())
        topList = []
        for dimen, listData in dataSet.items():
            run_cnt +=1
            model = self.coreEngine.loadPredictModel(dimen)
            if model is None:
                print(f"不支持的维度:{dimen}")
                continue
            print(f"开始计算维度:{dimen},进度:[{run_cnt}/{limit_size}]")

            predictList: Sequence['PredictData'] = model.predict(listData)

            for predict in predictList:
                cData = predict.collectData
                predict_sell_pct, predict_buy_pct = engine.getCoreStrategy().getSellBuyPctPredict(predict)

                occurBar: BarData = cData.occurBars[-2]
                skipBar: BarData = cData.occurBars[-1]

                high_price = skipBar.close_price
                for i in range(0,len(cData.predictBars)):
                    bar = cData.predictBars[i]
                    high_price = max(bar.high_price,high_price)

                predict_price = occurBar.close_price * (1 + predict_sell_pct / 100)
                if high_price < predict_price:
                    topItem = TopItem()
                    topItem.code = occurBar.symbol
                    topItem.name = sw.getSw2Name(topItem.code)
                    topItem.duration_day = len(cData.predictBars)
                    topItem.predict_price = predict_price
                    topItem.end_date = skipBar.datetime
                    topList.append(topItem)

        for topItem in topList:
            print(f"{topItem}")
        print(f"total:{len(topList)}")

        pass

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
                break
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

    """"
    """
    def computeBuyPrice(self):

        return None

    def computePredict(self,predict:PredictData):
        deal = False
        success = False
        earn_pct = 0.0

        collectData = predict.collectData
        sampleQunta:QuantData = predict.quantData
        occurBar:BarData = collectData.occurBars[-2]
        skipBar:BarData = collectData.occurBars[-1]



        sell_pct,buy_pct = engine.getCoreStrategy().getSellBuyPctLabel(collectData)

        predict_sell_pct, predict_buy_pct = engine.getCoreStrategy().getSellBuyPctPredict(predict)
        buy_price = skipBar.close_price
        buy_point_pct = (buy_price - occurBar.close_price) / occurBar.close_price  ##买入的价格

        if predict_buy_pct > 0.2 and predict_sell_pct > buy_point_pct:
            quantFloatEncoder = sampleQunta.getFloatEncoder()
            print(f"\nsample->sell{self.__getFloatRangeInfo(sampleQunta.sellRange,quantFloatEncoder)}")
            print(f"sample->buy{self.__getFloatRangeInfo(sampleQunta.buyRange, quantFloatEncoder)}")
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
                sell_price = occurBar.close_price * (1+predict_sell_pct / 100)
            earn_pct = 100 * (sell_price - buy_price) / buy_price

        return deal,success,earn_pct



if __name__ == "__main__":

    dirName = "files/backtest"
    trainDataSouce = SWDataSource( start = datetime(2014, 2, 1),end = datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1),datetime(2020, 9, 1))
    from earnmi.model.Strategy2kAlgo1 import Strategy2kAlgo1
    strategy = Strategy2kAlgo1()
    engine = CoreEngine.create(dirName,strategy,trainDataSouce)
    #engine = CoreEngine.load(dirName,strategy)
    runner = CoreEngineRunner(engine)

    runner.backtest(testDataSouce,strategy,limit=99999)


    pass