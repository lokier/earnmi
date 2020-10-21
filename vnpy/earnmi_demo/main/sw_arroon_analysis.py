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

class TheEngineModel(CoreEngineModel):

    def __init__(self):
        self.lasted3Bar = np.array([None ,None ,None])
        self.lasted3BarKdj = np.array([None ,None ,None])
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
        self.lasted3Bar[:-1] = self.lasted3Bar[1:]
        self.lasted3BarKdj[:-1] = self.lasted3BarKdj[1:]
        k, d, j = self.indicator.kdj(fast_period=9, slow_period=3)
        self.lasted3Bar[-1] = bar
        self.lasted3BarKdj[-1] = [k, d, j]
        timeKey = utils.to_start_date(bar.datetime);
        if self.mDateOccurCountMap.get(timeKey) is None:
            self.mDateOccurCountMap[timeKey] = 0

        if self.indicator.count >=30:
            aroon_down,aroon_up = self.indicator.aroon(n=14, array=False)
            from earnmi.chart.KPattern import KPattern
            if  aroon_up < aroon_down or aroon_up < 50:
                return None
            kPatternValue = KPattern.encode2KAgo1(self.indicator)
            if not kPatternValue is None :
                self.mDateOccurCountMap[timeKey] +=1

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
        predict_sell_pct = predict.getPredictSellPct(engine.getEngineModel())
        predict_buy_pct = predict.getPredictBuyPct(engine.getEngineModel())
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

if __name__ == "__main__":

    """
    动量指标：
    
    策略：
        收集arron_up>arron_down,且arron_up大于50的数据对象。
    """

    dirName = "models/sw_arroon_analysis"
    trainDataSouce = SWDataSource(start=datetime(2014, 2, 1), end=datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1), datetime(2020, 9, 1))

    model = TheEngineModel()
    #engine = CoreEngine.create(dirName,model,trainDataSouce,limit_dimen_size=99999999)
    engine = CoreEngine.load(dirName, model)
    runner = CoreEngineRunner(engine)

    def printSWTopOrder():
        strategy = MyStrategy()
        orderList =  runner.getSWCurrentPredictOrder(strategy)
        print(f"order size : {len(orderList)}")
        for order in orderList:
            print(f"{order}")
    printSWTopOrder()
    def test():
        strategy = MyStrategy()
        pdData = runner.backtest(testDataSouce, strategy, min_deal_count=15)
        writer = pd.ExcelWriter('models\output.xlsx')
        pdData.to_excel(writer, sheet_name="data", index=False)
        writer.save()
        writer.close()
        import numpy as np
        countList = np.array(list(strategy.mDateHoldCountMap.values()))
        print(f"每天操作平均发生:{countList.mean()},最大:{countList.max()},最小:{countList.min()}")
        countList = np.array(list(model.mDateOccurCountMap.values()))
        print(f"每个交易日平均发生:{countList.mean()},最大:{countList.max()},最小:{countList.min()}")
        countList = countList + 1
        from vnpy.trader.constant import Exchange, Interval
        swBars = []
        for dt,count in model.mDateOccurCountMap.items():
            value = 1000 * (count + 1) / 89
            bar = BarData(
                symbol="sw_code",
                exchange=Exchange.SZSE,
                datetime=dt,
                interval=Interval.DAILY,
                volume=value,
                open_price=value,
                high_price=value,
                low_price=value,
                close_price=value,
                open_interest=0,
                gateway_name="DB"
            )
            swBars.append(bar)
        bars = swBars
        code = "000300"
        from earnmi.data.MarketImpl import MarketImpl
        market = MarketImpl()
        market.addNotice(code)
        today: datetime = bars[-1].datetime
        market.setToday(today + timedelta(days=1))
        start: datetime = bars[0].datetime;
        baseBars = market.getHistory().getKbarFrom(code, datetime(start.year, start.month, start.day))
        chart = Chart()
        #chart.show(swBars)
        chart.showCompare(swBars,"000300")


