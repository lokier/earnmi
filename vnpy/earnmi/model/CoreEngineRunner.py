
"""

核心引擎
"""
import math
import sys
from dataclasses import dataclass
from datetime import datetime,timedelta
from functools import cmp_to_key
from typing import Sequence

import pandas as pd

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange
from earnmi.data.SWImpl import SWImpl
from earnmi.model.BarDataSource import BarDataSource, ZZ500DataSource
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.CoreEngineStrategy import CoreEngineStrategy
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictAbilityData import PredictAbilityData
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrderStatus, PredictOrder
from earnmi.model.QuantData import QuantData
from earnmi.uitl.BarUtils import BarUtils
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData

"""
收集Collector数据。
"""
class BackTestItemData(object):
    deal_count = 0  ##交易总数
    suc_count = 0   ##交易按预测情况成功次数
    earn_pct_total = 0.0  #实际总盈利（没有达到预测情况也可能盈利）
    loss_pct_total = 0.0  #实际总亏损
    eran_count = 0  #盈利次数
    earn_pct_max = 0
    loss_pct_max = 0

    def addTo(self,total):
        total.deal_count += self.deal_count
        total.suc_count += self.suc_count
        total.earn_pct_total += self.earn_pct_total
        total.loss_pct_total += self.loss_pct_total
        total.eran_count += self.eran_count
        total.earn_pct_max = max(self.earn_pct_max,total.earn_pct_max)
        total.loss_pct_max = min(self.loss_pct_max,total.loss_pct_max)


    def loss_cout(self):
        return self.deal_count - self.eran_count

    def deal_rate(self,total_count):
        if total_count < 1:
            return 0
        return  self.deal_count /total_count

    def suc_rate(self):
        if self.deal_count < 1:
            return 0.0
        return self.suc_count / self.deal_count

    def earn_rate(self):
        if self.deal_count < 1:
            return 0;
        return self.eran_count /self.deal_count

    def total_pct_avg(self):
        if self.deal_count < 1:
            return 0
        return (self.earn_pct_total + self.loss_pct_total) / self.deal_count

    def earn_pct_avg(self):
        if self.eran_count < 1:
            return 0
        return self.earn_pct_total / self.eran_count

    def loss_pct_avg(self):
        if self.loss_cout() < 1:
            return 0
        return self.loss_pct_total / self.loss_cout()

    def toStr(self,totolCount) -> str:
       return f"交易率:%.2f%%,成功率:%.2f%%,盈利率:%.2f%%,单均pct:%.2f,盈pct:%.2f(%.2f),亏pct:%.2f(%.2f)" % \
         ( 100 * self.deal_rate(totolCount), 100 * self.suc_rate(), 100 * self.earn_rate(),
          self.total_pct_avg(),self.earn_pct_avg(),self.earn_pct_max,
          self.loss_pct_avg(),self.loss_pct_max)


@dataclass
class BackTestData(object):
    dimen: Dimension
    count = 0   ##产生操作单次数
    sell_ok = 0  ##预测做多成功次数（不含交易）
    buy_ok = 0  ##预测做空成功次数（不含交易）

    longData:BackTestItemData = None  #做多情况统计
    shortData:BackTestItemData = None #做空情况统计

    def __post_init__(self):
        self.longData = BackTestItemData()
        self.shortData = BackTestItemData()

    def getSellScore(self):
        return 100 * self.sell_ok / self.count

    def getBuyScore(self):
        return 100 * self.buy_ok / self.count



