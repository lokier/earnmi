from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from ibapi.common import BarData

from earnmi.model.BarDataSource import BarDataSource
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineStrategy import CoreEngineStrategy
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder, PredictOrderStatus
from earnmi.model.op import *


@dataclass
class _OpOrderDataMap:
    order:OpOrder = None
    logs:[] = None
    def __post_init__(self):
        self.logs = []

class OpRunner(object):

    def __init__(self,order:PredictOrder,op_project:OpProject,db:OpDataBase,strategy:CoreEngineStrategy):
        self.op_project = op_project;
        self.strategy = strategy
        self.order = order
        self.db = db
        self.inited = None
        self.isOpenMarket = False
        self.opDataCache = _OpOrderDataMap()   ##为了性能，runner过程中把数据保存到cache里面，然后在init读取数据，在uninit保存数据。
        pass

    def isFinished(self):
        order = self.order
        if order.status == PredictOrderStatus.ABANDON or \
                order.status == PredictOrderStatus.SUC or \
                order.status == PredictOrderStatus.FAIL:
            return True
        return False

    def init(self, debug_parms:{} = None):
        assert self.inited == None
        self.inited =True
        init_log = self.strategy.onBeginOrder(self.order, debug_parms)
        op_order = self.__loadOpOrder(self.order)
        assert not op_order is None;
        history_logs = self.db.load_log_by_order_id(op_order.id)
        self.opDataCache.order = op_order
        self.opDataCache.logs.extend(history_logs)
        self.saveLog(init_log)

    """
    开始一天的交易
    """
    def openMarket(self, time:datetime,debug_parms:{} = None):
        assert self.inited
        assert self.isOpenMarket == False
        if self.isFinished():
            return False
        if (self.opDataCache.order.update_time - time).days > 0:
            ## 过滤历史bar时间。
            return False
        self.isOpenMarket = True
        opLog = self.strategy.onOpenTrade(self.order,debug_parms)
        self.saveLog(opLog)
        return True


    def update(self,bar:BarData,debug_parms:{} = None):
        assert self.inited
        assert self.isOpenMarket == True

        if self.opDataCache.order.update_time >= bar.datetime:
            ## 跳过已经更新的数据
            return

        order = self.order
        oldStatus = order.status
        _oldType = order.type

        opLog = self.strategy.onBar(order, bar, debug_parms)
        if oldStatus != order.status or _oldType != order.type:
            raise RuntimeError("cant changed PredictOrder status or type！！")
        if not opLog is None:
            operation = opLog.type
            if operation == OpLogType.BUY_LONG or operation ==  OpLogType.BUY_SHORT:
                assert order.type is None and not order.buyPrice is None
                order.type = operation
                order.status = PredictOrderStatus.HOLD
            elif operation == OpLogType.CROSS_SUCCESS or operation == OpLogType.CROSS_FAIL:
                assert not order.type is None and not order.sellPrice is None and not order.buyPrice is None and order.status == PredictOrderStatus.HOLD
                if operation == OpLogType.CROSS_SUCCESS:
                    order.status = PredictOrderStatus.SUC
                else:
                    order.status = PredictOrderStatus.FAIL
            elif operation == OpLogType.ABANDON:
                assert order.status == PredictOrderStatus.READY
                order.status = PredictOrderStatus.ABANDON
            else:
                assert operation == OpLogType.PLAIN
        order.update_time = bar.datetime
        if not opLog is None:
            self.saveLog(opLog)
        self.__updateOpOrder()


    def closeMarket(self, lastBar:BarData, debug_parms:{} = None):
        assert self.inited
        assert self.isOpenMarket == True
        self.isOpenMarket = False
        opLog = self.strategy.onEndTrade(self.order,lastBar, debug_parms)
        self.saveLog(opLog)

    def unInit(self, endBar:BarData,  debug_parms:{} = None):
        assert self.inited
        self.inited = False

        opLog = self.strategy.onEndOrder(self.order, endBar, debug_parms)
        self.saveLog(opLog)

        order = self.order
        if endBar:
            if order.status == PredictOrderStatus.HOLD:
                order.sellPrice = endBar.close_price
                order.status = PredictOrderStatus.FAIL
                cross_op_log = OpLog(type=OpLogType.CROSS_FAIL, info=f"超过持有天数限制，当天收盘价割单", time=endBar.datetime)
                self.saveLog(cross_op_log)
            elif order.status == PredictOrderStatus.READY:
                order.status = PredictOrderStatus.ABANDON
                cross_op_log = OpLog(type=OpLogType.CROSS_FAIL, info=f"超过持有天数限制,废弃", time=endBar.datetime)
                self.saveLog(cross_op_log)

        order.update_time = endBar.datetime
        self.__updateOpOrder()


        op_order = self.opDataCache.order
        buy_price, sell_price = self.load_order_sell_buy_price()

        print(f"final order: status:{op_order.status},buy:{buy_price},sell:{sell_price}")
        if op_order.status == OpOrderStatus.INVALID:
            assert buy_price is None and sell_price is None
        elif op_order.status == OpOrderStatus.HOLD:
            assert not buy_price is None and sell_price is None
        else:
            assert not buy_price is None and not sell_price is None

        ##保存所有的缓存后的数据。
        self.db.save_order(self.opDataCache.order)
        self.db.save_logs(self.opDataCache.logs)


    def __updateOpOrder(self):
        order = self.order
        time = order.update_time
        op_order = self.opDataCache.order
        assert time>= op_order.update_time
        # if time == op_order.update_time:
        #     return
        if (op_order.update_time - time).days < 0:
            op_order.duration +=1

        op_order.update_time = time

        if order.status == PredictOrderStatus.HOLD:
            op_order.status =  OpOrderStatus.HOLD
            real_buy_price, real_sell_price = self.load_order_sell_buy_price()
            assert not real_buy_price is None
            assert real_sell_price is None
        elif order.status == PredictOrderStatus.ABANDON:
            op_order.status = OpOrderStatus.INVALID
        elif order.status!= PredictOrderStatus.READY:
            real_buy_price, real_sell_price = self.load_order_sell_buy_price()
            assert not real_buy_price is None
            assert not real_sell_price is None
            assert order.status == PredictOrderStatus.SUC or order.status == PredictOrderStatus.FAIL
            if real_sell_price>= real_buy_price:
                op_order.status = OpOrderStatus.FINISHED_EARN
            else:
                op_order.status = OpOrderStatus.FINISHED_LOSS
            ###
            op_order.predict_suc = order.status == PredictOrderStatus.SUC
            op_order.sell_price_real = real_sell_price
            op_order.buy_price_real = real_buy_price


    def saveLog(self,log:OpLog):
        log.order_id = self.opDataCache.order.id
        log.project_id = self.op_project.id
        if log.type == OpLogType.BUY_LONG or log.type == OpLogType.BUY_SHORT:
            assert not self.order.buyPrice is None
            log.price = self.order.buyPrice
        elif log.type == OpLogType.CROSS_FAIL or log.type == OpLogType.CROSS_SUCCESS:
            log.price = self.order.sellPrice
        self.opDataCache.logs.append(log)
        print(f"save_log: {log.type},{log.info},price:{log.price}")

    def __loadOpOrder(self, order: PredictOrder) -> OpOrder:
        op_order = self.db.load_order_by_time(order.code, order.create_time)
        if op_order is None:
            op_order = OpOrder(code=order.code, code_name=order.code, project_id=self.op_project.id,
                               create_time=order.create_time
                               , buy_price=order.strategyBuyPrice, sell_price=order.strategySellPrice)
            op_order.op_name = f"dimen:{order.dimen}"
            op_order.duration = 0
            self.db.save_order(op_order)
            op_order = self.db.load_order_by_time(order.code, order.create_time)
            assert not op_order is None
        return op_order

    """
       返回order实际买入、卖出的价格。
       """

    def load_order_sell_buy_price(self):
        buy_price = None
        sell_price = None
        for log in self.opDataCache.logs:
            if log.type == OpLogType.BUY_SHORT or log.type == OpLogType.BUY_LONG:
                buy_price = log.price
            if log.type == OpLogType.CROSS_FAIL or log.type == OpLogType.CROSS_SUCCESS:
                sell_price = log.price
        return buy_price, sell_price



