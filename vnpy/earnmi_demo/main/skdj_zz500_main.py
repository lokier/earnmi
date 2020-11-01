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

class SKDJ_EngineModel(CoreEngineModel):

    PREDICT_LENGT = 3
    PCT_MAX_LIMIT = 99999999

    def __init__(self):
        self.lasted15Bar = np.full(15,None)
        self.lasted3BarKdj = np.full(3,None)
        self.lasted3BarMacd = np.full(3,None)
        self.lasted3BarArron = np.full(3,None)
        self.kdjEncoder = FloatEncoder([15,30,45,60,75,90])

    def getPctEncoder1(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-25,25.5, 50/20)), minValue=-26, maxValue=26)

    def getPctEncoder2(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-24.5, 27, 50 /20)), minValue=-25, maxValue=27)

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

        # 最近15天之内不含停牌数据
        if not BarUtils.isAllOpen(self.lasted15Bar):
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
        goldBar:BarData = self.lasted15Bar[-2]
        goldBarMacd = self.lasted3BarMacd[2];
        gold_dif_factory,gold_dea_factory = [ 100*goldBarMacd[0]/goldBar.close_price, 100*goldBarMacd[1]/goldBar.close_price]

        ##生成维度值
        verbute = Factory.vibrate(self.indicator.close,self.indicator.open,period=12)
        kPatternValue = self.makePatthernValue(verbute,gold_dif_factory,gold_dea_factory);

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

        #收集对象的有效性:无要求
        collectData.setValid(True)
        return collectData

    ENCODE1 = FloatEncoder([1,8,20,45,80]);
    ENCODE2 = FloatEncoder([-1,0,1,2.2,4.7]);

    def makePatthernValue(self,verbute, dif,dea):
        #mask1 = KDJMovementEngineModel.ENCODE1.mask()
        mask2 = SKDJ_EngineModel.ENCODE2.mask()
        v1 = SKDJ_EngineModel.ENCODE1.encode(verbute)
        v2 = SKDJ_EngineModel.ENCODE2.encode(dif)
        v3 = SKDJ_EngineModel.ENCODE2.encode(dea)
        return v1 * mask2 * mask2 + v2 * mask2 +v3;

    def onCollect(self, data: CollectData, newBar: BarData) :
        #不含停牌数据
        data.predictBars.append(newBar)
        size = len(data.predictBars)
        if size >= SKDJ_EngineModel.PREDICT_LENGT:
            data.setValid(BarUtils.isAllOpen(data.predictBars))
            data.setFinished()

    def getYBasePrice(self, cData: CollectData) -> float:
        ## 金叉形成后的前一天
        return cData.occurBars[-3].close_price

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


class DefaultStrategy(CoreEngineStrategy):

    def __init__(self):
        self.failBuyBar = None
        pass

    def isSupport(self, engine: CoreEngine, dimen:Dimension)->bool:
        abilityData = engine.queryPredictAbilityData(dimen)
        if abilityData.getScoreSell() < 0.72:
            return False
        return True

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
        buy_offset_pct = 0
        min_allow_buy_day = 2  #可以买入的交易天数

        suggestSellPrice = order.suggestSellPrice
        suggestBuyPrice = order.suggestBuyPrice * (1 + buy_offset_pct /100)
        if (order.status == PredictOrderStatus.HOLD):

            if order.isOverHighPrice:
                ##止损、止盈操作，第二天开盘价卖出
                order.sellPrice = bar.open_price
                return 4
            if bar.high_price >= suggestSellPrice:
                order.sellPrice = suggestSellPrice
                return 3
            if order.durationDay >= SKDJ_EngineModel.PREDICT_LENGT:
                order.sellPrice = bar.close_price
                return 4
        elif order.status == PredictOrderStatus.READY:
            if order.durationDay > min_allow_buy_day:
                #超过买入交易时间天数，废弃
                return 5
            ##这天观察走势,且当天high_price 不能超过预测卖出价
            #这里有个坑，
            # 1、如果当天是超过卖出价之后再跌到买入价，  这时第二天就要考虑止损
            # 2、如果是到底买入价之后的当天马上涨到卖出价，这时第二天就要考虑止盈
            #不管是那种情况，反正第二天就卖出。
            if suggestBuyPrice >= bar.low_price :
                ##趋势形成的第二天买入。
                order.buyPrice = suggestBuyPrice
                order.isOverHighPrice = bar.high_price >= suggestSellPrice
                return 1
        return 0



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

def runBackTest():
    _dirName = "models/skdj_zz500_runbacktest"
    start = datetime(2015, 10, 1)
    middle = datetime(2019, 9, 30)
    end = datetime(2020, 9, 30)
    historySource = ZZ500DataSource(start, middle)
    futureSouce = ZZ500DataSource(middle, end)

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

    model = SKDJ_EngineModelV2()
    strategy = DefaultStrategy()
    #strategy = BestStrategy()
    create = False
    engine = None
    if create:
        engine = CoreEngine.create(_dirName, model,historySource,min_size=200,useSVM=False)
    else:
        engine = CoreEngine.load(_dirName,model)
    runner = CoreEngineRunner(engine)
    runner.backtest(futureSouce, strategy, min_deal_count=-1)
    #params = {'buyDay':[0,1,2,3]}
    #runner.debugBestParam(futureSouce, MyStrategy(),params, min_deal_count=-1)


    pass

def printLaststTops():
    _dirName = "models/kdj_movement_lastesd_top"

    model = SKDJ_EngineModel()
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





