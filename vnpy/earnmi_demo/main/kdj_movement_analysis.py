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
        self.lasted15Bar = np.array([None ,None ,None,None,None,None,None,None,None,None,None,None,None,None,None])
        self.lasted3BarKdj = np.array([None ,None ,None])
        self.lasted3BarMacd = np.array([None ,None ,None])
        self.lasted3BarArron = np.array([None ,None ])

        self.kdjEncoder = FloatEncoder([15,30,45,60,75,90])
        self.mDateOccurCountMap = {} ##统计产生收集个数的次数
        self.sw = SWImpl()

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

        if self.indicator.count <=15:
            return None

        #最近15天之内不含停牌数据
        if not BarUtils.isAllOpen(self.lasted15Bar):
            return None
        #交易日天数间隔超过5天的数据
        if BarUtils.getMaxIntervalDay(self.lasted15Bar) >= 5:
            return None

        timeKey = utils.to_start_date(bar.datetime);
        if self.mDateOccurCountMap.get(timeKey) is None:
            self.mDateOccurCountMap[timeKey] = 0

        if self.indicator.count >=30:
            k0,d0,j0 = self.lasted3BarKdj[-2]
            k1,d1,j1 = self.lasted3BarKdj[-1]
            #金叉产生
            goldCross =  k0 < d0 and k1>=d1
            if not goldCross:
                return None
            kPatternValue = KPattern.encode3KAgo1(self.indicator)
            if not kPatternValue is None :
                self.mDateOccurCountMap[timeKey] +=1
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
        goldCrossBar = cData.occurBars[-2]

        occurBar = cData.occurBars[-2]
        skipBar = cData.occurBars[-1]
        kdj = cData.occurKdj[-1]
        sell_pct = 100 * (
                (skipBar.high_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price
        buy_pct = 100 * (
                (skipBar.low_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price

        def set_0_between_100(x):
            if x > 100:
                return 100
            if x < 0:
                return 0
            return x

        def percent_to_one(x):
            return int(x * 100) / 1000.0

        data = []
        data.append(percent_to_one(buy_pct))
        data.append(percent_to_one(sell_pct))
        data.append(set_0_between_100(kdj[0])/100)
        data.append(set_0_between_100(kdj[2])/100)
        return data

class MyStrategy(CoreEngineStrategy):
    def __init__(self):
        self.sw = SWImpl()
        self.mDateHoldCountMap = {} ##统计产生收集个数的次数

    def generatePredictOrder(self, engine: CoreEngine, predict: PredictData, debugPrams: {} = None) -> PredictOrder:

        if debugPrams is None:
            debugPrams = {}

        code = predict.collectData.occurBars[-1].symbol
        name = self.sw.getSw2Name(code)
        order = PredictOrder(dimen=predict.dimen, code=code, name=name)
        predict_sell_pct = predict.getPredictSellPct()
        predict_buy_pct = predict.getPredictSellPct()
        start_price = engine.getEngineModel().getYBasePrice(predict.collectData)
        order.suggestSellPrice = start_price * (1 + predict_sell_pct / 100)
        order.suggestBuyPrice = start_price * (1 + predict_buy_pct / 100)
        order.power_rate = engine.queryQuantData(predict.dimen).getPowerRate()

        timeKey = utils.to_start_date(predict.collectData.occurBars[-1].datetime);
        if self.mDateHoldCountMap.get(timeKey) is None:
            self.mDateHoldCountMap[timeKey] = 0

        ##for backTest
        occurBar: BarData = predict.collectData.occurBars[-2]
        skipBar: BarData = predict.collectData.occurBars[-1]
        buy_price = skipBar.close_price
        predict_sell_pct = 100 * (order.suggestSellPrice - start_price) / start_price
        predict_buy_pct = 100 * (order.suggestBuyPrice - start_price) / start_price
        buy_point_pct = 100 * (buy_price - occurBar.close_price) / occurBar.close_price  ##买入的价格

        abilityData = engine.queryPredictAbilityData(predict.dimen)
        quantData = engine.queryQuantData(predict.dimen)
        delta = abs(quantData.sellCenterPct) - abs(quantData.buyCenterPct)
        if abs(delta) < 0.05:
            # 多空力量差不多
            power = 0
        if delta > 0:
            # 适合做多
            power = (quantData.sellCenterPct + quantData.buyCenterPct) / quantData.sellCenterPct
        else:
            power = - (quantData.sellCenterPct + quantData.buyCenterPct) / quantData.buyCenterPct

        extraCondition = True
        quant_power = debugPrams.get("quant_power")
        if not quant_power is None:
            extraCondition = extraCondition and predict.quantData.getPowerRate() >= quant_power

        predict_buy_pct_param = debugPrams.get("predict_buy_pct")
        if not predict_buy_pct_param is None:
            extraCondition = extraCondition and predict_buy_pct >= predict_buy_pct_param

        if extraCondition and predict_sell_pct - buy_point_pct > 1 \
                and abilityData.trainData.biasSellLoss < 10:
            order.status = PredictOrderStatus.HOLD
            order.buyPrice = buy_price

            timeKey = utils.to_start_date(predict.collectData.occurBars[-1].datetime);
            self.mDateHoldCountMap[timeKey] +=1

        else:
            order.status = PredictOrderStatus.STOP
        return order

    def updatePredictOrder(self, order: PredictOrder, bar: BarData, isTodayLastBar: bool,debugParams:{}=None):
        if (order.status == PredictOrderStatus.HOLD):
            if bar.high_price >= order.suggestSellPrice:
                order.sellPrice = order.suggestSellPrice
                order.status = PredictOrderStatus.CROSS
                return
            order.holdDay += 1
            if order.holdDay >= 2:
                order.sellPrice = bar.close_price
                order.status = PredictOrderStatus.CROSS
                return

def analysicQuantDataOnly(start:datetime,end:datetime):
    souces = ZZ500DataSource(start, end)
    model = KDJMovementEngineModel()

    create = False
    engine = None
    if create:
        engine = CoreEngine.create(dirName, model,souces,build_quant_data_only = True,min_size=200)
    else:
        engine = CoreEngine.load(dirName,model)
        engine.buildPredictModel()



    pass

if __name__ == "__main__":

    """
    动量指标：
    
    策略：
        收集arron_up>arron_down,且arron_up大于50的数据对象。
    """
    dirName = "models/kdj_movement_analysis"
    start = datetime(2015, 10, 1)
    middle = datetime(2019, 9, 30)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    trainDataSouce = ZZ500DataSource(start, middle)
    testDataSouce = ZZ500DataSource(middle, end)

    analysicQuantDataOnly(start,end)




