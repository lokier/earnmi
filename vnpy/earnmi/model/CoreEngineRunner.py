
"""

核心引擎
"""
from dataclasses import dataclass
from datetime import datetime,timedelta
from functools import cmp_to_key
from typing import Sequence

import pandas as pd

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange
from earnmi.data.SWImpl import SWImpl
from earnmi.model.CoreEngine import CoreEngine, BarDataSource
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.CoreEngineStrategy import CoreEngineStrategy
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictAbilityData import PredictAbilityData
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrderStatus, PredictOrder
from earnmi.model.QuantData import QuantData
from vnpy.trader.object import BarData

"""
收集Collector数据。
"""


@dataclass
class BackTestData(object):
    dimen: Dimension
    count = 0
    sell_ok = 0
    buy_ok = 0

    deal_count = 0   ##
    dec_suc_count = 0  ##处理并成功预测的个数
    earn_pct = 0.0
    loss_pct = 0.0
    eran_count = 0

    quant: QuantData = None
    abilityData: PredictAbilityData = None

    def getEarnRate(self) -> float:
        if self.deal_count > 0:
            return self.dec_suc_count / self.deal_count
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
               f",earn_pct:%.2f%%,loss_pct:%.2f%%, " % \
               (self.getSellScore(), self.getBuyScore(), ok_rate * 100, earn_pct, lost_pct)


