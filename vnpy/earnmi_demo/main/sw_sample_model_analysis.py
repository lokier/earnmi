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
from earnmi.model.PredictData2 import PredictData
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData

if __name__ == "__main__":
    dirName = "mdoels/predict_current_sw_top2"

    class MyStrategy(CoreEngineStrategy):
        def __init__(self):
            self.sw = SWImpl()

        def generatePredictOrder(self, engine: CoreEngine, predict: PredictData) -> PredictOrder:
            code = predict.collectData.occurBars[-1].symbol
            name = self.sw.getSw2Name(code)
            order = PredictOrder(dimen=predict.dimen, code=code, name=name)
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
            order.power_rate = engine.queryQuantData(predict.dimen).getPowerRate()

            ##for backTest
            occurBar: BarData = predict.collectData.occurBars[-2]
            skipBar: BarData = predict.collectData.occurBars[-1]
            buy_price = skipBar.close_price
            predict_sell_pct = 100 * (order.suggestSellPrice - start_price) / start_price
            predict_buy_pct = 100 * (order.suggestBuyPrice - start_price) / start_price
            buy_point_pct = 100 * (buy_price - occurBar.close_price) / occurBar.close_price  ##买入的价格
            if predict_buy_pct > 0.2 and predict_sell_pct - buy_point_pct > 1:
                order.status = PredictOrderStatus.HOLD
                order.buyPrice = buy_price
            else:
                order.status = PredictOrderStatus.STOP
            return order

        def updatePredictOrder(self, order: PredictOrder, bar: BarData, isTodayLastBar: bool):
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


    dirName = "files/backtest"
    trainDataSouce = SWDataSource(start=datetime(2014, 2, 1), end=datetime(2019, 9, 1))
    testDataSouce = SWDataSource(datetime(2019, 9, 1), datetime(2020, 9, 1))
    from earnmi.model.EngineModel2KAlgo1 import EngineModel2KAlgo1

    model = EngineModel2KAlgo1()
    # engine = CoreEngine.create(dirName,model,trainDataSouce,limit_dimen_size=99999999)
    engine = CoreEngine.load(dirName, model)
    runner = CoreEngineRunner(engine)
    strategy = MyStrategy()
    pdData = runner.backtest(testDataSouce, strategy, min_deal_count=15)

    writer = pd.ExcelWriter('files\CoreEngineRunner.xlsx')
    pdData.to_excel(writer, sheet_name="data", index=False)
    writer.save()
    writer.close()