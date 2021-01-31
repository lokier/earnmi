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

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange2
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
            kPatternValue = KPattern.encode2KAgo1(self.indicator)
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
        return cData.occurBars[-1].close_price

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
    def operatePredictOrder2(self, engine:CoreEngine, order: PredictOrder, bar:BarData, isTodayLastBar:bool, debugParams:{}=None) ->int:
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
                order.buyPrice = order.suggestBuyPrice
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
    create = True
    engine = None
    if create:
        engine = CoreEngine.create(_dirName, model,historySource,min_size=200,useSVM=False)
    else:
        engine = CoreEngine.load(_dirName,model)

    runner = CoreEngineRunner(engine)
    strategy = CommonStrategy()
    #strategy = MyStrategy()
    runner.backtest(futureSouce, strategy)

    """
2020-11-09 20:02:03,800 - build - INFO - [dime:885]: count=220,pow_rate=0.059,sCenterPct=1.16,bCenterPct=-1.48
2020-11-09 20:02:03,800 - build - INFO -       sellRange:[[-0.21:3.12)=65.91%,[3.12:6.45)=15.45%,[-3.55:-0.21)=12.27%,[6.45:9.79)=5.00%,[-6.88:-3.55)=0.45%,[9.79:13.12)=0.45%,[26.45:max)=0.45%,[min:-23.55)=0.00%,[-23.55:-20.21)=0.00%,[-20.21:-16.88)=0.00%,[-16.88:-13.55)=0.00%,[-13.55:-10.21)=0.00%,[-10.21:-6.88)=0.00%,[13.12:16.45)=0.00%,[16.45:19.79)=0.00%,[19.79:23.12)=0.00%,[23.12:26.45)=0.00%,]
2020-11-09 20:02:03,801 - build - INFO -       buyRange:[[-3.03:0.30)=68.18%,[-6.37:-3.03)=19.09%,[0.30:3.63)=6.36%,[-9.70:-6.37)=4.55%,[-13.03:-9.70)=0.91%,[3.63:6.97)=0.91%,[min:-26.37)=0.00%,[-26.37:-23.03)=0.00%,[-23.03:-19.70)=0.00%,[-19.70:-16.37)=0.00%,[-16.37:-13.03)=0.00%,[6.97:10.30)=0.00%,[10.30:13.63)=0.00%,[13.63:16.97)=0.00%,[16.97:20.30)=0.00%,[20.30:23.63)=0.00%,[23.63:max)=0.00%,]
2020-11-09 20:02:03,896 - build - INFO - [dime:886]: count=290,pow_rate=0.898,sCenterPct=2.47,bCenterPct=-0.61
2020-11-09 20:02:03,896 - build - INFO -       sellRange:[[0.03:3.37)=62.41%,[3.37:6.70)=23.79%,[-3.30:0.03)=5.86%,[6.70:10.03)=5.52%,[10.03:13.37)=1.38%,[20.03:23.37)=0.69%,[13.37:16.70)=0.34%,[min:-26.63)=0.00%,[-26.63:-23.30)=0.00%,[-23.30:-19.97)=0.00%,[-19.97:-16.63)=0.00%,[-16.63:-13.30)=0.00%,[-13.30:-9.97)=0.00%,[-9.97:-6.63)=0.00%,[-6.63:-3.30)=0.00%,[16.70:20.03)=0.00%,[23.37:max)=0.00%,]
2020-11-09 20:02:03,896 - build - INFO -       buyRange:[[-1.84:1.49)=59.66%,[-5.17:-1.84)=22.07%,[1.49:4.83)=8.62%,[-8.51:-5.17)=7.24%,[-11.84:-8.51)=1.72%,[-15.17:-11.84)=0.34%,[4.83:8.16)=0.34%,[min:-25.17)=0.00%,[-25.17:-21.84)=0.00%,[-21.84:-18.51)=0.00%,[-18.51:-15.17)=0.00%,[8.16:11.49)=0.00%,[11.49:14.83)=0.00%,[14.83:18.16)=0.00%,[18.16:21.49)=0.00%,[21.49:24.83)=0.00%,[24.83:max)=0.00%,]
2020-11-09 20:02:03,968 - build - INFO - [dime:887]: count=217,pow_rate=1.204,sCenterPct=3.70,bCenterPct=0.23
2020-11-09 20:02:03,968 - build - INFO -       sellRange:[[1.39:4.73)=59.91%,[4.73:8.06)=23.96%,[-1.94:1.39)=6.45%,[8.06:11.39)=4.61%,[11.39:14.73)=2.76%,[14.73:18.06)=1.38%,[-5.27:-1.94)=0.92%,[min:-25.27)=0.00%,[-25.27:-21.94)=0.00%,[-21.94:-18.61)=0.00%,[-18.61:-15.27)=0.00%,[-15.27:-11.94)=0.00%,[-11.94:-8.61)=0.00%,[-8.61:-5.27)=0.00%,[18.06:21.39)=0.00%,[21.39:24.73)=0.00%,[24.73:max)=0.00%,]
2020-11-09 20:02:03,968 - build - INFO -       buyRange:[[-1.04:2.29)=57.14%,[-4.38:-1.04)=18.89%,[2.29:5.62)=11.98%,[-7.71:-4.38)=7.37%,[-11.04:-7.71)=2.30%,[-14.38:-11.04)=0.92%,[5.62:8.96)=0.92%,[-17.71:-14.38)=0.46%,[min:-24.38)=0.00%,[-24.38:-21.04)=0.00%,[-21.04:-17.71)=0.00%,[8.96:12.29)=0.00%,[12.29:15.62)=0.00%,[15.62:18.96)=0.00%,[18.96:22.29)=0.00%,[22.29:25.62)=0.00%,[25.62:max)=0.00%,]


dimen:885 => count = 220,s_得分=0.862,b_得分=0.719,s_稳定性=9.246911001713286,b_稳定性=1.02100188592187,sell：正方差|负方差=17.744|17.744,buy：正方差|负方差=8.293|8.293
    量化数据情况：count = 220,s_得分=0.6318181818181818,b_得分=0.6045454545454545,sell：正方差|负方差=5.701|5.701,buy：正方差|负方差=3.294|3.294
    预测SellPct值分布情况:[[-1.67:1.67)=90.91%,[1.67:5.00)=9.09%,[-26.00:-25.00)=0.00%,[-25.00:-21.67)=0.00%,[-21.67:-18.33)=0.00%,[-18.33:-15.00)=0.00%,[-15.00:-11.67)=0.00%,[-11.67:-8.33)=0.00%,[-8.33:-5.00)=0.00%,[-5.00:-1.67)=0.00%,[5.00:8.33)=0.00%,[8.33:11.67)=0.00%,[11.67:15.00)=0.00%,[15.00:18.33)=0.00%,[18.33:21.67)=0.00%,[21.67:25.00)=0.00%,[25.00:26.00)=0.00%,]
    预测Buy_Pct值分布情况:[[-1.67:1.67)=75.00%,[-5.00:-1.67)=25.00%,[-26.00:-25.00)=0.00%,[-25.00:-21.67)=0.00%,[-21.67:-18.33)=0.00%,[-18.33:-15.00)=0.00%,[-15.00:-11.67)=0.00%,[-11.67:-8.33)=0.00%,[-8.33:-5.00)=0.00%,[1.67:5.00)=0.00%,[5.00:8.33)=0.00%,[8.33:11.67)=0.00%,[11.67:15.00)=0.00%,[15.00:18.33)=0.00%,[18.33:21.67)=0.00%,[21.67:25.00)=0.00%,[25.00:26.00)=0.00%,]
dimen:886 => count = 290,s_得分=0.697,b_得分=0.769,s_稳定性=1.2228853375353865,b_稳定性=0.5693082448690328,sell：正方差|负方差=10.922|10.922,buy：正方差|负方差=11.932|11.932
    量化数据情况：count = 290,s_得分=0.5689655172413793,b_得分=0.5896551724137931,sell：正方差|负方差=5.053|5.053,buy：正方差|负方差=4.305|4.305
    预测SellPct值分布情况:[[1.67:5.00)=74.48%,[-1.67:1.67)=25.52%,[-26.00:-25.00)=0.00%,[-25.00:-21.67)=0.00%,[-21.67:-18.33)=0.00%,[-18.33:-15.00)=0.00%,[-15.00:-11.67)=0.00%,[-11.67:-8.33)=0.00%,[-8.33:-5.00)=0.00%,[-5.00:-1.67)=0.00%,[5.00:8.33)=0.00%,[8.33:11.67)=0.00%,[11.67:15.00)=0.00%,[15.00:18.33)=0.00%,[18.33:21.67)=0.00%,[21.67:25.00)=0.00%,[25.00:26.00)=0.00%,]
    预测Buy_Pct值分布情况:[[-1.67:1.67)=98.28%,[-5.00:-1.67)=1.72%,[-26.00:-25.00)=0.00%,[-25.00:-21.67)=0.00%,[-21.67:-18.33)=0.00%,[-18.33:-15.00)=0.00%,[-15.00:-11.67)=0.00%,[-11.67:-8.33)=0.00%,[-8.33:-5.00)=0.00%,[1.67:5.00)=0.00%,[5.00:8.33)=0.00%,[8.33:11.67)=0.00%,[11.67:15.00)=0.00%,[15.00:18.33)=0.00%,[18.33:21.67)=0.00%,[21.67:25.00)=0.00%,[25.00:26.00)=0.00%,]
dimen:887 => count = 217,s_得分=0.627,b_得分=0.613,s_稳定性=1.6502488624952178,b_稳定性=0.6335059579689342,sell：正方差|负方差=10.966|10.966,buy：正方差|负方差=13.442|13.442
    量化数据情况：count = 217,s_得分=0.5898617511520737,b_得分=0.5806451612903226,sell：正方差|负方差=5.013|5.013,buy：正方差|负方差=5.432|5.432
    预测SellPct值分布情况:[[1.67:5.00)=100.00%,[-26.00:-25.00)=0.00%,[-25.00:-21.67)=0.00%,[-21.67:-18.33)=0.00%,[-18.33:-15.00)=0.00%,[-15.00:-11.67)=0.00%,[-11.67:-8.33)=0.00%,[-8.33:-5.00)=0.00%,[-5.00:-1.67)=0.00%,[-1.67:1.67)=0.00%,[5.00:8.33)=0.00%,[8.33:11.67)=0.00%,[11.67:15.00)=0.00%,[15.00:18.33)=0.00%,[18.33:21.67)=0.00%,[21.67:25.00)=0.00%,[25.00:26.00)=0.00%,]
    预测Buy_Pct值分布情况:[[-1.67:1.67)=95.39%,[1.67:5.00)=4.61%,[-26.00:-25.00)=0.00%,[-25.00:-21.67)=0.00%,[-21.67:-18.33)=0.00%,[-18.33:-15.00)=0.00%,[-15.00:-11.67)=0.00%,[-11.67:-8.33)=0.00%,[-8.33:-5.00)=0.00%,[-5.00:-1.67)=0.00%,[5.00:8.33)=0.00%,[8.33:11.67)=0.00%,[11.67:15.00)=0.00%,[15.00:18.33)=0.00%,[18.33:21.67)=0.00%,[21.67:25.00)=0.00%,[25.00:26.00)=0.00%,]
【总体】: s得分:0.73[+22.08%],b得分:0.70[+18.38%],s_pct能力:3.50,b_pct能力:1.32,s稳定性:4.04,b稳定性0.74

[CoreEngineImpl]: [887]=>count:59(sScore:69.491,bScore:64.406),做多:[交易率:42.37%,成功率:32.00%,盈利率:52.00%,单均pct:-1.32,盈pct:2.62(3.37),亏pct:-5.59(-14.81)],做空:[交易率:0.00%,成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[CoreEngineImpl]: [886]=>count:65(sScore:64.615,bScore:67.692),做多:[交易率:55.38%,成功率:52.78%,盈利率:75.00%,单均pct:0.96,盈pct:2.22(4.96),亏pct:-2.82(-11.78)],做空:[交易率:0.00%,成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]
[CoreEngineImpl]: [885]=>count:33(sScore:96.969,bScore:57.575),做多:[交易率:45.45%,成功率:80.00%,盈利率:80.00%,单均pct:0.42,盈pct:0.61(3.44),亏pct:-0.33(-0.80)],做空:[交易率:0.00%,成功率:0.00%,盈利率:0.00%,单均pct:0.00,盈pct:0.00(0.00),亏pct:0.00(0.00)]

    
    """

    pass

if __name__ == "__main__":
    #analysicQuantDataOnly()
    runBackTest()

    """
    动量指标：
    
    策略：
        收集arron_up>arron_down,且arron_up大于50的数据对象。
    """





