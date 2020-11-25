from collections import Sequence
from datetime import datetime

from ibapi.common import BarData

from earnmi.model.BarDataSource import BarDataSource
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineStrategy import CoreEngineStrategy
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder, PredictOrderStatus
from earnmi.model.op import *



class OpRunner(object):

    def __init__(self,order:PredictOrder,op_project:OpProject,db:OpDataBase,strategy:CoreEngineStrategy):
        self.op_project = op_project;
        self.strategy = strategy
        self.order = order
        self.db = db
        self.inited = None
        self.op_orde:OpOrder = None
        self.order = None
        self.isOpenMarket = False
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
        op_log = self.strategy.onBeginOrder(self.order, debug_parms)
        self.op_order = self.__loadOpOrder(self.order)
        assert not self.op_order is None;
        self.saveLog(op_log)

    """
    开始一天的交易
    """
    def openMarket(self, time:datetime,debug_parms:{} = None):
        assert self.inited
        assert self.isOpenMarket == False
        if self.isFinished():
            return False
        if (self.op_order.update_time - time).days > 0:
            ## 过滤历史bar时间。
            return False
        self.isOpenMarket = True
        opLog = self.strategy.onOpenTrade(self.order,debug_parms)
        self.saveLog(opLog)
        return True


    def update(self,bar:BarData,debug_parms:{} = None):
        assert self.inited
        assert self.isOpenMarket == True

        if self.op_order.update_time >= bar.datetime:
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

    def unInit(self, endBar:BarData, debug_parms:{} = None):
        assert self.inited
        self.inited = False
        order = self.order
        if order.status == PredictOrderStatus.HOLD or order.status == PredictOrderStatus.READY:
            order.sellPrice = endBar.close_price
            order.status = PredictOrderStatus.FAIL
            cross_op_log = OpLog(type=OpLogType.CROSS_FAIL, info=f"超过持有天数限制，当天收盘价割单", time=endBar.datetime)
            self.saveLog(cross_op_log)
        order.update_time = endBar.datetime
        self.__updateOpOrder()
        opLog = self.strategy.onEndOrder(self.order, endBar, debug_parms)
        self.saveLog(opLog)
        assert  self.isFinished()


    def __updateOpOrder(self, time:datetime):
        assert time>= self.op_order.update_time
        if time == self.op_order.update_time:
            return
        if (self.op_order.update_time - time).days < 0:
            self.op_order.duration +=1

        self.op_order.update_time = time
        order = self.order

        if order.status == PredictOrderStatus.HOLD:
            self.op_order.status =  OpOrderStatus.HOLD
        elif order.status == PredictOrderStatus.ABANDON:
            self.op_order.status = OpOrderStatus.INVALID
        elif order.status!= PredictOrderStatus.READY:
            real_buy_price, real_sell_price = self.db.load_order_sell_buy_price(self.op_order.id)
            assert not real_buy_price is None
            assert not real_sell_price is None
            assert order.status == PredictOrderStatus.SUC or order.status == PredictOrderStatus.FAIL
            if real_sell_price>= real_buy_price:
                self.op_order.status = OpOrderStatus.FINISHED_EARN
            else:
                self.op_order.status = OpOrderStatus.FINISHED_LOSS
            self.op_order.predict_suc = order.status == PredictOrderStatus.SUC
        self.db.save_order(self.op_order)


    def saveLog(self,log:OpLog):
        log.order_id = self.op_order.id
        self.db.save_log(log)

    def __loadOpOrder(self, order: PredictOrder) -> OpOrder:
        op_order = self.db.load_order_by_time(order.code, order.create_time)
        if op_order is None:
            op_order = OpOrder(code=order.code, code_name=order.code, project_id=self.project.id,
                               create_time=order.create_time
                               , buy_price=order.strategyBuyPrice, sell_price=order.strategySellPrice)
            op_order.op_name = f"dimen:{order.dimen}"
            op_order.status = "新的"
            op_order.duration = 0
            self.db.save_order(op_order)
            op_order = self.db.load_order_by_time(order.code, order.create_time)
            assert not op_order is None
        return op_order



class ProjectRunner():

    def __init__(self, project: OpProject, opDB:OpDataBase,engine: CoreEngine):
        self.coreEngine: CoreEngine = engine
        self.project = project
        self.opDB = opDB
        assert not project.id is None
        self.opDB.save_projects(project)


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
        print(f"[runner|{datetime}]: {info}")


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

        __dataList = {}
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
            _testData = self.__run_backtest(model,strategy,dimen,listData);
            __dataList[dimen] = _testData

    def __run_backtest(self,model,strategy,dimen:Dimension,listData:Sequence['CollectData'],debug_parms:{} = None):
        predictList: Sequence['PredictData'] = model.predict(listData)
        for predict in predictList:
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
                runner.unInit(lastBar.debug_parms)




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




if __name__ == "__main__":
    pass

