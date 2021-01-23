from datetime import datetime

import numpy as np
from earnmi.model.CollectModel import CollectModel
from peewee import Database
from earnmi.chart.Factory import Factory
from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.core.App import App
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineModel import CoreEngineModel
from earnmi.model.CoreEngineRunner import CoreEngineRunner
from earnmi.model.CoreEngineStrategy import CommonStrategy
from earnmi.model.DataSource import DatabaseSource
from earnmi.model.Dimension import Dimension, TYPE_2KAGO1
from earnmi.model.ProjectRunner import OpStrategy
from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.object import BarData

class SKDJ_CollectModel(CollectModel):

    def onCollectStart(self, code: str) -> bool:
        from earnmi.chart.Indicator import Indicator
        self.indicator = Indicator(34)
        self.lastedBars = np.full(3, None)
        self.lasted3BarKdj = np.full(3, None)
        self.lasted3BarMacd = np.full(3, None)
        self.lasted3BarArron = np.full(3, None)
        self.code = code
        return True

    def onCollectTrace(self, bar: BarData) -> CollectData:
        self.indicator.update_bar(bar)
        self.lastedBars[:-1] = self.lastedBars[1:]
        self.lasted3BarKdj[:-1] = self.lasted3BarKdj[1:]
        self.lasted3BarMacd[:-1] = self.lasted3BarMacd[1:]
        self.lasted3BarArron[:-1] = self.lasted3BarArron[1:]
        k, d, j = self.indicator.kdj(fast_period=9, slow_period=3)
        dif, dea, mBar = self.indicator.macd( fast_period=12,slow_period = 26,signal_period = 9)
        aroon_down,aroon_up = self.indicator.aroon( n=14)
        self.lastedBars[-1] = bar
        self.lasted3BarKdj[-1] = [k, d, j]
        self.lasted3BarMacd[-1] = [dif, dea, mBar]
        self.lasted3BarArron[-1] = [aroon_down,aroon_up]

        if self.indicator.count <=34:
            return None

        # 最近15天之内不含停牌数据
        if not BarUtils.isAllOpen(self.lastedBars):
            return None

        if dif < 0 or dea < 0:
            return None

        k0, d0, j0 = self.lasted3BarKdj[-3]
        k1, d1, j1 = self.lasted3BarKdj[-2]
        # 金叉产生
        goldCross = k0 < d0 and k1 >= d1
        if not goldCross:
            return None

        #最近12天的震荡因子和金叉当前的dea和dif因子组合作为维度值
        goldBar:BarData = self.lastedBars[-2]
        goldBarMacd = self.lasted3BarMacd[2];
        gold_dif_factory,gold_dea_factory = [ 100*goldBarMacd[0]/goldBar.close_price, 100*goldBarMacd[1]/goldBar.close_price]

        ##生成维度值
        verbute = Factory.vibrate(self.indicator.close,self.indicator.open,period=12)
        kPatternValue = self.makePatthernValue(verbute,gold_dif_factory,gold_dea_factory);

        dimen = Dimension(type=TYPE_2KAGO1, value=kPatternValue)
        collectData = CollectData(dimen=dimen)
        collectData.occurBars = list(self.lastedBars)
        collectData.occurKdj = list(self.lasted3BarKdj)
        collectData.occurExtra['lasted3BarMacd'] = self.lasted3BarMacd
        collectData.occurExtra['lasted3BarArron'] = self.lasted3BarArron
        verbute9 =Factory.vibrate(self.indicator.close,self.indicator.open,period=9)
        verbute20 =Factory.vibrate(self.indicator.close,self.indicator.open,period=20)
        collectData.occurExtra['verbute9'] = verbute9
        collectData.occurExtra['verbute20'] = verbute20
        collectData.occurExtra['aroon_up'] = self.lasted3BarArron[-1][1];
        collectData.occurExtra['aroon_down'] =  self.lasted3BarArron[-1][0]

        #收集对象的有效性:无要求
        collectData.setValid(True)
        return collectData

    def makePatthernValue(self, verbute, dif, dea):
        # mask1 = KDJMovementEngineModel.ENCODE1.mask()
        mask2 = SKDJ_EngineModel.ENCODE2.mask()
        v1 = SKDJ_EngineModel.ENCODE1.encode(verbute)
        v2 = SKDJ_EngineModel.ENCODE2.encode(dif)
        v3 = SKDJ_EngineModel.ENCODE2.encode(dea)
        return v1 * mask2 * mask2 + v2 * mask2 + v3;

    def onCollect(self, data: CollectData, newBar: BarData):
        # 不含停牌数据
        data.predictBars.append(newBar)
        size = len(data.predictBars)
        if size >= SKDJ_EngineModel.PREDICT_LENGT:
            data.setValid(BarUtils.isAllOpen(data.predictBars))
            data.setFinished()

