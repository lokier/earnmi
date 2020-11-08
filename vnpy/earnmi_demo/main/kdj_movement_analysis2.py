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
from earnmi.model.CoreEngineStrategy import CoreEngineStrategy, CommonStrategy
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

        self.kdjEncoder = FloatEncoder([15,30,45,60,75,90])

    def getPctEncoder1(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-25,25.5, 50/15)), minValue=-26, maxValue=26)

    def getPctEncoder2(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-24.5, 27, 50 / 15)), minValue=-25, maxValue=27)

    def onCollectStart(self, code: str) -> bool:
        from earnmi.chart.Indicator import Indicator
        self.indicator = Indicator(34)
        self.code = code
        self.lasted15Bar = np.array(
            [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None])
        self.lasted3BarKdj = np.array([None, None, None])
        self.lasted3BarMacd = np.array([None, None, None])
        self.lasted3BarArron = np.array([None, None])
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
        collectData.setValid(False)
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
            return
        data.predictBars.append(newBar)
        data.setValid(True)
        size = len(data.predictBars)
        if size >= 5:
            data.setFinished()

    def getYLabelPct(self, cData:CollectData)->[float, float]:
        if len(cData.predictBars) < 5:
            #不能作为y标签。
            return None, None
        bars: ['BarData'] = cData.predictBars

        basePrice = self.getYBasePrice(cData)

        highIndex = 1
        lowIndex = 1
        ##跳过第一天观察
        highBar = cData.predictBars[1];
        lowBar = cData.predictBars[1]
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
        return cData.occurBars[-1].close_price

    def generateXFeature(self, cData: CollectData) -> []:
        # 保证len等于三，要不然就不能作为生成特征值。
        if (len(cData.occurBars) < 3):
            return None
        basePrcie = self.getYBasePrice(cData)

        ##使用随机森林，所以不需要标准化和归一化
        god_cross_dif, god_cross_dea, god_cross_macd = cData.occurExtra.get('lasted3BarMacd')[-1]
        god_cross_dif = 100 * god_cross_dif / cData.occurBars[-1].close_price
        god_cross_dea = 100 * god_cross_dea / cData.occurBars[-1].close_price
        k, d, j = cData.occurKdj[-2]

        def getSellBuyPct(bar: BarData):
            s_pct = 100 * ((bar.high_price + bar.close_price) / 2 - basePrcie) / basePrcie
            b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrcie) / basePrcie
            return s_pct, b_pct

        s_pct, b_pc = getSellBuyPct(cData.occurBars[-1])


        assert len(cData.predictBars) > 0
        _bar: BarData = cData.predictBars[0]
        d1_low_pct = 100 * (_bar.low_price - basePrcie) / basePrcie
        d1_close_pct = 100 * (_bar.close_price - basePrcie) / basePrcie

        data = []
        #最后一天的low_pct,close_pct。相对于 （2个）

        data.append(d1_low_pct)
        data.append(d1_close_pct)
        data.append(s_pct)
        data.append(b_pc)
        data.append(god_cross_dif)
        data.append(god_cross_dea)
        data.append(cData.occurExtra.get('verbute9'))
        data.append(cData.occurExtra.get('verbute20'))
        data.append(cData.occurExtra.get('aroon_up'))
        data.append(cData.occurExtra.get('aroon_down'))
        return data


class DefaultStrategy(CoreEngineStrategy):

    def __init__(self):
        self.failBuyBar = None
        pass

    """
    根据时间调整策略。
    1、555 : pct_limit = 4,offset = 0, opera_day = 3  = ==> 交易率:11.45%,成功率:25.00%,盈利率:71.15%,单均pct:3.80
       455 : pct_llimi = 2,offset = -1%，opera_day= 2   =》[交易率:13.26%,成功率:41.32%,盈利率:76.05%,单均pct:3.50
    """
    def getParams(self):
        pass

    def operatePredictOrder(self, engine: CoreEngine, order: PredictOrder, bar: BarData, isTodayLastBar: bool,
                            debugParams: {} = None) -> int:
        first_day_pct_limit = 1
        buy_offset = -1
        opera_day = 2
        cut_loss = False ##减损

        # if order.dimen == 555:
        #     buy_offset = 0
        #     first_day_pct_limit = 2
        #     opera_day = 3


        suggestSellPrice = order.suggestSellPrice
        suggestBuyPrice = order.suggestBuyPrice * (1 + buy_offset /100)
        if (order.status == PredictOrderStatus.HOLD):
            if bar.high_price >= suggestSellPrice:
                order.sellPrice = suggestSellPrice
                return 3
            if cut_loss and bar.close_price  < suggestBuyPrice:
                order.sellPrice = bar.close_price
                return 4
            if order.durationDay >= 5:
                order.sellPrice = bar.close_price
                return 4
        elif order.status == PredictOrderStatus.READY:
            if order.durationDay > opera_day:
                return 5
            quantData = engine.queryQuantData(order.dimen)
            targetPrice = bar.low_price
            if order.durationDay == 0:  # 生成的那天
                targetPrice = bar.close_price
                return 0
            if order.durationDay == 1:  # 生成的那天
                ##这天观察走势,且最高价不能超过预测价
                __pct = 100 * (suggestSellPrice - bar.close_price) / bar.close_price
                if __pct < first_day_pct_limit:
                     return 5
                return 0
            if suggestBuyPrice >= targetPrice and order.durationDay <=opera_day:
                ##趋势形成的第二天买入。
                order.buyPrice = suggestBuyPrice
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
    #strategy = DefaultStrategy()
    #strategy = BestStrategy()
    create = True
    engine = None
    if create:
        engine = CoreEngine.create(_dirName, model,historySource,min_size=200,useSVM=False)
    else:
        engine = CoreEngine.load(_dirName,model)
    runner = CoreEngineRunner(engine)
    runner.backtest(futureSouce, CommonStrategy())
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

    runner.printZZ500Tops(DefaultStrategy());


    pass

if __name__ == "__main__":
    #analysicQuantDataOnly()
    runBackTest()
    #printLaststTops()
    """
[555]=>count:454(sScore:76.651,bScore:63.876),做多:[交易率:44.05%,预测成功率:45.00%,盈利率:54.50%,单均pct:2.12,盈pct:6.37(17.15),亏pct:-2.98(-10.02)],做空:[交易率:0.00%,预测成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[455]=>count:1259(sScore:79.189,bScore:61.318),做多:[交易率:45.35%,预测成功率:46.06%,盈利率:57.97%,单均pct:2.10,盈pct:5.22(19.42),亏pct:-2.20(-11.45)],做空:[交易率:0.00%,预测成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[355]=>count:965(sScore:80.103,bScore:66.528),做多:[交易率:54.92%,预测成功率:50.38%,盈利率:58.30%,单均pct:1.52,盈pct:3.99(17.19),亏pct:-1.93(-9.98)],做空:[交易率:0.00%,预测成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[255]=>count:239(sScore:73.221,bScore:55.648),做多:[交易率:44.77%,预测成功率:39.25%,盈利率:47.66%,单均pct:0.61,盈pct:3.68(15.10),亏pct:-2.18(-9.44)],做空:[交易率:0.00%,预测成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]

    """
    """
    动量指标：
    
    策略：
        收集arron_up>arron_down,且arron_up大于50的数据对象。
    """





