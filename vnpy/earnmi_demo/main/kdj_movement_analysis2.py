from datetime import datetime, timedelta
from functools import cmp_to_key
from typing import Sequence

import pandas as pd
import numpy as np
import sklearn
from sklearn import model_selection
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
import pickle

from earnmi.chart.Chart import Chart
from earnmi.chart.Factory import Factory
from earnmi.data.SWImpl import SWImpl
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.CoreEngineRunner import CoreEngineRunner
from earnmi.model.CoreEngineStrategy import CoreEngineStrategy
from earnmi.model.PredictData2 import PredictData
from earnmi.uitl.BarUtils import BarUtils
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData

from earnmi.data.SWImpl import SWImpl
from earnmi.model.CoreEngineModel import CoreEngineModel
from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Union, Tuple, Sequence

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngine import CoreEngine,PredictModel
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.Dimension import Dimension, TYPE_2KAGO1
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder, PredictOrderStatus
from earnmi.model.QuantData import QuantData
from earnmi.model.CoreEngineModel import CoreEngineModel
from vnpy.trader.object import BarData
import numpy as np
import pandas as pd
from earnmi.chart.KPattern import KPattern

class KDJMovementEngineModel(CoreEngineModel):

    def __init__(self):
        self.lasted15Bar = np.array([None ,None ,None,None,None,None,None,None,None,None,None,None,None,None,None])
        self.lasted3BarKdj = np.array([None ,None ,None])
        self.lasted3BarMacd = np.array([None ,None ,None])
        self.lasted3BarArron = np.array([None ,None ])
        self.kdjEncoder = FloatEncoder([15,30,45,60,75,90])

    def getPctEncoder1(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-25,25.5, 50/15)), minValue=-26, maxValue=26)

    def getPctEncoder2(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-24.5, 27, 50 / 15)), minValue=-25, maxValue=27)

    def onCollectStart(self, code: str) -> bool:
        from earnmi.chart.Indicator import Indicator
        self.indicator = Indicator(34)
        self.code = code
        return True


    def onCollectTrace(self, bar: BarData) -> CollectData:
        self.indicator.update_bar(bar)
        self.lasted15Bar[:-1] = self.lasted15Bar[1:]
        self.lasted3BarKdj[:-1] = self.lasted3BarKdj[1:]
        self.lasted3BarMacd[:-1] = self.lasted3BarMacd[1:]
        self.lasted3BarArron[:-1] = self.lasted3BarArron[1:]
        k, d, j = self.indicator.kdj(fast_period=9, slow_period=3)
        dif, dea, mBar = self.indicator.macd( fast_period=12,slow_period = 26,signal_period = 9)
        aroon_down,aroon_up = self.indicator.aroon( n=14)

        self.lasted15Bar[-1] = bar
        self.lasted3BarKdj[-1] = [k, d, j]
        self.lasted3BarMacd[-1] = [dif, dea, mBar]
        self.lasted3BarArron[-1] = [aroon_down,aroon_up]

        if self.indicator.count <=34:
            return None

        if dif < 0 or dea < 0:
            return None

        #最近15天之内不含停牌数据
        if not BarUtils.isAllOpen(self.lasted15Bar):
            return None
        #交易日天数间隔超过5天的数据
        # if BarUtils.getMaxIntervalDay(self.lasted15Bar) >= 5:
        #     return None
        k0, d0, j0 = self.lasted3BarKdj[-2]
        k1, d1, j1 = self.lasted3BarKdj[-1]
        # 金叉产生
        goldCross = k0 < d0 and k1 >= d1
        if not goldCross:
            return None

        verbute = Factory.vibrate(self.indicator.close,self.indicator.open,period=12)
        kPatternValue = self.makePatthernValue(verbute,dif/bar.close_price,dea/bar.close_price);
        dimen = Dimension(type=TYPE_2KAGO1, value=kPatternValue)
        collectData = CollectData(dimen=dimen)
        collectData.occurBars = list(self.lasted15Bar[-3:])
        collectData.occurKdj = list(self.lasted3BarKdj)
        collectData.occurExtra['lasted3BarMacd'] = self.lasted3BarMacd
        collectData.occurExtra['lasted3BarArron'] = self.lasted3BarArron

        verbute9 =Factory.vibrate(self.indicator.close,self.indicator.open,period=9)
        verbute20 =Factory.vibrate(self.indicator.close,self.indicator.open,period=20)
        collectData.occurExtra['verbute9'] = verbute9
        collectData.occurExtra['verbute20'] = verbute20
        collectData.occurExtra['aroon_up'] = self.lasted3BarArron[-1][1];
        collectData.occurExtra['aroon_down'] =  self.lasted3BarArron[-1][0]

        return collectData

    ENCODE1 = FloatEncoder([0,1,5,10,20,50,80]);
    ENCODE2 = FloatEncoder([-5,-3,-2,-1,0,1,2,3,5]);

    def makePatthernValue(self,verbute, dif,dea):
        #mask1 = KDJMovementEngineModel.ENCODE1.mask()
        mask2 = KDJMovementEngineModel.ENCODE2.mask()
        v1 = KDJMovementEngineModel.ENCODE1.encode(verbute)
        v2 = KDJMovementEngineModel.ENCODE2.encode(dif)
        v3 = KDJMovementEngineModel.ENCODE2.encode(dea)
        return v1 * mask2 * mask2 + v2 * mask2 +v3;

    def onCollect(self, data: CollectData, newBar: BarData) :
        #不含停牌数据
        if not BarUtils.isOpen(newBar):
            data.setValid(False)
            return
        data.predictBars.append(newBar)
        size = len(data.predictBars)
        if size >= 5:
            data.setFinished()

    def getYLabelPct(self, cData:CollectData)->[float, float]:
        if len(cData.predictBars) < 5:
            #不能作为y标签。
            return None, None
        bars: ['BarData'] = cData.predictBars

        basePrice = self.getYBasePrice(cData)

        highIndex = 0
        lowIndex = 0
        highBar = cData.predictBars[0];
        lowBar = cData.predictBars[0]
        sell_pct =  100 * ((highBar.high_price + highBar.close_price) / 2 - basePrice) / basePrice
        buy_pct =  100 * ((lowBar.low_price + lowBar.close_price) / 2 - basePrice) / basePrice

        for i in range(1,len(cData.predictBars)):
            bar:BarData = cData.predictBars[i]
            _s_pct = 100 * ((bar.high_price + bar.close_price) / 2 - basePrice) / basePrice
            _b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrice) / basePrice
            if _s_pct > sell_pct:
                sell_pct = _s_pct
                highIndex = i
            if _b_pct < buy_pct:
                buy_pct = _b_pct
                lowIndex = i
        return sell_pct, buy_pct

    def getYBasePrice(self, cData:CollectData)->float:
        ##以金叉发生的当前收盘价作为基准值。
        return cData.occurBars[-2].close_price

    def generateXFeature(self, cData: CollectData) -> []:
        #保证len等于三，要不然就不能作为生成特征值。
        if(len(cData.occurBars) < 3):
            return None
        basePrcie = self.getYBasePrice(cData)

        ##使用随机森林，所以不需要标准化和归一化
        god_cross_dif,god_cross_dea,god_cross_macd = cData.occurExtra.get('lasted3BarMacd')[-1]
        god_cross_dif = 100 * god_cross_dif /cData.occurBars[-1].close_price
        god_cross_dea = 100 * god_cross_dea /cData.occurBars[-1].close_price
        k,d,j = cData.occurKdj[-2]

        def getSellBuyPct(bar:BarData):
            s_pct = 100 * ((bar.high_price + bar.close_price)/2 - basePrcie) / basePrcie
            b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrcie) / basePrcie
            return s_pct,b_pct

        s_pct,b_pc = getSellBuyPct(cData.occurBars[-1])

        data = []
        data.append(s_pct)
        data.append(b_pc)
        data.append(god_cross_dif)
        data.append(god_cross_dea)
        data.append(cData.occurExtra.get('verbute9'))
        data.append(cData.occurExtra.get('verbute20'))
        data.append(cData.occurExtra.get('aroon_up'))
        data.append(cData.occurExtra.get('aroon_down'))
        return data

