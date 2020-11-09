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

class DI_ZZ500_EngineModel(CoreEngineModel):

    PREDICT_LENGT = 4
    PCT_MAX_LIMIT = 99999999

    def __init__(self):
        self.kdjEncoder = FloatEncoder([15,30,45,60,75,90])

    def getPctEncoder1(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-15,25.5, 40/20)), minValue=-26, maxValue=26)

    def getPctEncoder2(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-14.5, 26, 40 / 20)), minValue=-25, maxValue=27)

    def onCollectStart(self, code: str) -> bool:
        from earnmi.chart.Indicator import Indicator
        self.indicator = Indicator(34)
        self.lasted15Bar = np.full(15, None)
        #self.lasted3BarKdj = np.full(3, None)
        #self.lasted3BarArron = np.full(3, None)
        self.code = code
        return True

    def _computeIsHold(self):
        #{'period': 14, 'di_dist': 40, 'max_p_id': 75}
        p_di = self.indicator.plus_di(14,array=True)
        m_di = self.indicator.minus_di(14,array=True)
        k, d, j = self.indicator.kdj(fast_period=9, slow_period=3, array=True)
        # dif, dea, macd = indicator.macd(fast_period=12, slow_period=26, signal_period=9)
        holdDay = 0
        for i in range(-1, -11, -1):
            isHold = k[i] >= d[i] and p_di[i] - m_di[i] >=15
            if not isHold:
                break
            holdDay += 1
        return holdDay

    def onCollectTrace(self, bar: BarData) -> CollectData:
        if not BarUtils.isOpen(bar):
            return None
        self.indicator.update_bar(bar)
        self.lasted15Bar[:-1] = self.lasted15Bar[1:]
        #k, d, j = self.indicator.kdj(fast_period=9, slow_period=3)
        #aroon_down,aroon_up = self.indicator.aroon( n=14)
        self.lasted15Bar[-1] = bar
        if self.indicator.count <=34:
            return None
        hold_day = self._computeIsHold()
        if hold_day < 2:
            return None

        dif, dea, macd = self.indicator.macd( fast_period=12,slow_period = 26,signal_period = 9)
        p_di = self.indicator.plus_di(14, array=False)
        m_di = self.indicator.minus_di(14, array=False)
        k, d, j = self.indicator.kdj(fast_period=9, slow_period=3)

        ##生成维度值
        dimen = Dimension(type=TYPE_2KAGO1, value=1)
        collectData = CollectData(dimen=dimen)
        collectData.occurBars = list(self.lasted15Bar[-3:])

        collectData.occurExtra['hold_day'] = hold_day - 4
        collectData.occurExtra['macd_dif'] = dif
        collectData.occurExtra['macd_macd'] = macd
        collectData.occurExtra['p_di'] = p_di
        collectData.occurExtra['m_di'] = m_di
        collectData.occurExtra['atr'] = self.indicator.atr(14)
        collectData.occurExtra['k'] = k
        collectData.occurExtra['j'] = j


        #收集对象的有效性:无要求
        collectData.setValid(True)
        return collectData

    def onCollect(self, data: CollectData, newBar: BarData) :
        if not BarUtils.isOpen(newBar):
            return
        #不含停牌数据
        data.predictBars.append(newBar)
        size = len(data.predictBars)
        holdDay = self._computeIsHold()
        if holdDay < 1:
            data.setFinished()
        if size >= DI_ZZ500_EngineModel.PREDICT_LENGT:
            data.setFinished()

    def getYBasePrice(self, cData: CollectData) -> float:
        ## 金叉形成后的前一天
        return cData.occurBars[-1].close_price

    def getYLabelPct(self, cData:CollectData)->[float, float]:
        if len(cData.predictBars) < 1:
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

    def generateXFeature(self, cData: CollectData) -> []:
        #保证len等于三，要不然就不能作为生成特征值。
        if (len(cData.occurBars) < 3):
            return None
        data = []
        data.append(cData.occurExtra['hold_day'])
        data.append(cData.occurExtra['macd_dif'])
        data.append(cData.occurExtra['macd_macd'])
        data.append(cData.occurExtra['p_di'])
        data.append(cData.occurExtra['m_di'])
        data.append(cData.occurExtra['atr'])
        data.append(cData.occurExtra['k'])
        data.append(cData.occurExtra['j'])

        basePrcie = cData.occurBars[-2].close_price
        def getSellBuyPct(bar: BarData):
            s_pct = 100 * ((bar.high_price + bar.close_price) / 2 - basePrcie) / basePrcie
            b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrcie) / basePrcie
            return s_pct, b_pct

        s_pct, b_pc = getSellBuyPct(cData.occurBars[-1])
        data.append(s_pct)
        data.append(b_pc)
        return data

    """
        优化特征。（主要去重）
        """

    """
    优化特征。（主要去重）
    """

    def optimize(self, x_feature: [], y_sell_1: [], y_buy_1: [], y_sell_2: [], y_buy_2: []):

        x_size = len(x_feature)
        y_list = []
        for i in range(0,len(x_feature[0])):
            y = np.full(x_size,None)
            for j in range(0,x_size):
                y[j] = x_feature[j][i]
            y_list.append(y)

        ##给每个特征编码。
        y_Encoder_list = np.full(len(y_list),None)
        for i in range(0,len(y_list)):
            y = y_list[i]
            _min = y.min()
            _max = y.max()
            split_size = (_max - _min) / 10
            y_Encoder_list[i] = FloatEncoder(list(np.arange(_min,_max, split_size)), minValue=_min, maxValue=_max)

        @dataclass()
        class Y_FEATURE:
            x_feature: []  ##X特征值
            def __eq__(self, o: object) -> bool:
                return self.x_feature.__eq__(o.x_feature)

            def __hash__(self) -> int:
                h = 1
                for x in self.x_feature:
                    h = h * x
                return hash(h)

        @dataclass()
        class Y_LABEL:
            y_sell_1:int
            y_buy_1:int
            y_sell_2:int
            y_buy_2:int
            y:int

        featureMap = {}
        for i in range(0,x_size):
            y = x_feature[i]
            for j in range(0,len(y)):
                y[j] = y_Encoder_list[j].encode(y[j])
            y_feature = Y_FEATURE(x_feature=y)
            y_label =  Y_LABEL(y_sell_1= y_sell_1[i],y_buy_1=y_buy_1[i],y_sell_2=y_buy_1[i],y_buy_2 = y_buy_2[i],y = y_sell_1[i])
            y_label_list = featureMap.get(y_feature)
            if y_label_list is None:
                y_label_list = []
                featureMap[y_feature] = y_label_list
            y_label_list.append(y_label)

        ##开始去重:多个相同的x特征对应多个y
        x_feature_new = []
        y_sell_1_new = []
        y_buy_1_new = []
        y_sell_2_new = []
        y_buy_2_new = []
        for y_feature,y_label_list in featureMap.items():
           y_label:Y_LABEL = self.unique_y_label(y_label_list)
           x_feature_new.append(y_feature.x_feature)
           y_sell_1_new.append(y_label.y_sell_1)
           y_buy_1_new.append(y_label.y_buy_1)
           y_sell_2_new.append(y_label.y_sell_2)
           y_buy_2_new.append(y_label.y_buy_2)
        return np.array(x_feature_new), np.array(y_sell_1_new), np.array(y_buy_1_new), np.array(y_sell_2_new), np.array(y_buy_2_new)

    def unique_y_label(self,y_label_list):
        ###每次删除差异最大的那个
        while len(y_label_list) > 2:
            y_list = []
            for i in range(0, len(y_label_list)):
                y_list.append(y_label_list[i].y)
            y = np.array(y_list)
            avg = y.mean()
            max_index = 0
            max_dist = abs(y[0]-avg)
            for i in range(1,len(y_list)):
                dist = abs(y[i]-avg)
                if dist > max_dist:
                    max_dist = dist
                    max_index = i
            del y_label_list[max_index]
        assert len(y_label_list) < 3
        return y_label_list[0]




