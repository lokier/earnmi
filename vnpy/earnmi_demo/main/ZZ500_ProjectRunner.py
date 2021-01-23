from collections import Sequence
from datetime import datetime,timedelta
from earnmi.core.Runner import Runner, RunnerScheduler
from earnmi.data.BarManager import BarManager
from earnmi.data.BarMarket import BarMarket
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver
from earnmi.model.BarDataSource import BarDataSource, ZZ500DataSource
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.DataSource import DatabaseSource
from earnmi.model.PredictData import PredictData
from earnmi.model.ProjectRunner import OpStrategy, OpProject, OpDataBase, OpRunner
from earnmi.model.bar import LatestBar
from earnmi.model.op import OpStatistic, OpOrderStatus, OpLogLevel
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData

"""
订单型操作策略。
"""
class ZZ500_ProjectRunner(Runner):

    def __init__(self,name:str,project:OpProject,source: DatabaseSource, strategy:OpStrategy,engine:CoreEngine):
        super().__init__()
        self.source:DatabaseSource = source
        self.strategy:OpStrategy = strategy
        self.project:OpProject = project
        self.name = name
        self.coreEngine = engine ##模型引擎
        self.unfinished_runners = []


    def getName(self):
        return self.name

    def onStart(self, scheduler: RunnerScheduler):
        ##创建一个行情市场
        self.context.log_i("onStart")
        index_driver = StockIndexDriver()  ##A股指数驱动
        drvier2 = ZZ500StockDriver()  ##中证500股票池驱动
        barManager:BarManager = BarManager.get(self.context)
        self.market:BarMarket = barManager.createBarMarket(index_driver,[drvier2])

        ##下载行情数据。


        scheduler.run_weekly("1-5","9:01:30",self._on_prepare_open_at_9_01,{},run_if_miss_time=True)
        is_backtest = self.context.is_backtest()
        if is_backtest:
            scheduler.run_weekly("1-5", "14:55:30", self._onUpdateOrdersWhileOpern, {}, run_if_miss_time=False)

    def _on_prepare_open_at_9_01(self):
        """
        开盘前做一下初始化化工作。
        """
        self.unfinished_runners = []
        self.generateTodayOpOrderLists()

    def _onUpdateOrdersWhileOpern(self):
        """
        更新操作单的状态。
        """
        ###更新当前股票价格。
        runner_size = len(self.unfinished_runners)
        ##获取今天的实时信息。

        code_list = []
        __code_map = {}
        for runner in self.unfinished_runners:
            code = runner.getOrder().code
            index = code.find(".")
            symbol = code[:index]
            code_list.append(symbol)
            __code_map[symbol] = code

        _latest_bar_map = self.market.get_latest_bar(code_list)

        todayBarsMap = {}
        for symbol,l_bar in _latest_bar_map.items():
            todayBarsMap[__code_map[symbol]] = l_bar

        to_delete_runners = []
        ####更新实时价格
        for runner in self.unfinished_runners:
            code = runner.getOrder().code
            bar: LatestBar = todayBarsMap.get(code)
            if bar is None:
                self.context.log_w(f"获取{code}的bar信息失败！！")
                continue
            is_updated = runner.update(bar.toBarData(), None)
            if is_updated:
                runner.save()
            if (runner.isFinished() or not runner.canMarketToday()):
                to_delete_runners.append(runner)
                break
        self.context.log_i(f" [onTrick]: update_size = {runner_size},finished_size = {len(to_delete_runners)}")
        for to_delete in to_delete_runners:
            self.unfinished_runners.remove(to_delete)



    def generateTodayOpOrderLists(self):
        """
        生成今天的操作单。
        """
        strategy = self.strategy
        engine = self.coreEngine
        db = self.source.createDatabase()
        opDB = OpDataBase(db)
        today = self.now()
        end = utils.to_end_date(today - timedelta(days=1))
        start = end - timedelta(days=90)
        self.log(f"generateTodayOpOrderLists():{start},end:{end}")
        soruce = ZZ500DataSource(start, end)
        dataSet = self.initCollectData(soruce, exclueUnFinihsedData=False)
        ##计算那些未完成的order
        unfinished_runners = []
        saveOrderCount = 0
        for dimen, listData in dataSet.items():
            if not strategy.isSupport(dimen):
                continue
            model = engine.loadPredictModel(dimen)
            if model is None:
                self.log(f"不支持的维度:{dimen}")
                continue
            self.log(f"开始实盘计算维度:{dimen}]")
            predictList: Sequence['PredictData'] = model.predict(listData)
            for predict in predictList:
                ##产生一个预测单,
                runner = self._loadRunner(opDB,strategy, predict, debug_parms=None)
                if runner is None:
                    continue
                if runner.isSave:
                    saveOrderCount += 1
                if predict.collectData.isFinished():
                    assert runner.isFinished()
                if not runner.isFinished():
                    unfinished_runners.append(runner)
        self.unfinished_runners = unfinished_runners;
        self.log(
            f"generateTodayOpOrderLists():finished, unfishedSize = {len(self.unfinished_runners)},  save = {saveOrderCount}")
        self.updateStatisitcs(opDB)  ##更新统计数据。
        opDB.close();


    def _loadRunner(self, opDB:OpDataBase,strategy, predict:PredictData, debug_parms:{} = None)->OpRunner:
        ##根据预测数据创建一个操作订单
        order = strategy.makeOpOrder(self.coreEngine, self.project, predict, 1,
                                     debug_parms)  ##self.__generatePredictOrder(self.coreEngine, predict)
        if order is None:
            print(f"makeOpOrder 为null")
            return None
        runner = OpRunner(op_project=self.project, predictData=predict, db=opDB, order=order, strategy=strategy)
        # 回复运行环境
        runner.restore();
        order = runner.getOrder()
        if runner.isFinished():
            ##print(f"   skip save : runner is already finished!!!!")
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
        foreceClose = predict.collectData.isFinished()
        if foreceClose:
            runner.foreFinish(lastBar.close_price, debug_parms)
        assert runner.isSave == False
        runner.saveIfChagned()
        return runner



    def initCollectData(self, soruce: BarDataSource, exclueUnFinihsedData:bool = True):
        model = self.coreEngine.getEngineModel()
        bars, code = soruce.nextBars()
        dataSet = {}
        finishedTotalCount = 0
        unfinishedTotalCount = 0
        self.log(f" initCollectData(): start")
        while not bars is None:
            finished, stop = model.collectBars(bars, code)
            _finished_size = len(finished)
            _unfinished_size = len(stop)
            ##self.log(f"    collect code:{code}, finished:{_finished_size},unfinished:{_unfinished_size}, last date: {bars[-1].datetime},volume={bars[-1].volume}")
            finishedTotalCount += _finished_size
            unfinishedTotalCount += _unfinished_size
            for data in finished:
                listData: [] = dataSet.get(data.dimen)
                if listData is None:
                    listData = []
                    dataSet[data.dimen] = listData
                listData.append(data)
            if not exclueUnFinihsedData:
                for data in stop:
                    listData: [] = dataSet.get(data.dimen)
                    if listData is None:
                        listData = []
                        dataSet[data.dimen] = listData
                    listData.append(data)
            bars, code = soruce.nextBars()
        self.log(f"initCollectData(): finished, finished:{finishedTotalCount},unfinished:{unfinishedTotalCount}")
        return dataSet

    def updateStatisitcs(self, opDB:OpDataBase):
        ###dt = datetime - timedelta(days=60)
        ##主键，0: 最近1个月，1：最近3个月，2: 最近6个月，3：最近1年
        typeDayMap = {}
        typeDayMap[1] = 30
        typeDayMap[2] = 91
        typeDayMap[3] = 183
        typeDayMap[4] = 365
        now = self.now()
        data_list = []
        for type,days in typeDayMap.items():
            start_time = now - timedelta(days=days)
            order_list  = opDB.load_order_all(self.project.id,finishOrder=True,start_time=start_time)
            statistic = self.makeStatistic(order_list,startTime = now)
            statistic.type = type
            data_list.append(statistic)

        opDB.save_statistices(data_list)

    """
       生成统计数据。
    """
    def makeStatistic(self, order_list: ['OpStatistic'], startTime=None) -> OpStatistic:
        statistic = OpStatistic(start_time=startTime, project_id=self.project.id)
        if len(order_list) == 0:
            return statistic

        statistic.count = len(order_list)
        for order in order_list:
            if not statistic.start_time is None:
                if statistic.start_time > order.create_time:
                    statistic.start_time = order.create_time
            if order.predict_suc:
                statistic.predict_suc_count += 1
            if order.status == OpOrderStatus.FINISHED_EARN or order.status == OpOrderStatus.FINISHED_LOSS:
                if order.predict_suc:
                    statistic.predict_suc_deal_count += 1
                isEarn = order.status == OpOrderStatus.FINISHED_EARN
                rate = (order.sell_price_real - order.buy_price_real) / order.buy_price_real
                statistic.dealCount += 1
                statistic.totalPct += rate
                if isEarn:
                    statistic.earnCount += 1
                    statistic.totalEarnPct += rate
                    statistic.maxEarnPct = max(statistic.maxEarnPct, rate)
                else:
                    statistic.maxLossPct = min(statistic.maxLossPct, rate)

        return statistic


    def printDetail(self):
        db = self.source.createDatabase()
        opDB = OpDataBase(db)
        op_order_list = opDB.load_order_all(self.project.id)
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
            statistic = self.makeStatistic(order_list)
            print(f"[交易率:{self.toRateText(statistic.dealCount, statistic.count)}"
                  f"(盈利欺骗占XX.XX%),"
                  f"成功率:{self.toRateText(statistic.predict_suc_deal_count, statistic.dealCount)},"
                  f"盈利率:{self.toRateText(statistic.earnCount, statistic.dealCount)},"
                  f"单均pct:{self.keep2Foat(self.divide(100 * statistic.totalPct, statistic.dealCount))},"
                  f"盈pct:{self.keep2Foat(self.divide(100 * statistic.totalEarnPct, statistic.earnCount))}({self.keep2Foat(100 * statistic.maxEarnPct)}),"
                  f"亏pct:{self.keep2Foat(self.divide(100 * (statistic.totalPct - statistic.totalEarnPct), statistic.dealCount - statistic.earnCount))}({self.keep2Foat(100 * statistic.maxLossPct)})]")

    def keep2Foat(self, v: float):
        return f"%.2f" % (v)

    def divide(self, f1: float, f2: float):
        if f2 < 0.0001:
            return 0.0
        return f1 / f2

    def toRateText(self, f1: float, f2: float) -> str:
        if f2 < 0.00001:
            return "0%"
        return f"%.2f%%" % (100 * f1 / f2)