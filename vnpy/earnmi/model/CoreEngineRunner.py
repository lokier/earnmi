
"""

核心引擎
"""
from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cmp_to_key
from typing import Union, Tuple, Sequence

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange
from earnmi.data.SWImpl import SWImpl
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngine import CoreEngine, BarDataSource,PredictModel
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.CoreEngineStrategy import CoreEngineStrategy
from earnmi.model.Dimension import Dimension, TYPE_2KAGO1
from earnmi.model.PredictAbilityData import PredictAbilityData
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrderStatus, PredictOrder
from earnmi.model.QuantData import QuantData
from earnmi.model.CoreEngineModel import CoreEngineModel
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData
import numpy as np
import pandas as pd

"""
收集Collector数据。
"""


@dataclass
class BackTestData(object):
    dimen: Dimension
    deal_count = 0
    predict_suc = 0
    count = 0
    sell_ok = 0
    buy_ok = 0
    earn_pct = 0.0
    loss_pct = 0.0
    eran_count = 0
    power_quant = 0.0
    power_predict = 0.0

    quant: QuantData = None
    abilityData: PredictAbilityData = None

    def getEarnRate(self) -> float:
        if self.deal_count > 0:
            return self.predict_suc / self.deal_count
        return 0

    def getSellScore(self):
        return 100 * self.sell_ok / self.count

    def getBuyScore(self):
        return 100 * self.buy_ok / self.count

    def __str__(self) -> str:
        earn_pct = 0.0
        lost_pct = 0.0
        if self.eran_count > 0:
            earn_pct = self.earn_pct / self.eran_count
        if self.deal_count - self.eran_count > 0:
            lost_pct = self.loss_pct / (self.deal_count - self.eran_count)
        ok_rate = self.getEarnRate()

        return f"count:{self.count}(test_sell_score:%.2f,test_buy_score:%.2f),deal_count:{self.deal_count},ok_rate:%.2f%%,earn:{self.eran_count}" \
               f",earn_pct:%.2f%%,loss_pct:%.2f%%, " \
               f"模型能力:[pow:%.2f]" % \
               (self.getSellScore(), self.getBuyScore(), ok_rate * 100, earn_pct, lost_pct, self.power_quant)


