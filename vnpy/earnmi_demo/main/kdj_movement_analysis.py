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

        if self.indicator.count <=15:
            return None

        #最近15天之内不含停牌数据
        if not BarUtils.isAllOpen(self.lasted15Bar):
            return None
        #交易日天数间隔超过5天的数据
        if BarUtils.getMaxIntervalDay(self.lasted15Bar) >= 5:
            return None

        if self.indicator.count >=30:
            k0,d0,j0 = self.lasted3BarKdj[-2]
            k1,d1,j1 = self.lasted3BarKdj[-1]
            #金叉产生
            goldCross =  k0 < d0 and k1>=d1
            if not goldCross:
                return None
            kPatternValue = KPattern.encode3KAgo1(self.indicator)
            if not kPatternValue is None :
                dimen = Dimension(type=TYPE_2KAGO1 ,value=kPatternValue)
                collectData = CollectData(dimen=dimen)
                collectData.occurBars = list(self.lasted15Bar[-3:])
                collectData.occurKdj = list(self.lasted3BarKdj)
                collectData.occurExtra['lasted3BarMacd'] = self.lasted3BarMacd
                collectData.occurExtra['lasted3BarArron'] = self.lasted3BarArron
                return collectData
        return None

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
        #保证len小于三，要不然就不能作为生成特征值。
        if(len(cData.occurBars) < 3):
            return None
        basePrcie = self.getYBasePrice(cData)
        ##使用随机森林，所以不需要标准化和归一化
        goldCrossBar = cData.occurBars[-2]
        god_cross_dif,god_cross_dea,god_cross_macd = cData.occurExtra.get('lasted3BarMacd')[-2]
        god_cross_dif = 100 * god_cross_dif /basePrcie
        god_cross_dea = 100 * god_cross_dea / basePrcie
        k,d,j = cData.occurKdj[-2]

        def getSellBuyPct(bar:BarData):
            s_pct = 100 * ((bar.high_price + bar.close_price)/2 - basePrcie) / basePrcie
            b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrcie) / basePrcie
            return s_pct,b_pct

        s_pct_1,b_pct_1 = getSellBuyPct(cData.occurBars[-3])
        s_pct_2,b_pct_2 = getSellBuyPct(cData.occurBars[-2])
        s_pct_3,b_pct_3 = getSellBuyPct(cData.occurBars[-1])

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
        if (order.status == PredictOrderStatus.HOLD):
            if bar.high_price >= order.suggestSellPrice:
                order.sellPrice = order.suggestSellPrice
                return 3
            if order.durationDay > 5:
                order.sellPrice = bar.close_price
                return 4
        elif order.status == PredictOrderStatus.READY:
            if order.durationDay > 2:
                return 5
            quantData = engine.queryQuantData(order.dimen)
            targetPrice = bar.low_price
            if order.durationDay == 0: #生成的那天
                targetPrice = bar.close_price
            if order.suggestBuyPrice >= targetPrice:
                order.buyPrice = targetPrice
                return 1
        return 0

def analysicQuantDataOnly():
    dirName = "models/kdj_movement_analysis"
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
    _dirName = "models/kdj_movement_analysis_back_test"
    start = datetime(2015, 10, 1)
    middle = datetime(2019, 9, 30)
    end = datetime(2020, 9, 30)
    historySource = ZZ500DataSource(start, middle)
    futureSouce = ZZ500DataSource(middle, end)

    model = KDJMovementEngineModel()
    create = False
    engine = None
    if create:
        engine = CoreEngine.create(_dirName, model,historySource,min_size=200)
    else:
        engine = CoreEngine.load(_dirName,model)

    runner = CoreEngineRunner(engine)
    runner.backtest(futureSouce, MyStrategy(), min_deal_count=-1)

    pass

if __name__ == "__main__":
    #analysicQuantDataOnly()
    runBackTest()

    """
    动量指标：
    
    策略：
        收集arron_up>arron_down,且arron_up大于50的数据对象。
    """