class SKDJ_EngineModel(CoreEngineModel):

    PREDICT_LENGT = 3
    PCT_MAX_LIMIT = 99999999

    def __init__(self):
        self.kdjEncoder = FloatEncoder([15,30,45,60,75,90])
        self._collect_model  = SKDJ_CollectModel()


    def getCollectModel(self)->CollectModel:
        return self._collect_model

    def getEngineName(self):
        return "skdj_zz500"

    def getPctEncoder1(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-25,25.5, 50/30)), minValue=-26, maxValue=26)

    def getPctEncoder2(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-24.5, 27, 50 /30)), minValue=-25, maxValue=27)


    ENCODE1 = FloatEncoder([1,8,20,45,80]);
    ENCODE2 = FloatEncoder([-1,0,1,2.2,4.7]);


    def getYBasePrice(self, cData: CollectData) -> float:
        ## 金叉形成后的前一天
        return cData.occurBars[-1].close_price

    def getYLabelPct(self, cData:CollectData)->[float, float]:
        if len(cData.predictBars) < SKDJ_EngineModel.PREDICT_LENGT:
            #不能作为y标签。
            return None, None

        basePrice = self.getYBasePrice(cData)

        sell_pct =  -self.PCT_MAX_LIMIT
        buy_pct =  self.PCT_MAX_LIMIT

        for i in range(0,len(cData.predictBars)):
            bar:BarData = cData.predictBars[i]
            _s_pct = 100 * ((bar.high_price + bar.close_price) / 2 - basePrice) / basePrice
            _b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrice) / basePrice
            sell_pct = max(_s_pct,sell_pct)
            buy_pct = min(_b_pct,buy_pct)
        assert sell_pct > -self.PCT_MAX_LIMIT
        assert buy_pct < self.PCT_MAX_LIMIT
        return sell_pct, buy_pct

    def __to_one(self,vallue,min_value,max_value):
        if(vallue< min_value):
            return 0;
        if(vallue > max_value):
            return 1
        return (vallue - min_value) / (max_value-min_value)

    def generateXFeature(self, cData: CollectData) -> []:
        #保证len等于三，要不然就不能作为生成特征值。
        if (len(cData.occurBars) < 3):
            return None
        basePrcie = self.getYBasePrice(cData)
        data = []

        #occurBars[-1]最后一天（ 金叉形成后的第2天）形成的收盘价pct，开盘价pct，最低价pct，最高价pct （4个）
        lastest1_occurBars :BarData = cData.occurBars[-1]
        open_pct = 100 * (lastest1_occurBars.open_price - basePrcie) / basePrcie
        high_pct = 100 * (lastest1_occurBars.high_price - basePrcie) / basePrcie
        close_pct = 100 * (lastest1_occurBars.close_price - basePrcie) / basePrcie
        low_pct = 100 * (lastest1_occurBars.low_price - basePrcie) / basePrcie
        data.append(self.__to_one(open_pct,-10,10))
        data.append(self.__to_one(high_pct,-10,10))
        data.append(self.__to_one(close_pct,-10,10))
        data.append(self.__to_one(low_pct,-10,10))

        ##使用随机森林，所以不需要标准化和归一化
        #金叉生成当天的（occurBars[-2]）的macd的dea，def因子，和kdj的k，d值，收盘价pct（5个）
        gold_occurBars :BarData = cData.occurBars[-2]
        god_cross_dif, god_cross_dea, god_cross_macd = cData.occurExtra.get('lasted3BarMacd')[-2]
        god_cross_dif = 100 * god_cross_dif / gold_occurBars.close_price
        god_cross_dea = 100 * god_cross_dea / gold_occurBars.close_price
        k, d, j = cData.occurKdj[-2]
        gold_close_pct = 100 * (gold_occurBars.close_price - basePrcie) / basePrcie
        data.append(self.__to_one(god_cross_dif,-10,10))
        data.append(self.__to_one(god_cross_dea,-10,10))
        data.append(self.__to_one(k,0,100))
        data.append(self.__to_one(d,0,100))
        data.append(self.__to_one(gold_close_pct,-10,10))

        #occurBars[-1]最后一天的震荡因子值：virbute_9,virbute_20
        #occurBars[ -1]最后一天的arron_up,arron_down值
        data.append(self.__to_one(cData.occurExtra.get('verbute9'),0,100))
        data.append(self.__to_one(cData.occurExtra.get('verbute20'),0,100))
        data.append(self.__to_one(cData.occurExtra.get('aroon_up'),0,100))
        data.append(self.__to_one(cData.occurExtra.get('aroon_down'),0,100))
        return data