class MyStrategy(CoreEngineStrategy):

    def __init__(self):
        pass

    """
      处理操作单
      0: 不处理
      1：做多
      2：做空
      3: 预测成功交割单
      4：预测失败交割单
      5：废弃改单
      """
    def operatePredictOrder(self,engine:CoreEngine, order: PredictOrder,bar:BarData,isTodayLastBar:bool,debugParams:{}=None) ->int:

        buyDay = 2
        if not  debugParams.get('buyDay') is None:
            buyDay = debugParams.get('buyDay')

        quantData = engine.queryQuantData(order.dimen)
        basePrice = engine.getEngineModel().getYBasePrice(order.predict.collectData)
        suggestSellPrice = order.suggestSellPrice
        suggestBuyPrcie =  order.suggestBuyPrice

        if (order.status == PredictOrderStatus.HOLD):
            if bar.high_price >= suggestSellPrice:
                order.sellPrice = suggestSellPrice
                return 3
            if order.durationDay > 5:
                order.sellPrice = bar.close_price
                return 4
            # 买入之后第二天收盘价亏，止损卖出
            if order.durationDay> buyDay and bar.close_price <= order.buyPrice:
                order.sellPrice = bar.close_price
                return 4
        elif order.status == PredictOrderStatus.READY:

            if order.durationDay > buyDay:
                return 5
            targetPrice = bar.low_price
            if order.durationDay == 0: #生成的那天
                # if order.suggestSellPrice > bar.high_price:
                #      #废弃改单
                #      return 5
                targetPrice = bar.close_price
            if suggestBuyPrcie >= targetPrice:
                order.buyPrice = targetPrice
                return 1

        return 0

