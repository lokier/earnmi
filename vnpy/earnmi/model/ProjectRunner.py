import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence
from earnmi.model.BarDataSource import BarDataSource, ZZ500DataSource
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictData import PredictData
from earnmi.model.bar import LatestBarDB, LatestBar
from earnmi.model.op import *
from earnmi.uitl.BarUtils import BarUtils
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData


class OpStrategy:
    def __init__(self):
        self.buy_day_max = 2  ## 设定买入交易的最大交易天数（将在这个交易日完成买入）
        self.max_day = 3  ##表示该策略的最大考虑天数，超过这个天数如果还没完成交割工作将强制割仓（类似止损止盈）
        self.buy_offset_pct = None #调整买入价格，3表示高于3%的价格买入，-3表示低于3%的价格买入 None表示没有限制。
        self.sell_offset_pct = None #调整买入价格，3表示高于3%的价格买入，-3表示低于3%的价格买入 None表示没有限制。
        self.sell_leve_pct_top = None  # sell_leve_pct的范围None表示没有限制
        self.sell_leve_pct_bottom = None
        self.buy_leve_pct_top = None  #buy_leve_pct的范围None表示没有限制
        self.buy_leve_pct_bottom = None

    def getName(self):
        return "CommonStrategy"

    def getParams(self,dimen_value:int):
        return None

    def initPrams(self,dimen: Dimension,debugParams: {}):
        if debugParams is None:
            debugParams = self.getParams(dimen.value)
        if debugParams is None:
            debugParams = {}
        if debugParams.__contains__('buy_day_max'):
            self.buy_day_max = debugParams['buy_day_max']
        if debugParams.__contains__('max_day'):
            self.max_day = debugParams['max_day']
        if debugParams.__contains__('buy_offset_pct'):
            self.buy_offset_pct = debugParams['buy_offset_pct']
        if debugParams.__contains__('sell_offset_pct'):
            self.sell_offset_pct = debugParams['sell_offset_pct']

        if debugParams.__contains__('sell_leve_pct_top'):
            self.sell_leve_pct_top = debugParams['sell_leve_pct_top']
        if debugParams.__contains__('sell_leve_pct_bottom'):
            self.sell_leve_pct_bottom = debugParams['sell_leve_pct_bottom']

        if debugParams.__contains__('buy_leve_pct_top'):
            self.buy_leve_pct_top = debugParams['buy_leve_pct_top']
        if debugParams.__contains__('buy_leve_pct_bottom'):
            self.buy_leve_pct_bottom = debugParams['buy_leve_pct_bottom']
        pass

    def isSupport(self, dimen: Dimension) -> bool:
        return True

    def makeOpOrder(self,engine:CoreEngine,project:OpProject,predict:PredictData,soruce = 0,params: {} = None)->OpOrder:
        code = predict.collectData.occurBars[-1].symbol
        crateDate = predict.collectData.occurBars[-1].datetime
        predict_sell_pct = predict.getPredictSellPct(engine.getEngineModel())
        predict_buy_pct = predict.getPredictBuyPct(engine.getEngineModel())
        start_price = engine.getEngineModel().getYBasePrice(predict.collectData)

        suggestSellPrice = start_price * (1 + predict_sell_pct / 100)
        suggestBuyPrice = start_price * (1 + predict_buy_pct / 100)
        self.initPrams(predict.dimen, params)
        ##根据参数调整买入、卖出价
        ##调整卖出价
        if not self.sell_offset_pct is None:
            selff_offset = self.sell_offset_pct / 100
            suggestSellPrice = suggestSellPrice * (1 + selff_offset)
        ##调整买入价
        if not self.buy_offset_pct is None:
            buy_offset = self.buy_offset_pct / 100
            suggestBuyPrice = suggestBuyPrice * (1 + buy_offset)
        if not self.buy_leve_pct_top is None or not self.buy_leve_pct_bottom is None:
            raise RuntimeError("暂未支持")

        op_order = OpOrder(code=code, code_name=code, project_id=project.id,
                           create_time=crateDate
                           , buy_price=suggestBuyPrice, sell_price=suggestSellPrice)
        op_order.dimen = f"{predict.dimen.value}"
        op_order.duration = 0
        op_order.source = soruce

        return op_order

    def onRestoreOrder(self, order: OpOrder)->OpLog:
        return OpLog(info=f"恢复order环境: project_id:{order.project_id},order_id:{order.id},code:{order.code}")

    def onSaveOrder(self, order: OpOrder)->OpLog:
        return OpLog(info=f"保存order环境: project_id:{order.project_id},order_id:{order.id},code:{order.code}")

    """准备开始一天的交易"""
    def onMarketOpen(self, order: OpOrder, params: {} = None)->OpLog:
        return OpLog(info=f"  开盘, code:{order.code}")

    def onMarketClose(self, order: OpOrder, bar: BarData, params: {} = None)->OpLog:
        return OpLog(info=f"  收盘, code:{order.code}")

    def onBar(self, order: OpOrder, data:PredictData, bar: BarData, params: {} = None) -> OpLog:
        self.initPrams(data.dimen, params)
        ocurrBar_close_price = data.collectData.occurBars[-1].close_price
        sell_leve_pct = 100 * (order.sell_price - ocurrBar_close_price) / ocurrBar_close_price
        if not self.sell_leve_pct_top is None and sell_leve_pct > self.sell_leve_pct_top:
            return OpLog(type=OpLogType.ABANDON,info = "当天走势不满足策略要求，废弃该操作单")
        if not self.sell_leve_pct_bottom is None and sell_leve_pct < self.sell_leve_pct_bottom:
            return OpLog(type=OpLogType.ABANDON,info = "当天走势不满足策略要求，废弃该操作单")
        suggestSellPrice = order.sell_price
        suggestBuyPrice = order.buy_price

        if (order.status == OpOrderStatus.HOLD):
            if bar.high_price >= suggestSellPrice:
                return OpLog(type=OpLogType.CROSS_SUCCESS,price=suggestSellPrice, info=f"成功到达卖出价，操作单按预测成功完成！")

            willClose = bar.datetime.hour >=14 and bar.datetime.minute >=40
            if willClose and order.duration >= self.max_day:
                return OpLog(type=OpLogType.CROSS_FAIL,price=bar.close_price, info=f"超过持有天数限制并强制减盈（减损），操作单未按预测成功！")
            order.isOverClosePct = 100 * (bar.close_price - suggestBuyPrice) / suggestBuyPrice  ##低价买入，是否想预期走势走高。
        elif order.status == OpOrderStatus.NEW:
            if order.duration > self.buy_day_max:
                # 超过买入交易时间天数，废弃
                return OpLog(type=OpLogType.ABANDON, info=f"超过考虑买入交易天数:{self.buy_day_max}")
            ##这天观察走势,且当天high_price 不能超过预测卖出价
            # 这里有个坑，
            # 1、如果当天是超过卖出价之后再跌到买入价，  这时第二天就要考虑止损
            # 2、如果是到底买入价之后的当天马上涨到卖出价，这时第二天就要考虑止盈
            # 不管是那种情况，反正第二天就卖出。
            if suggestBuyPrice >= bar.low_price:
                ##当天是否盈利欺骗
                order.isWinCheatBuy = bar.high_price >= suggestSellPrice
                ##趋势形成的第二天买入。
                return OpLog(type=OpLogType.BUY_LONG,price=suggestBuyPrice , info=f"成功到达最低价买入！！！，当天是否有超过卖出价:{order.isWinCheatBuy}")
        return None