def analysicQuantDataOnly():
    dirName = "models/skdj_analysic_quantdata"
    start = datetime(2015, 10, 1)
    end = datetime(2019, 10, 1)

    souces = ZZ500DataSource(start, end)
    model = DI_ZZ500_EngineModel()
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
    _dirName = "models/di_zz500_runbacktest"
    start = datetime(2015, 10, 1)
    middle = datetime(2019, 9, 30)
    end = datetime(2020, 9, 30)
    historySource = ZZ500DataSource(start, middle)
    futureSouce = ZZ500DataSource(middle, end)


    model = DI_ZZ500_EngineModel()
    #strategy = DefaultStrategy()
    strategy = CommonStrategy()
    create = False
    engine = None
    if create:
        engine = CoreEngine.create(_dirName, model,historySource,min_size=200,useSVM=False)
    else:
        engine = CoreEngine.load(_dirName,model)
    runner = CoreEngineRunner(engine)

    strategy.sell_leve_pct_bottom = 1
    runner.backtest(futureSouce, strategy)
    #
    # class MyStrategy(CommonStrategy):
    #     DIMEN = [107,
    #              93,92,100,64,57,99]
    #     def isSupport(self, engine: CoreEngine, dimen: Dimension) -> bool:
    #         # if dimen.value == 99:
    #         #     return True
    #         # abilityData =  engine.queryPredictAbilityData(dimen);
    #         # if abilityData.getScoreSell() < 0.72:
    #         #     return False
    #         return True
    # strategy = MyStrategy()
    # params = {
    #     'buy_offset_pct': [None, 1, -1],
    #     'sell_offset_pct': [None, -2,-1, 0],
    #     'sell_leve_pct_top': [None,1,2,3],
    #     'sell_leve_pct_bottom': [None,  -1, 1,2,3],
    # }
    #
    # def data_cmp(o1, o2):
    #     deal_rate1 = o1.longData.deal_rate(o1.count)
    #     deal_rate2 = o2.longData.deal_rate(o2.count)
    #     if deal_rate1 < 0.1 and deal_rate2 < 0.1:
    #         return o1.longData.total_pct_avg() - o2.longData.total_pct_avg()
    #     if deal_rate1 < 0.1:
    #         return -1
    #     if deal_rate2 < 0.1:
    #         return 1
    #     return o1.longData.total_pct_avg() - o2.longData.total_pct_avg()
    # runner.debugBestParam(futureSouce, strategy,params,backtest_data_cmp=data_cmp)

    pass


def printLaststTops():
    _dirName = "models/di_zz500_last_top"

    model = DI_ZZ500_EngineModel()
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






