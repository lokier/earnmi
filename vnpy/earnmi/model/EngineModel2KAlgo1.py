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

class EngineModel2KAlgo1(CoreEngineModel):

    def __init__(self):
        self.lasted3Bar = np.array([None ,None ,None])
        self.lasted3BarKdj = np.array([None ,None ,None])
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
        if self.indicator.count >= 15:
            from earnmi.chart.KPattern import KPattern
            kPatternValue = KPattern.encode2KAgo1(self.indicator)
            if not kPatternValue is None :
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

    def canPredict(self,collectData:CollectData)->bool:
        return len(collectData.occurBars)>= 3

    # def getSellBuyPctLabel(self, collectData: CollectData):
    #     bars: ['BarData'] = collectData.predictBars
    #     if len(bars) > 0:
    #         occurBar = collectData.occurBars[-2]
    #         startPrice = occurBar.close_price
    #         sell_pct = -99999
    #         buy_pct = 9999999
    #         for bar in bars:
    #             __sell_pct = 100 * ((bar.high_price + bar.close_price) / 2 - startPrice) / startPrice
    #             __buy_pct = 100 * ((bar.low_price + bar.close_price) / 2 - startPrice) / startPrice
    #             sell_pct = max(__sell_pct, sell_pct)
    #             buy_pct = min(__buy_pct, buy_pct)
    #         return sell_pct, buy_pct
    #     return None, None

    @abstractmethod
    def generateYLabel(self, cData:CollectData)->[float,float,float]:
        bars: ['BarData'] = cData.predictBars
        if len(bars) > 0:
            occurBar = cData.occurBars[-2]
            startPrice = occurBar.close_price
            sell_price = -9999999999
            buy_price = - sell_price
            for bar in bars:
                sell_price = max((bar.high_price + bar.close_price) / 2,sell_price)
                buy_price = min((bar.low_price + bar.close_price) / 2,buy_price)
            return startPrice, sell_price,buy_price
        return None, None,None

    # def __genereatePd(self, dataList: Sequence['CollectData']):
    #     trainDataSet = []
    #     for traceData in dataList:
    #         occurBar = traceData.occurBars[-2]
    #         skipBar = traceData.occurBars[-1]
    #         sell_pct = 100 * (
    #                 (skipBar.high_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price
    #         buy_pct = 100 * (
    #                 (skipBar.low_price + skipBar.close_price) / 2 - occurBar.close_price) / occurBar.close_price
    #
    #         label_sell_1 = None
    #         label_buy_1 = None
    #         label_sell_2 = None
    #         label_buy_2 = None
    #         if len(traceData.predictBars) > 0:
    #             real_sell_pct, real_buy_pct = self.getSellBuyPctLabel(traceData)
    #             label_sell_1 = PredictModel.PctEncoder1.encode(real_sell_pct)
    #             label_buy_1 = PredictModel.PctEncoder1.encode(real_buy_pct)
    #             label_sell_2 = PredictModel.PctEncoder2.encode(real_sell_pct)
    #             label_buy_2 = PredictModel.PctEncoder2.encode(real_buy_pct)
    #
    #         kdj = traceData.occurKdj[-1]
    #
    #         data = []
    #         data.append(buy_pct)
    #         data.append(sell_pct)
    #         data.append(kdj[0])
    #         data.append(kdj[2])
    #         data.append(label_sell_1)
    #         data.append(label_buy_1)
    #         data.append(label_sell_2)
    #         data.append(label_buy_2)
    #         trainDataSet.append(data)
    #     cloumns = ["buy_pct",
    #                "sell_pct",
    #                "k",
    #                "j",
    #                "label_sell_1",
    #                "label_buy_1",
    #                "label_sell_2",
    #                "label_buy_2",
    #                ]
    #     orgin_pd = pd.DataFrame(trainDataSet, columns=cloumns)
    #     return orgin_pd

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


    """
    生成特征值。(有4个标签）
    返回值为：x, y_sell_1,y_buy_1,y_sell_2,y_buy_2
    """
    # def generateFeature(self, engine, dataList: Sequence['CollectData']):
    #     engine.printLog(f"[SVMPredictModel]: generate feature")
    #
    #     def set_0_between_100(x):
    #         if x > 100:
    #             return 100
    #         if x < 0:
    #             return 0
    #         return x
    #
    #     def percent_to_one(x):
    #         return int(x * 100) / 1000.0
    #
    #     def toInt(x):
    #         v = int(x + 0.5)
    #         if v > 10:
    #             v = 10
    #         if v < -10:
    #             v = -10
    #         return v
    #
    #     d = self.__genereatePd(dataList)
    #     engine.printLog(f"   origin:\n{d.head()}")
    #
    #     d['buy_pct'] = d.buy_pct.apply(percent_to_one)  # 归一化
    #     d['sell_pct'] = d.sell_pct.apply(percent_to_one)  # 归一化
    #     d.k = d.k.apply(set_0_between_100)
    #     d.j = d.j.apply(set_0_between_100)
    #     d.k = d.k / 100
    #     d.j = d.j / 100
    #     engine.printLog(f"   convert:\n{d.head()}")
    #     data = d.values
    #     x, y = np.split(data, indices_or_sections=(4,), axis=1)  # x为数据，y为标签
    #     y_1 = y[:, 0:1].flatten()  # 取第一列
    #     y_2 = y[:, 1:2].flatten()  # 取第一列
    #     y_3 = y[:, 2:3].flatten()  # 取第一列
    #     y_4 = y[:, 3:4].flatten()  # 取第一列
    #
    #     engine.printLog(f"   y_1:\n{y_1}")
    #     engine.printLog(f"   y_2:\n{y_2}")
    #     engine.printLog(f"   y_3:\n{y_3}")
    #     engine.printLog(f"   y_4:\n{y_4}")
    #
    #     engine.printLog(f"[SVMPredictModel]: generate feature end!!!")
    #     return x, y_1, y_2, y_3, y_4


    def generatePredictOrder(self,engine:CoreEngine, predict: PredictData) -> PredictOrder:

        code = predict.collectData.occurBars[-1].symbol
        name = self.sw.getSw2Name(code)
        order = PredictOrder(dimen=predict.dimen,code=code,name=name)

        from earnmi.model.CoreEngine import PredictModel
        min1, max1 = PredictModel.PctEncoder1.parseEncode(predict.sellRange1[0].encode)
        min2, max2 = PredictModel.PctEncoder2.parseEncode(predict.sellRange2[0].encode)
        total_probal = predict.sellRange2[0].probal + predict.sellRange1[0].probal
        predict_sell_pct = (min1 + max1) / 2 * predict.sellRange1[0].probal / total_probal + (min2 + max2) / 2 * \
                           predict.sellRange2[0].probal / total_probal

        min1, max1 = PredictModel.PctEncoder1.parseEncode(predict.buyRange1[0].encode)
        min2, max2 = PredictModel.PctEncoder2.parseEncode(predict.buyRange2[0].encode)
        total_probal = predict.sellRange2[0].probal + predict.sellRange1[0].probal
        predict_buy_pct = (min1 + max1) / 2 * predict.buyRange1[0].probal / total_probal + (min2 + max2) / 2 * \
                          predict.buyRange2[0].probal / total_probal

        start_price = predict.collectData.occurBars[-2].close_price
        order.suggestSellPrice = start_price * (1 + predict_sell_pct / 100)
        order.suggestBuyPrice = start_price * (1 + predict_buy_pct / 100)

        ##for backTest
        occurBar: BarData = predict.collectData.occurBars[-2]
        skipBar: BarData = predict.collectData.occurBars[-1]
        buy_price = skipBar.close_price
        predict_sell_pct = 100 * (order.suggestSellPrice - start_price)/start_price
        predict_buy_pct = 100 * (order.suggestBuyPrice - start_price) / start_price
        buy_point_pct = 100 * (buy_price - occurBar.close_price) / occurBar.close_price  ##买入的价格
        if predict_buy_pct > 0.2 and predict_sell_pct - buy_point_pct > 1:
            order.status = PredictOrderStatus.HOLD
            order.buyPrice = buy_price
        else:
            order.status = PredictOrderStatus.STOP

        return order



    def updatePredictOrder(self, order: PredictOrder,bar:BarData,isTodayLastBar:bool):
        pass
        if(order.status == PredictOrderStatus.HOLD):
            if bar.high_price >= order.suggestSellPrice:
                order.sellPrice = order.suggestSellPrice
                order.status = PredictOrderStatus.CROSS
                return
            order.holdDay +=1
            if order.holdDay >=2:
                order.sellPrice = bar.close_price
                order.status = PredictOrderStatus.CROSS
                return