class CoreEngineRunner():

    def __init__(self,engine:CoreEngine):
        self.coreEngine:CoreEngine = engine
    """
    计算未来两天最有可能涨的股票SW指数。
    """
    def debugBestParam(self,  soruce: BarDataSource, strategy:CoreEngineStrategy, params:{},min_deal_count = -1, max_run_count = 999999999):
        bars, code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        model = self.coreEngine.getEngineModel()
        while not bars is None:
            # self.coreEngine.getEngineModel().collectBars(bars,code)
            finished, stop = model.collectBars(bars, code)
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

        max_run_count = min(max_run_count,len(dataSet))
        run_cnt = 0

        for paramName, paramsList in params.items():
            # 计算paramName的 value 值。
            for dimen, listData in dataSet.items():
                if run_cnt >= max_run_count:
                    break
                model = self.coreEngine.loadPredictModel(dimen)
                if model is None:
                    print(f"不支持的维度:{dimen}")
                    continue
                run_cnt += 1
                print(f"开始回测维度:{dimen},进度:[{run_cnt}/{max_run_count}]")
                predictList: Sequence['PredictData'] = model.predict(listData)
                for predict in predictList:
                    order = strategy.generatePredictOrder(self.coreEngine, predict)
                    for bar in predict.collectData.predictBars:
                        strategy.updatePredictOrder(order, bar, True)


    def backtest(self, soruce: BarDataSource, strategy:CoreEngineStrategy, min_deal_count = -1):
        bars, code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        model = self.coreEngine.getEngineModel()
        while not bars is None:
            #self.coreEngine.getEngineModel().collectBars(bars,code)
            finished, stop = model.collectBars(bars, code)
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

        __dataList:['BackTestData'] = []
        run_cnt = 0
        run_limit_size = len(dataSet)
        for dimen, listData in dataSet.items():
            if run_cnt >= run_limit_size:
                break
            model = self.coreEngine.loadPredictModel(dimen)
            if model is None:
                print(f"不支持的维度:{dimen}")
                continue
            run_cnt +=1
            print(f"开始回测维度:{dimen},进度:[{run_cnt}/{run_limit_size}]")
            predictList: Sequence['PredictData'] = model.predict(listData)
            _testData = BackTestData(dimen=dimen)
            abilityData = self.coreEngine.queryPredictAbilityData(dimen)
            _testData.abilityData = abilityData
            _testData.quant = self.coreEngine.queryQuantData(dimen)
            _testData.power_predict = 0

            for predict in predictList:
                order = strategy.generatePredictOrder(self.coreEngine,predict)
                for bar in predict.collectData.predictBars:
                    strategy.updatePredictOrder(order, bar, True)
                self.putToStatistics(_testData,order,predict)

            if _testData.deal_count > 0:
                _testData.power_predict = _testData.power_predict / _testData.deal_count
            __dataList.append(_testData)

        return self.__genrateAndPrintPdData(__dataList,min_deal_count)

    def __genrateAndPrintPdData(self,__dataList:['BackTestData'],min_deal_count:int):


        total = BackTestData(dimen=None)

        def diemdata_cmp(v1, v2):
            return v1.getEarnRate() - v2.getEarnRate()

        __dataList = sorted(__dataList, key=cmp_to_key(diemdata_cmp), reverse=False)
        columns = ["dimen", "count", "dealCount", "earnRate", "earnPct", "lossPct", "sScore", "bScore", "avg_power",
                   "量化数据:", "power", "count", "sCPct", "bCPct", "预测能力:", "countTrain", "sScoreTrain", "bScoreTrain",
                   "countTest", "sScoreTest", "bScoreTest"]
        values = []
        print("\n\n")
        for d in __dataList:
            if d.deal_count < min_deal_count:
                continue
            item = []
            item.append(d.dimen.value)
            item.append(d.count)
            item.append(d.deal_count)
            item.append(d.getEarnRate())
            item.append(d.earn_pct)
            item.append(d.loss_pct)
            item.append(d.getSellScore())
            item.append(d.getBuyScore())
            item.append(d.power_predict)
            item.append("")
            item.append(d.power_quant)
            item.append(d.quant.count)
            item.append(d.quant.sellCenterPct)
            item.append(d.quant.buyCenterPct)
            item.append("")
            item.append(d.abilityData.count_train)
            item.append(d.abilityData.sell_score_train)
            item.append(d.abilityData.buy_score_train)
            item.append(d.abilityData.count_test)
            item.append(d.abilityData.sell_score_test)
            item.append(d.abilityData.buy_score_test)
            values.append(item)

            total.loss_pct += d.loss_pct
            total.deal_count += d.deal_count
            total.eran_count += d.eran_count
            total.count += d.count
            total.earn_pct += d.earn_pct
            total.buy_ok += d.buy_ok
            total.sell_ok += d.sell_ok
            total.predict_suc += d.predict_suc

            print(f"[{d.dimen.value}]: {d}")

        deal_rate = 0.0
        if total.count > 0:
            deal_rate = total.deal_count / total.count

        print(f"总共产生{total.count}个预测,交易{total.deal_count}个，交易率:%.2f%%" % (100 * deal_rate))
        print(f"total:{total}")

        return pd.DataFrame(values, columns=columns)


    def putToStatistics(self, data:BackTestData, order,predict:PredictData):
        data.count += 1
        high_price = -99999999
        low_price = -high_price
        for bar in predict.collectData.predictBars:
            high_price = max(high_price, bar.high_price)
            low_price = min(low_price, bar.low_price)
        basePrice = self.coreEngine.getEngineModel().getYBasePrice(predict.collectData)
        sell_price = basePrice * (1 + predict.getPredictSellPct() / 100)
        buy_price = basePrice * (1 + predict.getPredictBuyPct() / 100)

        ## 预测价格有无到底最高价格
        sell_ok = high_price >= sell_price
        buy_ok = low_price <= buy_price

        if sell_ok:
            data.sell_ok += 1
        if buy_ok:
            data.buy_ok += 1
        deal = order.status == PredictOrderStatus.CROSS
        if deal:
            success = order.sellPrice == order.suggestSellPrice
            if success:
                data.predict_suc += 1
            pct = 100 * (order.sellPrice - order.buyPrice) / order.buyPrice
            data.deal_count += 1
            data.power_predict += predict.getPowerRate()
            data.power_quant = order.power_rate
            if pct > 0.0:
                data.earn_pct += pct
                data.eran_count += 1
            else:
                data.loss_pct += pct



    def __getFloatRangeInfo(self,ranges:['FloatRange'],encoder:FloatEncoder):
        return FloatRange.toStr(ranges,encoder)

    """"
    """
    def computeBuyPrice(self):

        return None



