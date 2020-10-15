
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
from earnmi.model.PredictOrder import PredictOrderStatus
from earnmi.model.QuantData import QuantData
from earnmi.model.CoreEngineModel import CoreEngineModel
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
    def computeSWLatestTop(self, strategy:CoreEngineModel, dimenValues:[]= None):
        end = utils.to_end_date(datetime.now() - timedelta(days=1))  ##昨天数据集
        start = end - timedelta(days=60)
        soruce = SWDataSource(start, end)

        print(f"computeSWLatestTop: end : {end},dimenValues:{dimenValues}")
        dataSet = {}
        canPredicCount = 0
        bars, code = soruce.onNextBars()
        while not bars is None:
            finished, stop = CoreEngineModel.collectBars(bars, code, strategy)
            print(f"[computeSWLatestTop]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
            bars, code = soruce.onNextBars()
            for data in stop:
                _basePrice,dd,xx = strategy.generateYLabel(self.coreEngine,data)
                noPredict =   _basePrice is None
                if  noPredict:
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

                predict_sell_pct, predict_buy_pct = engine.getEngineModel().getSellBuyPctPredict(predict)

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


    def backtest(self, soruce: BarDataSource, strategy:CoreEngineModel, limit=9999999):
        bars, code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        while not bars is None:
            finished, stop = CoreEngineModel.collectBars(bars, code, strategy)
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
            deal_count = 0
            predict_suc = 0
            count = 0
            sell_ok = 0
            buy_ok = 0
            earn_pct = 0.0
            loss_pct = 0.0
            eran_count = 0

            sell_core = 0.0  ##模型的分数
            buy_core =0.0   ##模型的分数

            def getOkRate(self) ->float:
                if self.deal_count > 0:
                   return self.predict_suc / self.deal_count
                return 0

            def __str__(self) -> str:
                earn_pct = 0.0
                lost_pct = 0.0
                if self.eran_count > 0:
                    earn_pct = self.earn_pct / self.eran_count
                if self.deal_count - self.eran_count > 0:
                    lost_pct = self.loss_pct / (self.deal_count - self.eran_count)
                ok_rate = self.getOkRate()
                test_sell_score = 100*self.sell_ok / self.count
                test_buy_score = 100*self.buy_ok / self.count

                return f"count:{self.count},deal_count:{self.deal_count},ok_rate:%.2f%%,earn:{self.eran_count}" \
                       f",earn_pct:%.2f%%,loss_pct:%.2f%%, " \
                       f"模型能力:[sell_core: %.2f,buy_core:%.2f,test_sell_score:%.2f,test_buy_score:%.2f]" % \
                       (ok_rate*100,earn_pct, lost_pct,100*self.sell_core,100*self.buy_core,test_sell_score,test_buy_score)

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
            predictList: Sequence['PredictData'] = model.predict(listData)
            dimenData = DimenData(dimen=dimen)
            abilityData = engine.queryPredictAbilityData(dimen)
            dimenData.sell_core = abilityData.sell_score_train
            dimenData.buy_core = abilityData.buy_score_train
            for predict in predictList:
                order = self.coreEngine.getEngineModel().generatePredictOrder(self.coreEngine,predict)

                for bar in predict.collectData.predictBars:
                    self.coreEngine.getEngineModel().updatePredictOrder(order, bar, True)
                dimenData.count +=1
                sell_ok,buy_ok = model.predictResult(predict)
                if sell_ok:
                    dimenData.sell_ok +=1
                if buy_ok:
                    dimenData.buy_ok +=1
                deal = order.status == PredictOrderStatus.CROSS
                if deal:
                    success = order.sellPrice == order.suggestSellPrice
                    if success:
                        dimenData.predict_suc +=1
                    pct = 100 * (order.sellPrice - order.buyPrice) / order.buyPrice
                    totalDeal += 1
                    dimenData.deal_count +=1
                    if pct > 0.0:
                        dimenData.earn_pct += pct
                        dimenData.eran_count +=1
                    else:
                        dimenData.loss_pct += pct
            totalOccurPredict += dimenData.count
            dimeDataList.append(dimenData)

        print("\n\n")
        total = DimenData(dimen=None)

        def diemdata_cmp(v1,v2):
            return v1.getOkRate() - v2.getOkRate()

        dimeDataList = sorted(dimeDataList, key=cmp_to_key(diemdata_cmp), reverse=False)
        for d in dimeDataList:
            total.loss_pct += d.loss_pct
            total.deal_count += d.deal_count
            total.eran_count += d.eran_count
            total.count += d.count
            total.earn_pct += d.earn_pct
            total.buy_ok +=d.buy_ok
            total.sell_ok += d.sell_ok
            total.predict_suc += d.predict_suc

            print(f"[{d.dimen.value}]: {d}")

        deal_rate = 0.0
        if totalOccurPredict > 0:
            deal_rate =  totalDeal / totalOccurPredict

        print(f"总共产生{totalOccurPredict}个预测,交易{totalDeal}个，交易率:%.2f%%" % (100 *deal_rate))
        print(f"total:{total}")

    def __getFloatRangeInfo(self,ranges:['FloatRange'],encoder:FloatEncoder):
        return FloatRange.toStr(ranges,encoder)

    """"
    """
    def computeBuyPrice(self):

        return None



if __name__ == "__main__":

    dirName = "files/backtest"
    trainDataSouce = SWDataSource( start = datetime(2014, 2, 1),end = datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1),datetime(2020, 9, 1))
    from earnmi.model.EngineModel2KAlgo1 import EngineModel2KAlgo1
    strategy = EngineModel2KAlgo1()
    engine = CoreEngine.create(dirName,strategy,trainDataSouce)
    #engine = CoreEngine.load(dirName,strategy)
    runner = CoreEngineRunner(engine)

    runner.backtest(testDataSouce,strategy,limit=1)


    """
    [884]: count:61,ok:46(75.41%),earn:45,earn_pct:0.65%,loss_pct:-0.84%, 模型能力:[sell_core: 99.59,buy_core:97.93]
    总共产生813个预测,交易61个，交易率:7.50%
    total:count:61,ok:46(75.41%),earn:45,earn_pct:0.65%,loss_pct:-0.84%, 模型能力:[sell_core: 0.00,buy_core:0.00]
    """

    """
    [884]: count:33,ok:13(39.39%),earn:17,earn_pct:1.06%,loss_pct:-1.93%, 模型能力:[sell_core: 99.65,buy_core:97.62]
总共产生813个预测,交易33个，交易率:4.06%
total:count:33,ok:13(39.39%),earn:17,earn_pct:1.06%,loss_pct:-1.93%, 模型能力:[sell_core: 0.00,buy_core:0.00]
    
    """

    pass