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
from earnmi.chart.KPattern2 import KPattern

class ObvWave_EngineModel(CoreEngineModel):

    PREDICT_LENGT = 3
    PCT_MAX_LIMIT = 99999999

    FLOAT_ENCOLDE = FloatEncoder([0, 2, 4, 6, 8, 10, 15, 25,35,], minValue=-1, maxValue=100)

    def __init__(self):
        self.kdjEncoder = FloatEncoder([15,30,45,60,75,90])

    def getPctEncoder1(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-25,25.5, 50/20)), minValue=-26, maxValue=26)

    def getPctEncoder2(self)->FloatEncoder:
        return FloatEncoder(list(np.arange(-24.5, 27, 50 /20)), minValue=-25, maxValue=27)

    def onCollectStart(self, code: str) -> bool:
        from earnmi.chart.Indicator import Indicator
        self.indicator = Indicator(35)
        self.lasted15Bar = np.full(15, None)

        self.code = code
        return True

    def getPctFeature(self,peroid,bars):
        base_price = bars[-peroid-1].close_price
        high_price = bars[-peroid].high_price
        low_price = bars[-peroid].low_price
        close_price = bars[-1].close_price
        for i in  range(-peroid+1,0):
            bar:BarData = bars[i]
            high_price = max(high_price,bar.high_price)
            low_price = min(low_price,bar.low_price)
        return  100 * (high_price - low_price) / base_price, 100 * (close_price-base_price)/base_price

    def onCollectTrace(self, bar: BarData) -> CollectData:
        if (not BarUtils.isOpen(bar)):
            return None
        self.lasted15Bar[:-1] = self.lasted15Bar[1:]
        self.lasted15Bar[-1] = bar
        self.indicator.update_bar(bar)

        # 最近15天之内不含停牌数据
        # if not BarUtils.isAllOpen(self.lasted15Bar):
        #     return None
        if not self.indicator.inited:
            return None
        wave_down, wave_up = Factory.obv_wave(33, self.indicator.close, self.indicator.high, self.indicator.low, self.indicator.volume)
        encdoe = ObvWave_EngineModel.FLOAT_ENCOLDE.encode(wave_down) * 10 +ObvWave_EngineModel.FLOAT_ENCOLDE.encode(wave_up)
        ##生成维度值
        dimen = Dimension(type=TYPE_2KAGO1, value=encdoe)
        collectData = CollectData(dimen=dimen)
        collectData.occurBars = list(self.lasted15Bar[-3:])
        collectData.occurExtra['wave_up'] = wave_up
        collectData.occurExtra['wave_down'] =  wave_down
        pct_atr1,pct_close1 = self.getPctFeature(1,self.lasted15Bar)
        pct_atr3,pct_close3 = self.getPctFeature(3,self.lasted15Bar)
        pct_atr9,pct_close9 = self.getPctFeature(9,self.lasted15Bar)
        collectData.occurExtra['pct_atr1'] = pct_atr1
        collectData.occurExtra['pct_close1'] = pct_close1
        collectData.occurExtra['pct_atr3'] = pct_atr3
        collectData.occurExtra['pct_close3'] = pct_close3
        collectData.occurExtra['pct_atr9'] = pct_atr9
        collectData.occurExtra['pct_close9'] = pct_close9
        #收集对象的有效性:无要求
        collectData.setValid(True)
        return collectData

    def onCollect(self, data: CollectData, newBar: BarData) :
        if (not BarUtils.isOpen(newBar)):
            return
        #不含停牌数据
        data.predictBars.append(newBar)
        size = len(data.predictBars)
        if size >= 3:
            data.setFinished()

    def getYBasePrice(self, cData: CollectData) -> float:
        ## 金叉形成后的前一天
        return cData.occurBars[-1].close_price

    def getYLabelPct(self, cData:CollectData)->[float, float]:
        if len(cData.predictBars) < 3:
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

    def isSupportBuildPredictModel(self, engine, dimen: Dimension) -> bool:
        qData:QuantData = engine.queryQuantData(dimen);
        if qData.sellCenterPct + qData.buyCenterPct <=0:
            return False
        if qData.count >5000:
            return False
        if qData.count < 500:
            return False
        return True

    def generateXFeature(self, cData: CollectData) -> []:
        #保证len等于三，要不然就不能作为生成特征值。
        if (len(cData.occurBars) < 3):
            return None
        data = []
        data.append(cData.occurExtra['wave_up'])
        data.append(cData.occurExtra['wave_down'])
        data.append(cData.occurExtra['pct_atr1'])
        data.append(cData.occurExtra['pct_close1'])
        data.append(cData.occurExtra['pct_atr3'])
        data.append(cData.occurExtra['pct_close3'])
        data.append(cData.occurExtra['pct_atr9'])
        data.append(cData.occurExtra['pct_close9'])
        return data


