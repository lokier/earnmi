from datetime import datetime, timedelta
from functools import cmp_to_key
from typing import Sequence, List

import pandas as pd
import numpy as np
import sklearn
from sklearn import model_selection
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
import pickle

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, IndicatorItem, Signal
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
from earnmi.chart.Indicator import Indicator


class ASignal:

    def __init__(self,period,up,down):
        self.period = period
        self.up = up
        self.down = down
        self.indicator = Indicator(period+3)

    def clone(self):
        a = ASignal(self.period,self.up,self.down)
        a.indicator = self.indicator.clone()
        return a

    def isInited(self):
        return self.indicator.inited

    def update_bar(self,bar):
        self.indicator.update_bar(bar)
        aroon_down, aroon_up = self.indicator.aroon(self.period, True)
        self.aroon_down = aroon_down
        self.aroon_up = aroon_up

    def getAroonDown(self):
        return self.aroon_down[-1]
    def getAroonUp(self):
        return self.aroon_up[-1]

    def isOccurFirst(self):
        match1 = self.match(self.aroon_down[-2], self.aroon_up[-2])
        match2 = self.match(self.aroon_down[-1], self.aroon_up[-1])
        return match1 == False and match2 == True

    def isOccurNow(self):
        return self.match(self.aroon_down[-1],self.aroon_up[-1])

    def match(self,aroon_down,aroon_up):
        return aroon_up>=self.up and aroon_down<=self.down



class AsignalModel(CoreEngineModel):


    def __init__(self):
        pass

    def onCollectStart(self, code: str) -> bool:
        self.indicator = Indicator(34)
        self.aSignal = ASignal(20,70,30)
        self.code = code
        self.lastedBars = np.full(20,None)

        return True

    def getPctEncoder1(self)->FloatEncoder:
        return FloatEncoder([-12, -5, 0, 5, 12], minValue=-20, maxValue=20)

    def onCollectTrace(self, bar: BarData) -> CollectData:
        self.indicator.update_bar(bar)
        self.aSignal.update_bar(bar)
        self.lastedBars[:-1] = self.lastedBars[1:]
        self.lastedBars[-1] = bar

        # 最近20天之内不含停牌数据
        # if not BarUtils.isAllOpen(self.lasted20Bar):
        #     return None
        if not self.aSignal.isInited():
            return None

        if not self.aSignal.isOccurFirst():
            return None

        dimen = Dimension(type=TYPE_2KAGO1, value=1)
        collectData = CollectData(dimen=dimen)
        collectData.occurBars = self.lastedBars
        assert collectData.occurBars is self.lastedBars
        collectData.occurBars = list(self.lastedBars)
        assert not collectData.occurBars is self.lastedBars
        assert len(collectData.occurBars) == len(self.lastedBars)


        collectData.setValid(False)
        return collectData

    def onCollect(self, data: CollectData, newBar: BarData) :

        if  self.aSignal.isOccurNow():
            down ,up =  self.indicator.aroon(20)
            assert  self.aSignal.match(down,up)
            data.setValid(True)
            data.predictBars.append(newBar)
        else:
            data.extraBars = []
            data.extraBars.append(newBar)
            data.setFinished()

    def getYBasePrice(self, cData: CollectData) -> float:
        ## 金叉形成后的前一天
        return cData.occurBars[-1].close_price

    def getYLabelPct(self, cData:CollectData)->[float, float]:

        # basePrice = self.getYBasePrice(cData)
        # assert len(cData.predictBars) > 0
        # pct = 100 * (cData.predictBars[-1].close_price - basePrice) /basePrice
        # return pct, pct
        basePrice = self.getYBasePrice(cData)
        sell_pct = -99999999
        buy_pct = -sell_pct
        sell_day = 0
        for i in range(0, len(cData.predictBars)):
            bar: BarData = cData.predictBars[i]
            _s_pct = 100 * ((bar.high_price + bar.close_price) / 2 - basePrice) / basePrice
            _b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrice) / basePrice
            if _s_pct > sell_pct:
                sell_pct = _s_pct
                sell_day = i
            buy_pct = min(_b_pct, buy_pct)
        cData.sell_day = sell_day
        return sell_pct, buy_pct


    def generateXFeature(self, cData: CollectData) -> []:
        data = []
        return data


"""
 RSI指标
"""
class aSignalAroon(IndicatorItem):

    def __init__(self):
        super().__init__(False)

    def getNames(self) -> List:
        return [
            "up",
               "down",
                "1",
                "2",
                ];
        #return ["osi3"];

    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        values["1"] = 70;
        values["2"] = 30;
        if indicator.count>22 :

            down,up = indicator.aroon(20)
            if up >= 70 and down <= 30:
                signal.buy = True

            values["up"] = up
            values["down"] = down
            #values["osi1"] = 0
        else:
            values["up"] = 50
            values["down"] = 50
        return values

    def getColor(self, name: str):
        if name == "1":
            return 'r'
        elif name == '2':
            return 'b'
        elif name == 'up':
            return 'black'
        return 'y'

def analysicQuantDataOnly():
    _dirName = "models/sSignal_zz500"
    start = datetime(2018, 10, 1)
    middle = datetime(2019, 9, 30)
    end = datetime(2020, 9, 30)
    #historySource = ZZ500DataSource(start, middle)
    #futureSouce = ZZ500DataSource(middle, end)
    source = ZZ500DataSource(start, end)

    model = AsignalModel()
    create = True
    engine = None
    if create:
        engine = CoreEngine.create(_dirName, model,source,build_quant_data_only = True,min_size=200)
    else:
        engine = CoreEngine.load(_dirName,model)

    dimen = Dimension(type=TYPE_2KAGO1, value=1)


    cDataList = engine.loadCollectData(dimen)
    day_value = []
    sell_day_value = []

    chart = Chart()
    chart_count = 0
    for i in range(0,len(cDataList)):
        cData:CollectData = cDataList[i];
        day_value.append(len(cData.predictBars))
        sell_day_value.append(cData.sell_day)

        # bars = cData.occurBars + cData.predictBars + cData.extraBars
        # bar = bars[-1]
        # if bars[-1].symbol == '000028.XSHE':
        #     print("wwhy")
        # chart.show(bars, item = aSignalAroon(),savefig=f'models/files/{bars[-1].symbol}_{bar.datetime.year}_{bar.datetime.month}_{bar.datetime.day}.png')
        #
        # chart_count +=1
        # if chart_count > 50:
        #     print(f"wwhy")
        #     break

    dayEncoder = FloatEncoder(list(np.arange(0,15,2)))
    print(f"    分布:{FloatRange2.toStr(dayEncoder.computeValueDisbustion(day_value), dayEncoder)}")
    print(f"    分布:{FloatRange2.toStr(dayEncoder.computeValueDisbustion(sell_day_value), dayEncoder)}")
    day_value = np.array(day_value)
    sell_day_value = np.array(sell_day_value)

    print(f"   avg:{day_value.mean()}")
    print(f"   sell:{sell_day_value.mean()}")

    pass

# def analysic():
#     start = datetime(2018, 10, 1)
#     middle = datetime(2019, 9, 30)
#     end = datetime(2020, 9, 30)
#     # historySource = ZZ500DataSource(start, middle)
#     # futureSouce = ZZ500DataSource(middle, end)
#     source = ZZ500DataSource(start, end)
#     CoreEngineModel.onCollect()

if __name__ == "__main__":
    analysicQuantDataOnly()






