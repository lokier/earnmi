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


from earnmi.data.SWImpl import SWImpl
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.CoreEngineRunner import CoreEngineRunner
from earnmi.model.CoreEngineStrategy import CoreEngineStrategy
from earnmi.model.PredictData2 import PredictData
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
from earnmi.model.CoreEngine import CoreEngine, BarDataSource,PredictModel
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.Dimension import Dimension, TYPE_2KAGO1
from earnmi.model.PredictData import PredictData
from earnmi.model.PredictOrder import PredictOrder, PredictOrderStatus
from earnmi.model.QuantData import QuantData
from earnmi.model.CoreEngineModel import CoreEngineModel
from vnpy.trader.object import BarData
import numpy as np
import pandas as pd

class EngineModel2KAlgo2(CoreEngineModel):

    def __init__(self):
        self.lasted3Bar = np.array([None ,None ,None])
        self.lasted3BarKdj = np.array([None ,None ,None])
        self.kdjEncoder = FloatEncoder([15,30,45,60,75,90])
        self.sw = SWImpl()

    def onCollectStart(self, code: str) -> bool:
        from earnmi.chart.Indicator import Indicator
        self.indicator = Indicator(40)
        self.code = code
        return True

    def onCollectTrace(self, bar: BarData) -> CollectData:
        self.indicator.update_bar(bar)
        self.lasted3Bar[:-1] = self.lasted3Bar[1:]
        self.lasted3BarKdj[:-1] = self.lasted3BarKdj[1:]
        k, d, j = self.indicator.kdj(fast_period=9, slow_period=3)
        self.lasted3Bar[-1] = bar
        self.lasted3BarKdj[-1] = [k, d, j]
        if self.indicator.count >=20:
            from earnmi.chart.KPattern import KPattern
            kPatternValue = KPattern.encode2KAgo1(self.indicator)
            if not kPatternValue is None :

                _kdj_mask = self.kdjEncoder.mask()
                kPatternValue = kPatternValue * _kdj_mask* _kdj_mask + self.kdjEncoder.encode(k) * _kdj_mask + self.kdjEncoder.encode(d)

                dimen = Dimension(type=TYPE_2KAGO1 ,value=kPatternValue)
                collectData = CollectData(dimen=dimen)
                collectData.occurBars.append(self.lasted3Bar[-2])
                collectData.occurBars.append(self.lasted3Bar[-1])

                collectData.occurKdj.append(self.lasted3BarKdj[-2])
                collectData.occurKdj.append(self.lasted3BarKdj[-1])

                return collectData
        return None

    def onCollect(self, data: CollectData, newBar: BarData) -> bool:
        if len(data.occurBars) < 3:
            data.occurBars.append(self.lasted3Bar[-1])
            data.occurKdj.append(self.lasted3BarKdj[-1])
        else:
            data.predictBars.append(newBar)
        size = len(data.predictBars)
        return size >= 2


    @abstractmethod
    def getYLabelPrice(self, cData:CollectData)->[float, float, float]:
        bars: ['BarData'] = cData.predictBars
        if len(bars) > 0:
            sell_price = -9999999999
            buy_price = - sell_price
            for bar in bars:
                sell_price = max((bar.high_price + bar.close_price) / 2,sell_price)
                buy_price = min((bar.low_price + bar.close_price) / 2,buy_price)
            return sell_price,buy_price
        return None,None

    def getYBasePrice(self, cData:CollectData)->float:
        return cData.occurBars[-2].close_price

    def generateXFeature(self, cData: CollectData) -> []:
        #保证len小于三，要不然就不能作为生成特征值。
        if(len(cData.occurBars) < 3):
            return None
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

if __name__ == "__main__":



    dirName = "models/sw_sample_model_analysis"
    trainDataSouce = SWDataSource(start=datetime(2014, 2, 1), end=datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1), datetime(2020, 9, 1))

    model = EngineModel2KAlgo2()
    #engine = CoreEngine.create(dirName,model,trainDataSouce,limit_dimen_size=99999999)
    engine = CoreEngine.load(dirName, model)
    runner = CoreEngineRunner(engine)
    strategy = MyStrategy()
    pdData = runner.backtest(testDataSouce, strategy, min_deal_count=15)

    writer = pd.ExcelWriter('models\output.xlsx')
    pdData.to_excel(writer, sheet_name="data", index=False)
    writer.save()
    writer.close()