class CoreEngineRunner():

    def __init__(self,engine:CoreEngine):
        self.coreEngine:CoreEngine = engine
    """
    计算未来两天最有可能涨的股票SW指数。
    """
    def debugBestParam(self,  soruce: BarDataSource, strategy:CoreEngineStrategy, params:{},min_deal_count = -1, max_run_count = 999999999,printDetail = False):
        bars, code = soruce.nextBars()
        dataSet = {}
        totalCount = 0
        model = self.coreEngine.getEngineModel()
        while not bars is None:
            # self.coreEngine.getEngineModel().collectBars(bars,code)
            finished, stop = model.collectBars(bars, code)
            print(f"[backtest]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
            totalCount += len(finished)
            bars, code = soruce.nextBars()
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
                        order = self.__generatePredictOrder(self.coreEngine, predict)
                        __bars = [predict.collectData.occurBars[-1]] + predict.collectData.predictBars
                        self.__updateOrdres(strategy,order, __bars,__the_param);
                        self.putToStatistics(_testData, order, predict)

                    __dataList.append(_testData)
                    dimenSet[paramValue] = totalData
                    _paramTotalSet[paramValue].append(totalData)
        """
         for predict in predictList:
            order = self.__generatePredictOrder(self.coreEngine, predict)
            __bars = [predict.collectData.occurBars[-1]] + predict.collectData.predictBars
            self.__updateOrdres(strategy, order, __bars);
            self.putToStatistics(_testData, order, predict)
        __dataList[dimen] = _testData
        self.__PrintStatictis(__dataList, min_deal_count)

        """



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

    def backtest(self, soruce: BarDataSource, strategy:CoreEngineStrategy, min_deal_count = -1):
        bars, code = soruce.nextBars()
        dataSet = {}
        totalCount = 0
        model = self.coreEngine.getEngineModel()
        while not bars is None:
            #self.coreEngine.getEngineModel().collectBars(bars,code)
            finished, stop = model.collectBars(bars, code)
            print(f"[backtest]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
            totalCount += len(finished)
            bars, code = soruce.nextBars()
            for data in finished:
                ##收录
                listData: [] = dataSet.get(data.dimen)
                if listData is None:
                    listData = []
                    dataSet[data.dimen] = listData
                listData.append(data)

        __dataList = {}
        run_cnt = 0
        run_limit_size = len(dataSet)
        for dimen, listData in dataSet.items():
            if run_cnt >= run_limit_size:
                break
            model = self.coreEngine.loadPredictModel(dimen)
            if model is None:
                self.coreEngine.printLog(f"不支持的维度:{dimen}")
                continue
            run_cnt +=1
            self.coreEngine.printLog(f"开始回测维度:{dimen},进度:[{run_cnt}/{run_limit_size}]")
            predictList: Sequence['PredictData'] = model.predict(listData)
            _testData = BackTestData(dimen=dimen)
            _testData.abilityData = self.coreEngine.queryPredictAbilityData(dimen)
            _testData.quant = self.coreEngine.queryQuantData(dimen)

            for predict in predictList:
                order = self.__generatePredictOrder(self.coreEngine,predict)
                __bars = [predict.collectData.occurBars[-1]] +  predict.collectData.predictBars
                self.__updateOrdres(strategy,order,__bars);
                self.putToStatistics(_testData,order,predict)
            __dataList[dimen] = _testData

        self.__PrintStatictis(__dataList, min_deal_count)


    def __updateOrdres(self, strategy:CoreEngineStrategy,order,bars:[],debug_parms:{} = None,foce_close_order= True):
        if debug_parms is None:
            debug_parms = {}
        order.durationDay = -1
        todayOperaion = None
        for bar in bars:
            if order.status == PredictOrderStatus.ABANDON or \
                    order.status == PredictOrderStatus.SUC or \
                    order.status == PredictOrderStatus.FAIL:
                break
            oldStatus = order.status
            _oldType = order.type
            order.durationDay +=1
            last_today_bar = bar == bars[-1]
            operation = strategy.operatePredictOrder(self.coreEngine, order, bar, last_today_bar, debug_parms)
            if oldStatus != order.status or _oldType != order.type:
                raise RuntimeError("cant changed PredictOrder status or type！！")
            """
               处理操作单
               0: 不处理
               1：做多
               2：做空
               3: 预测成功交割单
               4：预测失败交割单
               5：废弃单              """
            if operation == 1 or operation == 2:
                assert order.type is None and  not order.buyPrice is None
                order.type = operation
                order.status = PredictOrderStatus.HOLD
            elif operation == 3 or operation == 4:
                assert not order.type is None and not order.sellPrice is None and not order.buyPrice is None and order.status == PredictOrderStatus.HOLD
                if operation == 3:
                    order.status = PredictOrderStatus.SUC
                else:
                    order.status = PredictOrderStatus.FAIL
            elif operation ==5:
                assert order.status == PredictOrderStatus.READY
                order.status = PredictOrderStatus.ABANDON
            else:
                assert operation == 0
            if last_today_bar:
                todayOperaion = operation
        ##强制清单
        if foce_close_order and order.status == PredictOrderStatus.HOLD:
            order.sellPrice = bars[-1].close_price
            order.status = PredictOrderStatus.FAIL
        # elif order.status == PredictOrderStatus.READY:
        #     order.status = PredictOrderStatus.ABANDON
        return todayOperaion
    def __generatePredictOrder(self, engine: CoreEngine, predict: PredictData) -> PredictOrder:
        code = predict.collectData.occurBars[-1].symbol
        crateDate = predict.collectData.occurBars[-1].datetime
        order = PredictOrder(dimen=predict.dimen, code=code, name=code,create_time=crateDate)
        predict_sell_pct = predict.getPredictSellPct(engine.getEngineModel())
        predict_buy_pct = predict.getPredictBuyPct(engine.getEngineModel())
        start_price = engine.getEngineModel().getYBasePrice(predict.collectData)
        order.suggestSellPrice = start_price * (1 + predict_sell_pct / 100)
        order.suggestBuyPrice = start_price * (1 + predict_buy_pct / 100)
        order.power_rate = engine.queryQuantData(predict.dimen).getPowerRate()
        order.predict = predict

        return order

    def __PrintStatictis(self, __dataList:{}, min_deal_count:int, debugy_param:[] = None):

        # def diemdata_cmp(v1, v2):
        #     return v1.getEarnRate() - v2.getEarnRate()
        # __dataList = sorted(__dataList, key=cmp_to_key(diemdata_cmp), reverse=True)
        # columns = ["dimen", "总数", "操作数", "盈利率", "总盈利", "总亏损", "分数|卖", "分数|买",
        #            "量化数据:", "power", "count", "sCPct", "bCPct", "预测能力:",
        #            "count", "sScore", "bScore","sBiasWin", "bBiasWin", "sBiasLoss","bBiasLoss"]
        values = []
        total = BackTestData(None)
        for dimen,d in __dataList.items():
            if (d.longData.deal_count + d.shortData.deal_count) < min_deal_count:
                continue
            total.count += d.count
            total.buy_ok +=d.buy_ok
            total.sell_ok += d.sell_ok
            d.longData.addTo(total.longData)
            d.shortData.addTo(total.shortData)
            self.coreEngine.printLog(f"[{dimen.value}]=>count:{d.count}(sScore:{utils.keep_3_float(d.getSellScore())},bScore:{utils.keep_3_float(d.getBuyScore())})," \
                       f"做多:[{d.longData.toStr(d.count)}]," \
                       f"做空:[{d.shortData.toStr(d.count)}]" )

        ##
        self.coreEngine.printLog("\n注意：预测得分高并一定代表操作成功率应该高，因为很多情况是先到最高点，再到最低点，有个顺序问题")
        self.coreEngine.printLog(f"回测总性能:count:{total.count}(sScore:{utils.keep_3_float(total.getSellScore())},bScore:{utils.keep_3_float(total.getBuyScore())})\n" \
                                 f"做多:[{total.longData.toStr(total.count)}]\n" \
                                 f"做空:[{total.shortData.toStr(total.count)}]")



    def putToStatistics(self, data:BackTestData, order:PredictOrder,predict:PredictData):
        assert  order.status!= PredictOrderStatus.HOLD
        data.count += 1
        high_price = -99999999
        low_price = -high_price
        for bar in predict.collectData.predictBars:
            high_price = max(high_price, bar.high_price)
            low_price = min(low_price, bar.low_price)
        sell_price = order.suggestSellPrice
        buy_price = order.suggestBuyPrice
        ## 预测价格有无到底最高价格
        sell_ok = high_price >= sell_price
        buy_ok = low_price <= buy_price
        if sell_ok:
            data.sell_ok += 1
        if buy_ok:
            data.buy_ok += 1

        ##预测成功并一定代表操作成功，因为很多情况是先到底最高点，再到底最低点，有个顺序问题

        hasDeal =  order.status == PredictOrderStatus.SUC  or order.status == PredictOrderStatus.FAIL
        if hasDeal:
            pct = 100 * (order.sellPrice - order.buyPrice) / order.buyPrice
            if order.type == 2:
                #做空
                data.shortData.deal_count +=1
                if order.status == PredictOrderStatus.SUC:
                    data.shortData.suc_count += 1
                if pct > 0.0:
                    data.shortData.earn_pct_total += pct
                    data.shortData.eran_count += 1
                    data.shortData.earn_pct_max = max(data.shortData.earn_pct_max, pct)
                else:
                    data.shortData.loss_pct_total += pct
                    data.shortData.loss_pct_max = min(data.shortData.loss_pct_max, pct)


            elif order.type == 1:
                #做多
                data.longData.deal_count += 1
                if order.status == PredictOrderStatus.SUC:
                    data.longData.suc_count += 1
                if pct > 0.0:
                    data.longData.earn_pct_total += pct
                    data.longData.eran_count += 1
                    data.longData.earn_pct_max = max(data.longData.earn_pct_max, pct)
                else:
                    data.longData.loss_pct_total += pct
                    data.longData.loss_pct_max = min(data.longData.loss_pct_max, pct)


    def __getFloatRangeInfo(self,ranges:['FloatRange'],encoder:FloatEncoder):
        return FloatRange.toStr(ranges,encoder)

    """"
    """
    def computeBuyPrice(self):

        return None

    ###中证500的数据
    def printZZ500Tops(self, strategy:CoreEngineStrategy,level = 1):
        today = datetime.now()
        end = utils.to_end_date(today - timedelta(days=1))
        start = end - timedelta(days=90)
        soruce = ZZ500DataSource(start, end)
        from earnmi.uitl.jqSdk import jqSdk
        todayBarsMap = jqSdk.fethcNowDailyBars(ZZ500DataSource.SZ500_JQ_CODE_LIST)
        bars, code = soruce.nextBars()
        dataSet = {}
        totalCount = 0
        latestDay = None
        model = self.coreEngine.getEngineModel()
        while not bars is None:
            if utils.is_same_day(bars[-1].datetime,today):
                del bars[-1]
            ##加上今天的数据
            todayBar =  todayBarsMap.get(code)
            if not todayBar is None and BarUtils.isOpen(todayBar):
                bars.append(todayBar)

            if latestDay is None or bars[-1].datetime > latestDay:
                latestDay = bars[-1].datetime
            finished, stop = model.collectBars(bars, code)
            print(f"[getTops]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
            totalCount += len(stop)
            bars, code = soruce.nextBars()
            for data in stop:
                ##收录
                listData: [] = dataSet.get(data.dimen)
                if listData is None:
                    listData = []
                    dataSet[data.dimen] = listData
                listData.append(data)
        if len(dataSet) < 1:
            self.coreEngine.printLog("当前没有出现特征数据！！")
        today_order_list = []
        done_order_list = []
        for dimen, listData in dataSet.items():
            model = self.coreEngine.loadPredictModel(dimen)
            if model is None:
                self.coreEngine.printLog(f"不支持的维度:{dimen}")
                continue
            self.coreEngine.printLog(f"开始实盘计算维度:{dimen}]")
            predictList: Sequence['PredictData'] = model.predict(listData)
            _testData = BackTestData(dimen=dimen)
            _testData.abilityData = self.coreEngine.queryPredictAbilityData(dimen)
            _testData.quant = self.coreEngine.queryQuantData(dimen)
            for predict in predictList:
                order = self.__generatePredictOrder(self.coreEngine,predict)
                __bars = [predict.collectData.occurBars[-1]] +  predict.collectData.predictBars
                todayOpration = self.__updateOrdres(strategy,order,__bars,foce_close_order=False);
                if not todayOpration is None:
                    order.todayOpration = todayOpration
                    today_order_list.append(order)
                else:
                    done_order_list.append(order)



        def order_cmp_by_time(o1, o2):
            if o1.create_time < o2.create_time:
                return -1
            if o1.create_time > o2.create_time:
                return 1
            return 0
        """
               0: 不处理
               1：做多
               2：做空
               3: 预测成功交割单
               4：预测失败交割单
               5：废弃单
        """
        def order_cmp_today(o1, o2):
            if o1.todayOpration == o2.todayOpration:
                return order_cmp_by_time(o1,o2)
            return o1.todayOpration - o2.todayOpration
        self.coreEngine.printLog(f"=========今天关注订单：{len(today_order_list)}个,date:{latestDay}")
        today_order_list = sorted(today_order_list, key=cmp_to_key(order_cmp_today), reverse=False)
        for order in today_order_list:
            desc = "unkonw"
            if order.todayOpration == 2:
                desc = "做空完成"
            if order.todayOpration == 1:
                desc = "买入完成"
            if order.todayOpration == 0:
                desc = "待关注"
                if order.durationDay == 1:
                    desc ="观望"
                if order.durationDay == 2:
                    desc ="下单买入"
                if order.durationDay > 2:
                    desc ="关注卖出"
            if order.todayOpration == 3:
                desc = "成功卖出"
            if order.todayOpration == 4:
                desc = "失败卖出"
            if order.todayOpration == 5:
                desc = "废弃单"

            self.coreEngine.printLog(f"【{desc}】{order.getStr()}")
            bar: BarData = todayBarsMap.get(order.code)
            if bar is None:
                info = f"    当前价格未知！"
            else:
                target_pct = utils.keep_3_float(100 * (order.suggestSellPrice - bar.close_price) / bar.close_price);
                buy_pct = utils.keep_3_float(100 * (bar.close_price - order.suggestBuyPrice) / bar.close_price);
                info = f"                   当前价格:{bar.close_price},离卖出:{target_pct}%,离买入:{buy_pct}%"
            self.coreEngine.printLog(info)

        self.coreEngine.printLog(f"=========已经结束订单：{len(done_order_list)}个")

        done_order_list = sorted(done_order_list, key=cmp_to_key(order_cmp_by_time), reverse=True)
        for order in done_order_list:
            self.coreEngine.printLog(f"[状态:{order.status}]{order.getStr()}")
            # bar:BarData = todayBarsMap.get(order.code)
            # if bar is None:
            #     info = f"    当前价格未知！"
            # else:
            #     target_pct = utils.keep_3_float(100*(order.suggestSellPrice - bar.close_price)/bar.close_price);
            #     buy_pct = utils.keep_3_float(100 * ( bar.close_price -order.suggestBuyPrice) / bar.close_price);
            #     info = f"    当前价格:{bar.close_price},离目标:{target_pct},买入目标:{buy_pct}%"
            # self.coreEngine.printLog(info)


        #return order_list;


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
            predict_sell_pct = predict.getPredictSellPct(engine.getEngineModel())
            predict_buy_pct = predict.getPredictBuyPct(engine.getEngineModel())
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