def analysicQuantDataOnly():
    dirName = "models/skdj_analysic_quantdata"
    start = datetime(2015, 10, 1)
    end = datetime(2019, 10, 1)

    souces = ZZ500DataSource(start, end)
    model = SKDJ_EngineModel()
    create = False
    engine = None
    if create:
        engine = CoreEngine.create(dirName, model,souces,build_quant_data_only = True,min_size=200)
    else:
        engine = CoreEngine.load(dirName,model)
        #engine.buildQuantData()
    engine.buildPredictModel(useSVM=False)
    pass


class SKDJ_EngineModelV2(SKDJ_EngineModel):

        def __to_one(self, vallue, min_value, max_value):
            if (vallue < min_value):
                return 0;
            if (vallue > max_value):
                return 1
            return (vallue - min_value) / (max_value - min_value)

        def generateXFeature(self, cData: CollectData) -> []:
            # 保证len等于三，要不然就不能作为生成特征值。
            if (len(cData.occurBars) < 3):
                return None
            basePrcie = self.getYBasePrice(cData)
            data = []

            # occurBars[-1]最后一天（ 金叉形成后的第2天）形成的收盘价pct，最低价pct（2个）
            lastest1_occurBars: BarData = cData.occurBars[-1]
            open_pct = 100 * (lastest1_occurBars.open_price - basePrcie) / basePrcie
            high_pct = 100 * (lastest1_occurBars.high_price - basePrcie) / basePrcie
            close_pct = 100 * (lastest1_occurBars.close_price - basePrcie) / basePrcie
            low_pct = 100 * (lastest1_occurBars.low_price - basePrcie) / basePrcie
            data.append(open_pct)
            data.append(high_pct)
            data.append(close_pct)
            data.append(low_pct)

            ##使用随机森林，所以不需要标准化和归一化
            # 金叉生成当天的（occurBars[-2]）的macd的dea，def因子，金叉生成当天（occurBars[-2]）sell_pct,buy_pct;
            def getSellBuyPct(bar: BarData):
                s_pct = 100 * ((bar.high_price + bar.close_price) / 2 - basePrcie) / basePrcie
                b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrcie) / basePrcie
                return s_pct, b_pct
            gold_occurBars: BarData = cData.occurBars[-2]
            god_cross_dif, god_cross_dea, god_cross_macd = cData.occurExtra.get('lasted3BarMacd')[-2]
            god_cross_dif = 100 * god_cross_dif / gold_occurBars.close_price
            god_cross_dea = 100 * god_cross_dea / gold_occurBars.close_price
            gold_sell_pct,golde_buy_pct  = getSellBuyPct(gold_occurBars)
            data.append(god_cross_dif)
            data.append(god_cross_dea)
            data.append(gold_sell_pct)
            data.append(golde_buy_pct)

            # occurBars[-1]最后一天的震荡因子值：virbute_9,virbute_20
            # occurBars[ -1]最后一天的arron_up,arron_down值
            #data.append(cData.occurExtra.get('verbute9'))
            #data.append(cData.occurExtra.get('verbute20'))
            data.append(cData.occurExtra.get('aroon_up'))
            data.append(cData.occurExtra.get('aroon_down'))
            return data


def __getBackTestRunner(engine):
    from earnmi.model.op import OpProject
    project = OpProject(id=1, status="new", name="skdj_500", create_time=datetime(year=2020, month=11, day=26))
    from earnmi.model.ProjectRunner import ProjectRunner
    from peewee import SqliteDatabase
    from earnmi.model.op import OpDataBase

    db_file = SqliteDatabase("models/skdj_zz500_runbacktest/project.db")
    db = OpDataBase(db_file);
    return ProjectRunner(project, db, engine)



