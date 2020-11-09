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
        self.indicator = Indicator(40)
        self.code = code
        self.lasted15Bar = np.full(15,None)
        self.lasted3BarKdj = np.full(3,None)

        return True

    def getKdjHoldDay(self):
        k, d, j = self.indicator.kdj(fast_period=9, slow_period=3, array=True)
        assert abs(k[-2] - self.lasted3BarKdj[-2][0]) < 0.01
        assert abs(d[-3] -self.lasted3BarKdj[-3][1]) < 0.01
        holdDay = 0
        for i in range(-1, -6, -1):
            isHold = k[i] >= d[i]
            if not isHold:
                break
            holdDay += 1
        return holdDay

    def onCollectTrace(self, bar: BarData) -> CollectData:
        self.indicator.update_bar(bar)
        self.lasted15Bar[:-1] = self.lasted15Bar[1:]
        self.lasted3BarKdj[:-1] = self.lasted3BarKdj[1:]
        k, d, j = self.indicator.kdj(fast_period=9, slow_period=3)
        dif, dea, macdBar = self.indicator.macd( fast_period=12,slow_period = 26,signal_period = 9,array=True)

        self.lasted15Bar[-1] = bar
        self.lasted3BarKdj[-1] = [k, d, j]

        if self.indicator.count <37:
            return None

        #最近15天之内不含停牌数据
        if not BarUtils.isAllOpen(self.lasted15Bar):
            return None
        # 交易日天数间隔超过5天的数据
        if BarUtils.getMaxIntervalDay(self.lasted15Bar) >= 5:
            return None

        kdjHoldDay = self.getKdjHoldDay();

        if kdjHoldDay !=1:
            return None

        kPatternValue = KPattern.encode2KAgo1(self.indicator)
        if not kPatternValue is None:
            dimen = Dimension(type=TYPE_2KAGO1, value=kPatternValue)
            collectData = CollectData(dimen=dimen)
            collectData.occurBars = list(self.lasted15Bar[-3:])
            collectData.occurKdj = list(self.lasted3BarKdj)
            collectData.occurExtra['before_gold_corss_macd'] = [dif[-2],dea[-2],macdBar[-2]]
            return collectData
        return None

    def onCollect(self, data: CollectData, newBar: BarData) :
        #不含停牌数据
        if not BarUtils.isOpen(newBar):
            data.setValid(False)
            data.setFinished()
            return
        data.predictBars.append(newBar)
        data.setValid(True)
        size = len(data.predictBars)
        if size >= 5:
            data.setFinished()

    def getYLabelPct(self, cData:CollectData)->[float, float]:
        if len(cData.predictBars) < 5:
            # 不能作为y标签。
            return None, None

        basePrice = self.getYBasePrice(cData)  ###为什么这里不同，给出的回测结果也不同，
        highBar = cData.predictBars[0];
        lowBar = cData.predictBars[0]
        sell_pct = 100 * ((highBar.high_price + highBar.close_price) / 2 - basePrice) / basePrice
        buy_pct = 100 * ((lowBar.low_price + lowBar.close_price) / 2 - basePrice) / basePrice

        for i in range(1, len(cData.predictBars)):
            bar: BarData = cData.predictBars[i]
            _s_pct = 100 * ((bar.high_price + bar.close_price) / 2 - basePrice) / basePrice
            _b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrice) / basePrice
            if _s_pct > sell_pct:
                sell_pct = _s_pct
            if _b_pct < buy_pct:
                buy_pct = _b_pct
        return sell_pct, buy_pct

    def getYBasePrice(self, cData:CollectData)->float:
        ##以金叉发生的当前收盘价作为基准值。
        return cData.occurBars[-1].close_price

    def generateXFeature(self, cData: CollectData) -> []:
        # 保证len等于三，要不然就不能作为生成特征值。
        if (len(cData.occurBars) < 3):
            return None
        ##金叉前一天作为basePrice
        basePrcie = self.getYBasePrice(cData)
        assert basePrcie > 1
        ##使用随机森林，所以不需要标准化和归一化
        ##金叉前一天的macd值
        god_cross_dif, god_cross_dea, god_cross_macd = cData.occurExtra.get('before_gold_corss_macd')

        god_cross_dif = 100 * god_cross_dif / basePrcie
        god_cross_dea = 100 * god_cross_dea / basePrcie
        ##金叉前一天的k，d，j
        k, d, j = cData.occurKdj[-2]
        def getSellBuyPct(bar: BarData):
            s_pct = 100 * ((bar.high_price + bar.close_price) / 2 - basePrcie) / basePrcie
            b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrcie) / basePrcie
            return s_pct, b_pct
        s_pct_1, b_pct_1 = getSellBuyPct(cData.occurBars[-3])  #金叉前两天
        s_pct_2, b_pct_2 = getSellBuyPct(cData.occurBars[-2])  #金叉前一天
        s_pct_3, b_pct_3 = getSellBuyPct(cData.occurBars[-1]) #金叉

        data = []
        data.append(god_cross_dif)
        data.append(god_cross_dea)
        data.append(k)
        data.append(d)
        data.append(s_pct_1)
        data.append(b_pct_1)
        data.append(s_pct_2)
        data.append(b_pct_2)
        data.append(s_pct_3)
        data.append(b_pct_3)
        return data

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

    runner.printZZ500Tops(CommonStrategy());


    pass

if __name__ == "__main__":
    #analysicQuantDataOnly()
    runBackTest()
    #printLaststTops()