def analysicQuantDataOnly():
    dirName = "models/kdj_movement_analysis2"
    start = datetime(2015, 10, 1)
    middle = datetime(2019, 9, 30)
    end = datetime(2020, 9, 30)

    souces = ZZ500DataSource(start, end)
    model = KDJMovementEngineModel()
    create = False
    engine = None
    if create:
        engine = CoreEngine.create(dirName, model,souces,build_quant_data_only = True,min_size=200)
    else:
        engine = CoreEngine.load(dirName,model)
        engine.buildQuantData()
        #engine.buildPredictModel(useSVM=False)
    pass

def runBackTest():
    _dirName = "models/kdj_movement_analysis_back_test2"
    start = datetime(2015, 10, 1)
    middle = datetime(2019, 9, 30)
    end = datetime(2020, 9, 30)
    historySource = ZZ500DataSource(start, middle)
    futureSouce = ZZ500DataSource(middle, end)

    model = KDJMovementEngineModel()
    create = False
    engine = None
    if create:
        engine = CoreEngine.create(_dirName, model,historySource,min_size=200,useSVM=False)
    else:
        engine = CoreEngine.load(_dirName,model)
    runner = CoreEngineRunner(engine)
    runner.backtest(futureSouce, MyStrategy(), min_deal_count=-1)
    #params = {'buyDay':[0,1,2,3]}
    #runner.debugBestParam(futureSouce, MyStrategy(),params, min_deal_count=-1)


    pass

def printLaststTops():
    _dirName = "models/kdj_movement_lastesd_top"

    model = KDJMovementEngineModel()
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

    runner.printZZ500Tops(MyStrategy());


    pass

if __name__ == "__main__":
    #analysicQuantDataOnly()
    runBackTest()
    #printLaststTops()
    """
     day <= 2
    [555] = > count: 454(sScore:76.651, bScore: 63.876), 做多: [交易率:44.05 %, 成功率: 45.00 %, 单均pct: 2.12, 盈pct: 6.37(17.15), 亏pct: -2.98(-10.02)], 
    [455] = > count: 1259(sScore:79.189, bScore: 61.318), 做多: [交易率:45.35 %, 成功率: 46.06 %, 单均pct: 2.10, 盈pct: 5.22(19.42), 亏pct: -2.20(-11.45)], 做空: [交易率:0.00 %, 成功率: 0.00 %, 单均pct: 0.00, 盈pct: 0.00(0.00), 亏pct: 0.00(0.00)]
    [355] = > count: 965(sScore:80.103, bScore: 66.528), 做多: [交易率:54.92 %, 成功率: 50.38 %, 单均pct: 1.52, 盈pct: 3.99( 17.19), 亏pct: -1.93(-9.98)], 做空: [交易率:0.00 %, 成功率: 0.00 %, 单均pct: 0.00, 盈pct: 0.00(0.00), 亏pct: 0.00(0.00)]
    [255] = > count: 239(sScore:73.221, bScore: 55.648), 做多: [交易率:44.77 %, 成功率: 39.25 %, 单均pct: 0.61, 盈pct: 3.68(15.10), 亏pct: -2.18(-9.44)], 做空: [交易率:0.00 %, 成功率: 0.00 %, 单均pct: 0.00, 盈pct: 0.00(0.00), 亏pct: 0.00(0.00)]

    """

    # from earnmi.uitl.jqSdk import jqSdk
    #
    # jq = jqSdk.get()
    #
    # todayBarsMap = jqSdk.fethcNowDailyBars(ZZ500DataSource.SZ500_JQ_CODE_LIST)
    #
    # for code,bar in todayBarsMap.items():
    #     print(f"code:{code},price:{bar.close_price}")
    # print(f"todayBars:{len(todayBarsMap)}")
    """
    动量指标：
    
    策略：
        收集arron_up>arron_down,且arron_up大于50的数据对象。
    """