def runBackTest():
    _dirName = "models/skdj_zz500_runbacktest"
    start = datetime(2015, 10, 1)
    middle = datetime(2019, 9, 30)
    end = datetime(2019, 12, 30)
    #end = datetime(2020, 9, 30)
    #end = datetime(2019,12,30)
    historySource = ZZ500DataSource(start, middle)
    futureSouce = ZZ500DataSource(middle, end)


    model = SKDJ_EngineModelV2()
    #strategy = DefaultStrategy()
    strategy = CommonStrategy()
    create = False
    engine = None
    if create:
        engine = CoreEngine.create(_dirName, model,historySource,min_size=200,useSVM=False)
    else:
        engine = CoreEngine.load(_dirName,model)
    runner = CoreEngineRunner(engine)

    class MyStrategy(CommonStrategy):
        DIMEN = [107, 93, 92, 100, 64, 57, 99]

        def __init__(self):
            super().__init__()
            self.paramMap = {}
            self.paramMap[99] = {'buy_offset_pct': None, 'sell_offset_pct': None, 'sell_leve_pct_bottom': 2}
            # self.paramMap[100] = {'buy_offset_pct': None, 'sell_offset_pct': 1, 'sell_leve_pct_bottom': 1}
            # self.paramMap[94] = {'buy_offset_pct': None, 'sell_offset_pct': 1, 'sell_leve_pct_bottom': 1}
            # self.paramMap[58] = {'buy_offset_pct': None, 'sell_offset_pct': None, 'sell_leve_pct_bottom': 1}

        def getParams(self, dimen_value: int):
            return self.paramMap.get(dimen_value)

        def isSupport(self, engine: CoreEngine, dimen: Dimension) -> bool:
            return not self.paramMap.get(dimen.value) is None

    class MyStrategy2(OpStrategy):
        DIMEN = [107, 93, 92, 100, 64, 57, 99]

        def __init__(self):
            super().__init__()
            self.paramMap = {}
            self.paramMap[99] = {'buy_offset_pct': None, 'sell_offset_pct': None, 'sell_leve_pct_bottom': 2}
            self.paramMap[100] = {'buy_offset_pct': None, 'sell_offset_pct': 1, 'sell_leve_pct_bottom': 1}
            self.paramMap[94] = {'buy_offset_pct': None, 'sell_offset_pct': 1, 'sell_leve_pct_bottom': 1}
            self.paramMap[58] = {'buy_offset_pct': None, 'sell_offset_pct': None, 'sell_leve_pct_bottom': 1}

        def getParams(self, dimen_value: int):
            return self.paramMap.get(dimen_value)

        def isSupport(self, dimen: Dimension) -> bool:
            return not self.paramMap.get(dimen.value) is None

    run_old_runner = True
    if run_old_runner:
        p_runnner = __getBackTestRunner(engine)
        futureSouce = ZZ500DataSource(middle, end)
        p_runnner.opDB.clearAll()
        p_runnner.runBackTest(futureSouce,MyStrategy2())
        p_runnner.printDetail()
    else:
        ##
        ##middle = datetime(2019, 11, 22)

        app = App()
        index_driver = StockIndexDriver()  ##A股指数驱动
        drvier2 = ZZ500StockDriver()  ##中证500股票池驱动
        #barManager:BarManager = BarManager.getBarManager(app)
        ##market = app.getBarManager().createBarMarket(index_driver, [drvier2])
        ##updator = app.getBarManager().createUpdator();
        ##updator.update(market,start)
        from earnmi.model.op import OpProject
        project = OpProject(id=1, status="new", name="skdj_500", create_time=datetime(year=2020, month=11, day=26))
        from earnmi.model.ProjectRunner import ProjectRunner
        from peewee import SqliteDatabase
        from earnmi.model.op import OpDataBase
        class MyDatabaseSource(DatabaseSource):
            def createDatabase(self) -> Database:
                return SqliteDatabase("models/skdj_zz500_runbacktest/project_v2.db")
        dataSource = MyDatabaseSource()

        db = dataSource.createDatabase()
        opDB = OpDataBase(db)
        opDB.clearAll()
        db.close()

        runner = ZZ500_ProjectRunner(name="skdj_500", project=project, source=dataSource, strategy=MyStrategy2(), engine=engine)
        app.getRunnerManager().add(runner)
        app.run_backtest(middle)
        seconds = int(end.timestamp() - middle.timestamp())
        app.engine.go(seconds)
        runner.printDetail()
        print(f"finished1！！！！！！！")


