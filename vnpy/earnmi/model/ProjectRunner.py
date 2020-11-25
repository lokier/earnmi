from collections import Sequence
from datetime import datetime

from earnmi.model.BarDataSource import BarDataSource
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineStrategy import CoreEngineStrategy
from earnmi.model.Dimension import Dimension
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder
from earnmi.model.op import *


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
            strategy.onInitOrder(order,debug_parms)


            self.__updateOrdres(strategy, order, predict.collectData.predictBars,debug_parms = debug_parms);


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