if __name__ == "__main__":

    class MyStrategy(CoreEngineStrategy):
        def __init__(self):
            self.sw = SWImpl()

        def generatePredictOrder(self, engine: CoreEngine, predict: PredictData) -> PredictOrder:
            code = predict.collectData.occurBars[-1].symbol
            name = self.sw.getSw2Name(code)
            order = PredictOrder(dimen=predict.dimen, code=code, name=name)
            from earnmi.model.CoreEngine import PredictModel
            predict_sell_pct = predict.getPredictSellPct()
            predict_buy_pct = predict.getPredictSellPct()
            start_price = engine.getEngineModel().getYBasePrice(predict.collectData)
            order.suggestSellPrice = start_price * (1 + predict_sell_pct / 100)
            order.suggestBuyPrice = start_price * (1 + predict_buy_pct / 100)
            order.power_rate = engine.queryQuantData(predict.dimen).getPowerRate()

            ##for backTest
            occurBar: BarData = predict.collectData.occurBars[-2]
            skipBar: BarData = predict.collectData.occurBars[-1]
            buy_price = skipBar.close_price
            predict_sell_pct = 100 * (order.suggestSellPrice - start_price) / start_price
            predict_buy_pct = 100 * (order.suggestBuyPrice - start_price) / start_price
            buy_point_pct = 100 * (buy_price - occurBar.close_price) / occurBar.close_price  ##买入的价格

            abilityData = engine.queryPredictAbilityData(predict.dimen)
            quantData = engine.queryQuantData(predict.dimen)
            delta = abs(quantData.sellCenterPct) - abs(quantData.buyCenterPct)
            if abs(delta) < 0.05:
                # 多空力量差不多
                power = 0
            if delta > 0:
                # 适合做多
                power= (quantData.sellCenterPct + quantData.buyCenterPct) / quantData.sellCenterPct
            else:
                power = - (quantData.sellCenterPct + quantData.buyCenterPct) / quantData.buyCenterPct

            if predict_buy_pct > 0.2 and predict_sell_pct - buy_point_pct > 1:
                order.status = PredictOrderStatus.HOLD
                order.buyPrice = buy_price
            else:
                order.status = PredictOrderStatus.STOP
            return order

        def updatePredictOrder(self, order: PredictOrder, bar: BarData, isTodayLastBar: bool):
            if (order.status == PredictOrderStatus.HOLD):
                if bar.high_price >= order.suggestSellPrice:
                    order.sellPrice = order.suggestSellPrice
                    order.status = PredictOrderStatus.CROSS
                    return
                order.holdDay += 1
                if order.holdDay >= 2:
                    order.sellPrice = bar.close_price
                    order.status = PredictOrderStatus.CROSS
                    return

    dirName = "files/backtest"
    trainDataSouce = SWDataSource( start = datetime(2014, 2, 1),end = datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1),datetime(2020, 9, 1))
    from earnmi.model.EngineModel2KAlgo1 import EngineModel2KAlgo1
    model = EngineModel2KAlgo1()
    #engine = CoreEngine.create(dirName,model,trainDataSouce,limit_dimen_size=1)
    engine = CoreEngine.load(dirName,model)
    runner = CoreEngineRunner(engine)
    strategy = MyStrategy()
    pdData = runner.backtest(testDataSouce,strategy,min_deal_count = 15)

    writer = pd.ExcelWriter('files\CoreEngineRunner.xlsx')
    pdData.to_excel(writer, sheet_name="data", index=False)
    writer.save()
    writer.close()


    pass