def printBackTest():
    p_runnner = __getBackTestRunner(None)
    p_runnner.printDetail()
    p_runnner.updateStatisitcs()
    pass



def printLaststTops():
    _dirName = "models/skdj_zz500_last_top"

    model = SKDJ_EngineModelV2()
    create = False
    engine = None
    if create:
        start = datetime(2015, 10, 1)
        end = datetime(2020, 9, 30)
        historySource = ZZ500DataSource(start, end)
        engine = CoreEngine.create(_dirName, model, historySource, min_size=200,useSVM=False)
    else:
        engine = CoreEngine.load(_dirName, model)


    runner = CoreEngineRunner(engine)

    class MyStrategy(CommonStrategy):
        DIMEN = [107, 93, 92, 100, 64, 57, 99]

        def __init__(self):
            super().__init__()
            self.paramMap = {}
            self.paramMap[99] = {'buy_offset_pct': None, 'sell_offset_pct': None, 'sell_leve_pct_bottom': 2}
            self.paramMap[100] = {'buy_offset_pct': None, 'sell_offset_pct': 1, 'sell_leve_pct_bottom': 1}
            self.paramMap[94] = {'buy_offset_pct': None, 'sell_offset_pct': 1, 'sell_leve_pct_bottom': 1}
            self.paramMap[58] = {'buy_offset_pct': None, 'sell_offset_pct': None, 'sell_leve_pct_bottom': 1}

        def getParams(self, dimen_value: int):
            return self.paramMap.get(dimen_value)

        def isSupport(self, engine: CoreEngine, dimen: Dimension) -> bool:
            return not self.paramMap.get(dimen.value) is None

    # keys = {"database", "user", "password", "host", "port"}
    # settings = {k: v for k, v in settings.items() if k in keys}
    from peewee import MySQLDatabase
    # db = MySQLDatabase(**settings)
    dbSetting = {"database":"vnpy","user":"root","password":"Qwer4321","host":"localhost","port":3306}
    #db = SqliteDatabase("opdata.db")
    db = MySQLDatabase(**dbSetting)
    runner.runZZ500Now(db,MyStrategy());


    pass




if __name__ == "__main__":
    #analysicQuantDataOnly()
    runBackTest()
    #printLaststTops()
    #printBackTest()
    """
[99]=>count:15(sScore:93.333,bScore:53.333),做多:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)],做空:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[100]=>count:39(sScore:76.923,bScore:66.666),做多:[交易率:38.46%(盈利欺骗占6.67%),成功率:13.33%,盈利率:33.33%,单均pct:-0.40,盈pct:2.93(6.00),亏pct:-2.07(-7.21)],做空:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[58]=>count:10(sScore:80.0,bScore:60.0),做多:[交易率:40.00%(盈利欺骗占25.00%),成功率:75.00%,盈利率:75.00%,单均pct:1.24,盈pct:1.67(1.69),亏pct:-0.07(-0.07)],做空:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[94]=>count:10(sScore:70.0,bScore:80.0),做多:[交易率:50.00%(盈利欺骗占0.00%),成功率:60.00%,盈利率:60.00%,单均pct:0.93,盈pct:2.94(3.51),亏pct:-2.09(-3.97)],做空:[交易率:0.00%(盈利欺骗占0.00%),成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]

[交易率:13.16%(盈利欺骗占XX.XX%),成功率:55.00%,盈利率:75.00%,单均pct:1.24,盈pct:3.37(4.97),亏pct:-5.15(-9.76)]

注意：预测得分高并一定代表操作成功率应该高，因为很多情况是先到最高点，再到最低点，有个顺序问题
回测总性能:count:847(sScore:80.519,bScore:67.886)
做多:[交易率:40.61%(盈利欺骗占0.00%),成功率:41.86%,盈利率:59.30%,单均pct:0.43,盈pct:3.03(7.00),亏pct:-3.36(-16.63)]
    """