class TradeRunner:

    """
    (启动程序，或者在第二天一早执行）
    """
    def onLoad(self):
        pass

    """
    准备开盘。
    """
    def onOpen(self):
        pass
    """
      股票开市时执行。 返回下一次执行时间。单位秒，或者默认一分钟。
    """
    def onTrick(self):
        pass
    """
    当天收盘
    """
    def onClose(self):
        pass

class OpRunner(object):

    def __init__(self,op_project:OpProject,predictData:PredictData,db:OpDataBase,order:OpOrder,strategy:OpStrategy):
        self.op_project = op_project;
        self.strategy:OpStrategy = strategy
        self.__order = order
        self.__opLogs= []
        self.marketTime = None  ##市场时间
        self.db = db
        self.predictData = predictData
        self.buyTime = None
        assert not order is None

    def getOrder(self)->OpOrder:
        return self.__order

    """
        恢复运行环境
    """
    def restore(self):
        op_order = self.__order
        db_op_order = self.db.load_order_by_time(self.op_project.id,op_order.code, op_order.create_time)
        if db_op_order is None:
            ##说明使用的未保存的op_order，先保存获取到order_id
            self.db.save_order(op_order)
            op_order = self.db.load_order_by_time(self.op_project.id,op_order.code, op_order.create_time)
            assert not op_order is None
            self.__order = op_order
            self.__opLogs =[]
        else:
            self.__order = db_op_order
            self.__opLogs = self.db.load_logs(self.op_project.id,self.__order.id)
        assert not self.__order.id is None
        self.__order_backup = copy.copy(self.__order)
        resotre_log = self.strategy.onRestoreOrder(self.__order)
        self.saveLog(resotre_log)

    """
     有变动时保存数据。
    """
    def saveIfChagned(self):
        assert not self.__order_backup is None
        if self.__order_backup!=self.__order:
            self.save()
        else:
            print(f"   skip save : because no chagned!!")

    def save(self):
        ##保存所有的缓存后的数据。
        save_log = self.strategy.onSaveOrder(self.__order)
        self.saveLog(save_log)
        self.db.save_order(self.__order)
        self.db.save_logs(self.__opLogs)


    def isFinished(self):
        order = self.__order
        if order.status == OpOrderStatus.INVALID or \
                order.status == OpOrderStatus.FINISHED_EARN or \
                order.status == OpOrderStatus.FINISHED_LOSS:
            return True
        return False

    """
    今天是否可以交易
    """
    def canMarketToday(self):
        if not self.buyTime is None:
            return not utils.is_same_day(self.buyTime,self.marketTime)
        return True

    """
    开始一天的交易
    """
    def openMarket(self, time:datetime,debug_parms:{} = None):
        self.marketTime = time

        if self.isFinished():
            return False

        if self.__order.update_time >= time:
            return False

        opLog = self.strategy.onMarketOpen(self.__order,debug_parms)
        opLog.time = time
        self.saveLog(opLog)
        self.__updateOrderTime(time)
        return True


    def update(self,bar:BarData,debug_parms:{} = None)->bool:
        self.marketTime = bar.datetime
        if not self.canMarketToday() or self.__order.update_time >= bar.datetime:
            ## 跳过已经更新的数据
            return False

        order = self.__order
        order.current_price = bar.close_price
        oldStatus = order.status
        self.__updateTradeTime(bar.datetime)
        self.__updateOrderTime(bar.datetime)

        if not BarUtils.isOpen(bar):
            return True

        opLog = self.strategy.onBar(order,self.predictData, bar, debug_parms)
        if not order.predict_suc:
            order.predict_suc = bar.high_price >= order.sell_price
        if not opLog is None:
            opLog.time = bar.datetime
            self.saveLog(opLog)
            operation = opLog.type
            newStatus = None
            if operation == OpLogType.BUY_LONG or operation ==  OpLogType.BUY_SHORT:
                assert oldStatus == OpOrderStatus.NEW
                newStatus = OpOrderStatus.HOLD
            elif operation == OpLogType.CROSS_SUCCESS or operation == OpLogType.CROSS_FAIL:
                assert oldStatus == OpOrderStatus.HOLD
                newStatus = self.corssOrder()
            elif operation == OpLogType.ABANDON:
                assert oldStatus == OpOrderStatus.NEW
                newStatus = OpOrderStatus.INVALID
            else:
                assert operation == OpLogType.PLAIN
            if not newStatus is None:
                self.__updateOpOrder(newStatus)
        return True

    def corssOrder(self):
        order = self.__order
        real_buy_price, real_sell_price = self.load_order_sell_buy_price()
        assert not real_buy_price is None
        assert not real_sell_price is None
        cross_status = OpOrderStatus.FINISHED_LOSS
        if real_sell_price >= real_buy_price:
            cross_status = OpOrderStatus.FINISHED_EARN
        ###
        order.sell_price_real = real_sell_price
        order.buy_price_real = real_buy_price
        return cross_status

    def __updateOrderTime(self,time:datetime):
        assert self.__order.update_time <= time
        if self.__order.update_time < time:
            self.__order.update_time = time

    def __updateTradeTime(self,time:datetime):
        if self.__order.current_trade_time is None:
            self.__order.current_trade_time = time
            self.__order.duration =1
            return
        assert self.__order.current_trade_time <= time
        if self.__order.current_trade_time < time:
            if not utils.is_same_day(self.__order.current_trade_time,time):
                self.__order.duration +=1
            self.__order.current_trade_time = time


    def __updateOpOrder(self,newStatus:int):
        order = self.__order
        oldStatus = order.status
        order.status = newStatus
        if order.status == OpOrderStatus.HOLD:
            real_buy_price, real_sell_price = self.load_order_sell_buy_price()
            assert not real_buy_price is None
            assert real_sell_price is None
            order.buy_price_real = real_buy_price


    def closeMarket(self, lastBar:BarData, debug_parms:{} = None):
        self.marketTime = lastBar.datetime
        if self.__order.update_time >= lastBar.datetime:
            ##旧数据跳过
            return
        opLog = self.strategy.onMarketClose(self.__order,lastBar, debug_parms)
        opLog.time = lastBar.datetime
        self.saveLog(opLog)
        self.__updateOrderTime(lastBar.datetime)

    """
    强制运行结束。一般在回撤环境。
    """
    def foreFinish(self, close_price:float, debug_parms:{} = None):
        order = self.__order
        if order.status == OpOrderStatus.HOLD:
            cross_op_log = OpLog(type=OpLogType.CROSS_FAIL, info=f"ForeFinish:超过持有天数限制，当天收盘价割单", time=order.update_time,price=close_price)
            self.saveLog(cross_op_log)
            newStatus = self.corssOrder()
            self.__updateOpOrder(newStatus)
        elif order.status == OpOrderStatus.NEW:
            cross_op_log = OpLog(type=OpLogType.ABANDON, info=f"ForeFinish:超过持有天数限制,废弃", time=order.update_time)
            self.saveLog(cross_op_log)
            self.__updateOpOrder(OpOrderStatus.INVALID)


    def saveLog(self,log:OpLog):
        if log is None:
            return
        log.order_id = self.__order.id
        log.project_id = self.op_project.id
        if log.type == OpLogType.BUY_LONG or log.type == OpLogType.BUY_SHORT:
            assert not log.price is None
            self.buyTime = log.time
        elif log.type == OpLogType.CROSS_FAIL or log.type == OpLogType.CROSS_SUCCESS:
            assert not log.price is None
        self.__opLogs.append(log)
        print(f"save_log: {log.type},{log.info},price:{log.price}")

    def log(self, info: str, level: int = 100, type: int = OpLogType.PLAIN, time: datetime = None, price: float = 0.0):
        if time is None:
            time = datetime.now()
        log = OpLog(order_id=self.__order.id)
        log.type = type
        log.level = level
        log.time = time
        log.price = price
        log.info = info
        self.saveLog(log)
    """
       返回order实际买入、卖出的价格。
       """
    def load_order_sell_buy_price(self):
        buy_price = None
        sell_price = None
        for log in self.__opLogs:
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


    def runBackTest(self, soruce: BarDataSource, strategy:OpStrategy):
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
            if  not self.coreEngine.isSupport(dimen) or not strategy.isSupport(dimen):
                self.log(f"不支持的维度:{dimen}")
                continue
            model = self.coreEngine.loadPredictModel(dimen)
            if model is None:
                self.log(f"维度:{dimen}不含模型数据预测能力")
                continue
            run_cnt +=1
            self.log(f"开始回测维度:{dimen},进度:[{run_cnt}/{dataSetCount}]")
            predictList: Sequence['PredictData'] = model.predict(listData)
            run_cunt = 0
            for predict in predictList:
                run_cunt += 1
                print(f"{run_cunt}/{len(predictList)}")
                runner = self._loadRunner(strategy, predict, foreceClose=True, debug_parms=None)
                if runner is None:
                    continue
                ###回测环境每次runner都完成。
                assert runner.isFinished()

    """
    加载Runner。
    多次加载，需要去除加载操作。
    """
    def _loadRunner(self, strategy, predict:PredictData, foreceClose=False, debug_parms:{} = None)->OpRunner:
        ##根据预测数据创建一个操作订单
        order = strategy.makeOpOrder(self.coreEngine, self.project, predict, 1,
                                     debug_parms)  ##self.__generatePredictOrder(self.coreEngine, predict)
        if order is None:
            print(f"makeOpOrder 为null")
            return None
        runner = OpRunner(op_project=self.project, predictData=predict, db=self.opDB, order=order, strategy=strategy)
        # 回复运行环境
        runner.restore();
        order = runner.getOrder()
        if runner.isFinished():
            print(f"   skip save : runner is already finished!!!!")
            return runner

        lastBar: BarData = None
        for bar in predict.collectData.predictBars:
            lastBar = bar
            if runner.isFinished():
                break
            ##开市
            bar.datetime = utils.changeTime(bar.datetime,hour=9,minute=30,second=0)
            canContinue = runner.openMarket(bar.datetime, debug_parms)
            if not canContinue:
                ##历史数据跳过
                continue
            if runner.isFinished():
                break;
            ##更新每天trick粒度以天，所以回测只有一次update
            tickBars = [bar]
            bar.datetime = utils.changeTime(bar.datetime,hour=14,minute=57,second=0)
            for tickBar in tickBars:
                runner.update(tickBar, debug_parms)
                if (runner.isFinished() or not runner.canMarketToday()):
                    break
            bar.datetime = utils.changeTime(bar.datetime,hour=15,minute=00,second=0)
            runner.closeMarket(bar, debug_parms)
        if foreceClose:
            runner.foreFinish(lastBar.close_price, debug_parms)
        runner.saveIfChagned()
        return runner

    def loadZZ500NowRunner(self,latestDB:LatestBarDB,strategy:OpStrategy)->TradeRunner:
        engine = self.coreEngine
        project_runner = self
        latestDB = latestDB
        class MyRunner(TradeRunner):
            """
            (启动程序，或者在第二天一早执行）
            """
            def onLoad(self):
                today = datetime.now()
                end = utils.to_end_date(today - timedelta(days=1))
                start = end - timedelta(days=90)
                project_runner.log(f"load history barData, start:{start},end:{end}")
                soruce = ZZ500DataSource(start, end)
                bars, code = soruce.nextBars()
                model = engine.getEngineModel()
                dataSet = {}
                while not bars is None:
                    finished, stop = model.collectBars(bars, code)
                    project_runner.log(
                        f"[getTops]: collect code:{code}, finished:{len(finished)},stop:{len(stop)},last date: {bars[-1].datetime},volume={bars[-1].volume}")
                    bars, code = soruce.nextBars()
                    all_data_list = list(finished) + list(stop)
                    for data in all_data_list:
                        listData: [] = dataSet.get(data.dimen)
                        if listData is None:
                            listData = []
                            dataSet[data.dimen] = listData
                        listData.append(data)
                if len(dataSet) < 1:
                    project_runner.log("当前没有出现特征数据！！")

                ##计算那些未完成的order
                unfinished_runners = []
                for dimen, listData in dataSet.items():
                    if not strategy.isSupport(dimen):
                        continue
                    model = engine.loadPredictModel(dimen)
                    if model is None:
                        project_runner.log(f"不支持的维度:{dimen}")
                        continue
                    project_runner.log(f"开始实盘计算维度:{dimen}]")
                    predictList: Sequence['PredictData'] = model.predict(listData)
                    for predict in predictList:
                        ##产生一个预测单,
                        runner = project_runner._loadRunner(strategy, predict, foreceClose=False, debug_parms=None)
                        if runner is None:
                            continue
                        if not runner.isFinished():
                            unfinished_runners.append(runner)
                self.unfinished_runners = unfinished_runners;
                project_runner.log(f"load historyfinished！！")
            """
            准备开盘。
            """
            def onOpen(self):
                for runner in self.unfinished_runners:
                    runner.log("开盘")
                    runner.save()
            """
              股票开市时执行。 返回下一次执行时间。单位秒，或者默认一分钟。
            """
            def onTrick(self):
                ###更新当前股票价格。
                runner_size = len(self.unfinished_runners)

                ##获取今天的实时信息。
                todayBarsMap= latestDB.load(ZZ500DataSource.SZ500_JQ_CODE_LIST)

                to_delete_runners = []
                ####更新实时价格
                for runner in self.unfinished_runners:
                    code = runner.getOrder().code
                    bar: LatestBar = todayBarsMap.get(code)
                    if bar is None:
                        project_runner.log(info="获取{code}的bar信息失败！！", level=OpLogLevel.WARN)
                        continue
                    is_updated = runner.update(bar.toBarData(), None)
                    if is_updated:
                        runner.save()
                    if (runner.isFinished() or not runner.canMarketToday()):
                        to_delete_runners.append(runner)
                        break
                project_runner.log(f" [onTrick]: update_size = {runner_size},finished_size = {len(to_delete_runners)}")
                for to_delete in to_delete_runners:
                    self.unfinished_runners.remove(to_delete)

            """
            当天收盘
            """
            def onClose(self):
                for runner in self.unfinished_runners:
                    runner.log("收盘")
                    runner.save()
        return MyRunner()


    def printDetail(self):

        op_order_list =  self.opDB.load_order_all(self.project.id)
        print(f"orderList : size = {len(op_order_list)}")
        op_orde_map_list = {}
        for order in op_order_list:
            dimenText = order.dimen
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

                if order.status == OpOrderStatus.FINISHED_EARN or order.status == OpOrderStatus.FINISHED_LOSS:
                    if order.predict_suc:
                        sucCount += 1
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