class CoreEngineRunner():

    def __init__(self,engine:CoreEngine):
        self.coreEngine:CoreEngine = engine
    """
    计算未来两天最有可能涨的股票SW指数。
    """
    def debugBestParam(self,  soruce: BarDataSource, strategy:CoreEngineStrategy, params:{},min_deal_count = -1, max_run_count = 999999999,printDetail = False):
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

        __dataDetailSet = {}
        __dataTotalSet = {}
        for paramName, paramsList in params.items():
            # 计算paramName的 value 值。
            _paramNameSet = {}
            __dataDetailSet[paramName] = _paramNameSet

            _paramTotalSet = {}
            __dataTotalSet[paramName] = _paramTotalSet
            for paramValue in paramsList:
                _paramTotalSet[paramValue] = []

            for dimen, listData in dataSet.items():
                if run_cnt >= max_run_count:
                    break
                model = self.coreEngine.loadPredictModel(dimen)
                if model is None:
                    print(f"不支持的维度:{dimen}")
                    continue
                run_cnt += 1
                print(f"开始回测维度:{dimen},进度:[{run_cnt}/{max_run_count}]")

                ##开始计算dimen，在paramName各个参数值的情况。
                dimenSet = _paramNameSet.get(dimen)
                if dimenSet is None:
                    dimenSet = {}
                    _paramNameSet[dimen] = dimenSet
                for paramValue in paramsList:
                    __dataList = []
                    _testData = BackTestData(dimen=dimen)
                    _testData.abilityData = self.coreEngine.queryPredictAbilityData(dimen)
                    _testData.quant = self.coreEngine.queryQuantData(dimen)
                    __the_param = {paramName:paramValue}

                    predictList: Sequence['PredictData'] = model.predict(listData)
                    for predict in predictList:
                        order = strategy.generatePredictOrder(self.coreEngine, predict,__the_param)
                        for bar in predict.collectData.predictBars:
                            strategy.updatePredictOrder(order, bar, True,__the_param)
                        self.putToStatistics(_testData, order, predict)
                    __dataList.append(_testData)
                    totalData = self.__combine(__dataList,min_deal_count)
                    dimenSet[paramValue] = totalData
                    _paramTotalSet[paramValue].append(totalData)

        for paramName, paramsList in params.items():
            _paramNameSet = __dataDetailSet[paramName]
            if len(_paramNameSet) < 1:
                print(f"参数值{paramName}为空数据!!!!")
            print(f"参数值{paramName}的总体数据情况:")
            _paramTotalSet = __dataTotalSet[paramName]
            for paramValue in paramsList:
                 __dataList = _paramTotalSet.get(paramValue)
                 totalData = self.__combine(__dataList, min_deal_count)
                 print(f"    [{paramValue}]: {totalData}")
            if printDetail:
                print(f"参数值{paramName}的具体每个维度的情况:")
                ##每个dimen的维度情况。
                for dimen,dimenSet in _paramNameSet.items():
                    print(f"   dimen = {dimen}:")
                    paramValues = dimenSet.keys()
                    for paramValue in paramValues:
                        totalData:BackTestData = dimenSet.get(paramValue)
                        print(f"          [{paramValue}]: {totalData}")

    """
    获取申万当前的操作单
    """
    def getSWCurrentPredictOrder(self,strategy:CoreEngineStrategy):
        end = datetime.now()
        start = end - timedelta(days=100)
        soruce = SWDataSource(start, end)
        bars, code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        model = self.coreEngine.getEngineModel()
        orderList: Sequence['PredictOrder'] = []
        while not bars is None:
            # self.coreEngine.getEngineModel().collectBars(bars,code)
            finished, stop = model.collectBars(bars, code)
            print(f"[backtest]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
            totalCount += len(stop)
            bars, code = soruce.onNextBars()
            for data in stop:
                ##收录
                listData: [] = dataSet.get(data.dimen)
                if listData is None:
                    listData = []
                    dataSet[data.dimen] = listData
                listData.append(data)

        for dimen, listData in dataSet.items():
            model = self.coreEngine.loadPredictModel(dimen)
            if model is None:
                print(f"不支持的维度:{dimen}")
                continue
            predictList: Sequence['PredictData'] = model.predict(listData)
            for predict in predictList:
                order = strategy.generatePredictOrder(self.coreEngine, predict)
                for bar in predict.collectData.predictBars:
                    strategy.updatePredictOrder(order, bar, True, None)
                if order.status == PredictOrderStatus.HOLD or \
                    order.status == PredictOrderStatus.CROSS:
                    orderList.append(order)
        return orderList

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
            _testData.abilityData = self.coreEngine.queryPredictAbilityData(dimen)
            _testData.quant = self.coreEngine.queryQuantData(dimen)

            for predict in predictList:
                order = strategy.generatePredictOrder(self.coreEngine,predict)
                for bar in predict.collectData.predictBars:
                    strategy.updatePredictOrder(order, bar, True,None)
                self.putToStatistics(_testData,order,predict)

            __dataList.append(_testData)

        pdData =  self.__genrateAndPrintPdData(__dataList,min_deal_count)
        print(f"{pdData.head(20)}")
        return pdData

    def __combine(self,__dataList:['BackTestData'],min_deal_count):
        total = BackTestData(dimen=None)
        for d in __dataList:
            if d.deal_count < min_deal_count:
                continue
            total.loss_pct += d.loss_pct
            total.deal_count += d.deal_count
            total.eran_count += d.eran_count
            total.dec_suc_count += d.dec_suc_count
            total.count += d.count
            total.earn_pct += d.earn_pct
            total.buy_ok += d.buy_ok
            total.sell_ok += d.sell_ok
        deal_rate = 0.0
        if total.count > 0:
            deal_rate = total.deal_count / total.count

        return total

    def __genrateAndPrintPdData(self,__dataList:['BackTestData'],min_deal_count:int,debugy_param:[] = None):


        def diemdata_cmp(v1, v2):
            return v1.getEarnRate() - v2.getEarnRate()
        __dataList = sorted(__dataList, key=cmp_to_key(diemdata_cmp), reverse=True)
        columns = ["dimen", "总数", "操作数", "盈利率", "总盈利", "总亏损", "分数|卖", "分数|买",
                   "量化数据:", "power", "count", "sCPct", "bCPct", "预测能力:",
                   "count", "sScore", "bScore","sBiasWin", "bBiasWin", "sBiasLoss","bBiasLoss"]
        values = []
        for d in __dataList:
            if d.deal_count < min_deal_count:
                continue
            item = []
            if(d.dimen is None):
                item.append(-1)
            else:
                item.append(d.dimen.value)
            item.append(d.count)
            item.append(d.deal_count)
            item.append(d.getEarnRate())
            item.append(d.earn_pct)
            item.append(d.loss_pct)
            item.append(d.getSellScore())
            item.append(d.getBuyScore())
            item.append("")
            item.append(d.quant.getPowerRate())
            item.append(d.quant.count)
            item.append(d.quant.sellCenterPct)
            item.append(d.quant.buyCenterPct)
            item.append("")
            ability:PredictAbilityData = d.abilityData
            item.append(ability.getCount())
            item.append(ability.getScoreSell())
            item.append(ability.getScoreBuy())

            item.append(ability.getBiasSell(True))
            item.append(ability.getBiasBuy(True))
            item.append(ability.getBiasSell(False))
            item.append(ability.getBiasBuy(False))

            values.append(item)

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
                data.dec_suc_count += 1
            pct = 100 * (order.sellPrice - order.buyPrice) / order.buyPrice
            data.deal_count += 1
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

        def generatePredictOrder(self, engine: CoreEngine, predict: PredictData,debugPrams:{}=None) -> PredictOrder:

            if debugPrams is None:
                debugPrams = {}

            code = predict.collectData.occurBars[-1].symbol
            name = self.sw.getSw2Name(code)
            order = PredictOrder(dimen=predict.dimen, code=code, name=name)
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

            extraCondition = True
            quant_power = debugPrams.get("quant_power")
            if not quant_power is None:
                extraCondition = extraCondition and predict.quantData.getPowerRate() >= quant_power

            predict_buy_pct_param = debugPrams.get("predict_buy_pct")
            if not predict_buy_pct_param is None:
                extraCondition = extraCondition and predict_buy_pct >= predict_buy_pct_param

            if extraCondition and predict_sell_pct - buy_point_pct > 1 \
                and abilityData.trainData.biasSellLoss < 10:
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

    class QuantStrategy(CoreEngineStrategy):
        def __init__(self):
            self.sw = SWImpl()

        def generatePredictOrder(self, engine: CoreEngine, predict: PredictData,debugPrams:{}=None) -> PredictOrder:

            if debugPrams is None:
                debugPrams = {}
            quantData = engine.queryQuantData(predict.dimen)
            code = predict.collectData.occurBars[-1].symbol
            name = self.sw.getSw2Name(code)
            order = PredictOrder(dimen=predict.dimen, code=code, name=name)
            start_price = engine.getEngineModel().getYBasePrice(predict.collectData)

            _min, _max = quantData.getSellFloatEncoder().parseEncode(quantData.sellRange[0].encode)
            order.suggestSellPrice = start_price * (1 + (_min +  _max) / 2 / 100)
            _min, _max = quantData.getBuyFloatEncoder().parseEncode(quantData.buyRange[0].encode)
            order.suggestBuyPrice = start_price * (1 + (_min +  _max) / 2 / 100)

            order.power_rate = quantData.getPowerRate();

            ##for backTest
            self.checkIfBuyPrice(order,predict.collectData.occurBars[-1].close_price,debugPrams)
            return order

        def checkIfBuyPrice(self,order: PredictOrder,targetPrice:float,debugPrams:{}=None):
            if order.status != PredictOrderStatus.TRACE:
                return
            quantData = engine.queryQuantData(order.dimen)

            if quantData.getPowerRate() > 0.9 and order.suggestBuyPrice >= targetPrice:
                order.status = PredictOrderStatus.HOLD
                order.buyPrice = targetPrice

        def updatePredictOrder(self, order: PredictOrder, bar: BarData, isTodayLastBar: bool,debugPrams:{}):
            if (order.status == PredictOrderStatus.HOLD):
                if bar.high_price >= order.suggestSellPrice:
                    order.sellPrice = order.suggestSellPrice
                    order.status = PredictOrderStatus.CROSS
                    return
                if order.holdDay >= 1:
                    order.sellPrice = bar.close_price
                    order.status = PredictOrderStatus.CROSS
                    return
            order.holdDay += 1
            self.checkIfBuyPrice(order,bar.low_price,debugPrams)

    dirName = "files/backtest"
    trainDataSouce = SWDataSource( start = datetime(2014, 2, 1),end = datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1),datetime(2020, 9, 1))
    from earnmi.model.EngineModel2KAlgo1 import EngineModel2KAlgo1
    model = EngineModel2KAlgo1()
    #engine = CoreEngine.create(dirName,model,trainDataSouce,limit_dimen_size=9999999)
    engine = CoreEngine.load(dirName,model)
    runner = CoreEngineRunner(engine)
    #strategy = MyStrategy()
    strategy = QuantStrategy()


    # parasMap = {
    #     #"quant_power":[0.3,0.4,0.5,0.6,0.7,0.8,0.9,1],
    #     "predict_buy_pct":[-1.5,-1,-0.5,0, 0.5, 1],
    # }
    # runner.debugBestParam(testDataSouce,strategy,parasMap,max_run_count=1,min_deal_count = 15,printDetail = True);

    pdData = runner.backtest(testDataSouce,strategy,min_deal_count = 15)
    writer = pd.ExcelWriter('files/CoreEngineRunner.xlsx')
    pdData.to_excel(writer, sheet_name="data", index=False)
    writer.save()
    writer.close()


    pass