class ProjectRunner:

    def __init__(self, project: OpProject, opDB:OpDataBase,engine: CoreEngine):
        self.coreEngine: CoreEngine = engine
        self.project = project
        self.opDB = opDB
        assert not project.id is None
        self.opDB.save_projects([project])


    """
    level日志等级：
        0: verbse 
        100:debug 
        200：info   
        300:warn: 
        400 :error
    """
    def log(self, info: str, level: int = 100, type: int = OpLogType.PLAIN, time: datetime = None, price: float = 0.0):
        if time is None:
            time = datetime.now()
        log = OpLog(order_id= None)
        log.project_id = self.project.id
        log.type = type
        log.level = level
        log.time = time
        log.price = price
        log.info = info
        self.opDB.save_log(log)
        print(f"[runner|{time}]: {info}")


    def runBackTest(self, soruce: BarDataSource, strategy:CoreEngineStrategy):
        bars, code = soruce.nextBars()
        dataSet = {}
        totalCount = 0
        model = self.coreEngine.getEngineModel()
        while not bars is None:
            finished, stop = model.collectBars(bars, code)
            self.log(f"collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
            totalCount += len(finished)
            bars, code = soruce.nextBars()
            for data in finished:
                ##收录
                listData: [] = dataSet.get(data.dimen)
                if listData is None:
                    listData = []
                    dataSet[data.dimen] = listData
                listData.append(data)

        run_cnt = 0
        dataSetCount = len(dataSet)
        for dimen, listData in dataSet.items():
            if  not self.coreEngine.isSupport(dimen) or not strategy.isSupport(self.coreEngine, dimen):
                self.log(f"不支持的维度:{dimen}")
                continue
            model = self.coreEngine.loadPredictModel(dimen)
            if model is None:
                self.log(f"维度:{dimen}不含模型数据预测能力")
                continue
            run_cnt +=1
            self.log(f"开始回测维度:{dimen},进度:[{run_cnt}/{dataSetCount}]")
            self.__run_backtest(model,strategy,dimen,listData);

    def __run_backtest(self,model,strategy,dimen:Dimension,listData:Sequence['CollectData'],debug_parms:{} = None):
        predictList: Sequence['PredictData'] = model.predict(listData)
        run_cunt = 0

        for predict in predictList:
            run_cunt +=1
            print(f"{run_cunt}/{len(predictList)}")
            order = self.__generatePredictOrder(self.coreEngine, predict)
            runner = OpRunner(op_project=self.project,db = self.opDB, order= order,strategy = strategy)
            runner.init(debug_parms)
            if not runner.isFinished():
                lastBar = None
                for bar in predict.collectData.predictBars:
                    isOpen = runner.openMarket(bar.datetime,debug_parms)
                    if isOpen:
                        ##更新每天trick粒度以天，所以回测只有一次update

                        tickBars = [bar]
                        for tickBar in tickBars:
                            runner.update(tickBar,debug_parms)
                            if(runner.isFinished()):
                                break
                        runner.closeMarket(bar, debug_parms)
                        lastBar = bar
                runner.unInit(lastBar,debug_parms)
                assert runner.isFinished()



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

    def printDetail(self):

        op_order_list =  self.opDB.load_order_all(self.project.id)
        print(f"orderList : size = {len(op_order_list)}")
        op_orde_map_list = {}
        for order in op_order_list:
            dimenText = order.op_name
            order_list = op_orde_map_list.get(dimenText)
            if order_list is None:
                order_list = []
                op_orde_map_list[dimenText] = order_list
            order_list.append(order)

        for dimenText,order_list in op_orde_map_list.items():
            order_count = len(order_list)
            print(f"维度值:{dimenText} : size = {order_count}")

            dealCount = 0
            sucCount = 0
            earnCount = 0
            max_earn_rate = 0
            max_loss_rate = 0
            total_earn_rate = 0
            total_rate = 0
            for order in order_list:
                #assert order.status != OpOrderStatus.HOLD and order.status!=OpOrderStatus.NEW
                if order.predict_suc:
                    sucCount+=1
                if order.status == OpOrderStatus.FINISHED_EARN or order.status == OpOrderStatus.FINISHED_LOSS:
                    isEarn = order.status == OpOrderStatus.FINISHED_EARN
                    rate = (order.sell_price_real - order.buy_price_real)/order.buy_price_real
                    dealCount += 1
                    total_rate += rate
                    if isEarn:
                        earnCount+=1
                        total_earn_rate+=rate
                        max_earn_rate = max(max_earn_rate,rate)
                    else:
                        max_loss_rate = min(max_loss_rate,rate)

            print(f"[交易率:{self.toRateText(dealCount,order_count)}"
                  f"(盈利欺骗占XX.XX%),"
                  f"成功率:{self.toRateText(sucCount,dealCount)},"
                  f"盈利率:{self.toRateText(earnCount,dealCount)},"
                  f"单均pct:{self.keep2Foat(self.divide(100*total_rate,dealCount))},"
                  f"盈pct:{self.keep2Foat(self.divide(100*total_earn_rate,earnCount))}({self.keep2Foat(100*max_earn_rate)}),"
                  f"亏pct:{self.keep2Foat(self.divide(100* (total_rate - total_earn_rate),dealCount - earnCount))}({self.keep2Foat(100*max_loss_rate)})]")
            """
[99]=>count:15(sScore:93.333,bScore:53.333),做多:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)],做空:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[100]=>count:39(sScore:76.923,bScore:66.666),做多:[交易率:38.46%(盈利欺骗占6.67%),成功率:13.33%,盈利率:33.33%,单均pct:-0.40,盈pct:2.93(6.00),亏pct:-2.07(-7.21)],做空:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[58]=>count:10(sScore:80.0,bScore:60.0),做多:[交易率:40.00%(盈利欺骗占25.00%),成功率:75.00%,盈利率:75.00%,单均pct:1.24,盈pct:1.67(1.69),亏pct:-0.07(-0.07)],做空:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[94]=>count:10(sScore:70.0,bScore:80.0),做多:[交易率:50.00%(盈利欺骗占0.00%),成功率:60.00%,盈利率:60.00%,单均pct:0.93,盈pct:2.94(3.51),亏pct:-2.09(-3.97)],做空:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
          """

        pass
    def keep2Foat(self,v:float):
        return f"%.2f" % (v)

    def divide(self,f1:float,f2:float):
        if f2 < 0.0001:
            return 0.0
        return f1/f2

    def toRateText(self,f1:float,f2:float)->str:
        if f2 <0.00001:
            return "0%"
        return f"%.2f%%" % (100*f1/f2)

if __name__ == "__main__":
    pass