def analysicQuantDataOnly():
    dirName = "models/obv_analysic_quantdata"
    start = datetime(2015, 10, 1)
    end = datetime(2019, 10, 1)

    souces = ZZ500DataSource(start, end)
    model = ObvWave_EngineModel()
    create = True
    engine = None
    if create:
        engine = CoreEngine.create(dirName, model,souces,build_quant_data_only = True,min_size=200)
    else:
        engine = CoreEngine.load(dirName,model)
        #engine.buildQuantData()
    engine.buildPredictModel(useSVM=False)
    pass





def runBackTest():
    _dirName = "models/obv_wave_zz500_runbacktest"
    start = datetime(2015, 10, 1)
    middle = datetime(2019, 9, 30)
    end = datetime(2020, 9, 30)
    historySource = ZZ500DataSource(start, middle)
    futureSouce = ZZ500DataSource(middle, end)


    model = ObvWave_EngineModel()

    class MyStrategy(CommonStrategy):
        DIMEN = [37,
                 66, 36, 46, 26, 55, 27,77]
        # def isSupport(self, engine: CoreEngine, dimen: Dimension) -> bool:
        #     if dimen.value == 37:
        #         return True
        #     return False

    strategy = MyStrategy()
    create = False
    engine = None
    if create:
        engine = CoreEngine.create(_dirName, model,historySource,min_size=200,useSVM=False)
    else:
        engine = CoreEngine.load(_dirName,model)
    runner = CoreEngineRunner(engine)
    #runner.backtest(futureSouce, strategy)
    params = {
        'buy_offset_pct': [None, -2,-1,1],
        'sell_offset_pct': [None,  -1,1],
        #'sell_leve_pct_top': [None,  1, 2,],
        'sell_leve_pct_bottom': [0,   1,2,3],
    }
    runner.debugBestParam(futureSouce, strategy,params)
    pass


def printLaststTops():
    _dirName = "models/obv_wave_zz500_last_top"

    model = ObvWave_EngineModel()
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

    # params: {'buy_offset_pct': None, 'sell_offset_pct': None, 'sell_leve_pct_top': 2, 'sell_leve_pct_bottom': 1}
    # [27] = > count: 418(sScore:77.511, bScore: 68.181), 做多: [
    #     交易率:37.08 %, 成功率: 62.58 %, 盈利率: 76.77 %, 单均pct: 0.91, 盈pct: 2.40(8.02), 亏pct: -4.01(-10.00)], 做空: [
    #     交易率:0.00 %, 成功率: 0.00 %, 盈利率: 0.00 %, 单均pct: 0.00, 盈pct: 0.00(0.00), 亏pct: 0.00(0.00)]
    class MyStrategy(CommonStrategy):
        def isSupport(self, engine: CoreEngine, dimen: Dimension) -> bool:
            if dimen.value == 27:
                return True
            return False
    strategy = MyStrategy()
    strategy.sell_leve_pct_top =2
    strategy.sell_leve_pct_bottom = 1

    runner.printZZ500Tops(strategy)

    pass

if __name__ == "__main__":
    #analysicQuantDataOnly()
    #runBackTest()


    printLaststTops()






