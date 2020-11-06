import numpy as np
from future.backports.datetime import datetime

from earnmi.model.CollectData import CollectData
from earnmi.model.Dimension import Dimension, TYPE_2KAGO1
from earnmi_demo.statistcs.FactoryParser import FactoryParser
from vnpy.trader.object import BarData

from earnmi.chart.Chart import Chart
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange
from earnmi.chart.Indicator import Indicator
from earnmi.chart.Factory import Factory
from earnmi.data.MarketImpl import MarketImpl
from datetime import datetime, timedelta
import talib
import numpy as np
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.model.CollectModel import CollectModel
from earnmi.uitl.BarUtils import BarUtils
import os

"""
统计因子值在某个范围，对应未来3天的最大sell_pct和最小buy_pct值。
"""
def parse_wave_ability_disbute():
    start = datetime(2018, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    bars, code = souces.nextBars()

    class MyCollectModel(CollectModel):
        FLOAT_ENCOLDE = FloatEncoder([-1,0,10,20,30,40,50,60,70,80,90,100],minValue=-1,maxValue=100)
        def onCollectStart(self, code: str) -> bool:
            self.indicator = Indicator(45)
            return True
        def onCollectTrace(self, bar: BarData) -> CollectData:
            if not BarUtils.isOpen(bar):
                return None
            self.indicator.update_bar(bar)
            if not self.indicator.inited:
                return None
            #wave_down, wave_up = Factory.wave(30, self.indicator.close, self.indicator.high, self.indicator.low)
            wave_down, wave_up = Factory.obv_wave(30, self.indicator.close, self.indicator.high, self.indicator.low,self.indicator.volume)

            #wave_down, wave_up = self.indicator.aroon(24)

            ##编码
            down_encode = MyCollectModel.FLOAT_ENCOLDE.encode(wave_down)
            up_encode = MyCollectModel.FLOAT_ENCOLDE.encode(wave_up)
            key = down_encode * MyCollectModel.FLOAT_ENCOLDE.mask() + up_encode

            down_encode2 = (int(key / MyCollectModel.FLOAT_ENCOLDE.mask())) % MyCollectModel.FLOAT_ENCOLDE.mask()
            up_encode2 = key % MyCollectModel.FLOAT_ENCOLDE.mask()
            assert down_encode == down_encode2
            assert up_encode2 == up_encode


            dimen = Dimension(type=TYPE_2KAGO1, value=key)
            data = CollectData(dimen)
            data.occurBars.append(bar)
            data.occurExtra['wave_down'] = wave_down
            data.occurExtra['wave_up'] = wave_up
            return data
        def onCollect(self, data: CollectData, newBar: BarData):
            if not BarUtils.isOpen(newBar):
                return
            data.predictBars.append(newBar)
            if len(data.predictBars) >= 3:
                data.setFinished()
    dimen_sell_pct_list_map = {}
    dimen_buy_pct_list_map = {}

    collectModel = MyCollectModel()
    fParser = FactoryParser()
    while not bars is None:
        indicator = Indicator(40)
        last_33bars = np.full(33, None)
        finishedData, unFinishedData = CollectModel.collect(collectModel,bars,code)
        print(f"collect: {len(finishedData)}")

        for cData in finishedData:
            dimen = cData.dimen
            basePrice = cData.occurBars[-1].close_price
            sell_pct_list = dimen_sell_pct_list_map.get(dimen.value)
            if sell_pct_list is None:
                sell_pct_list = []
                dimen_sell_pct_list_map[dimen.value] = sell_pct_list
            buy_pct_list = dimen_buy_pct_list_map.get(cData.dimen.value)
            if buy_pct_list is None:
                buy_pct_list = []
                dimen_buy_pct_list_map[dimen.value] = buy_pct_list
            sell_pct,buy_pct = BarUtils.getMaxSellBuyPct(cData.predictBars,basePrice)
            sell_pct_list.append(sell_pct)
            buy_pct_list.append(buy_pct)
            wave_up = cData.occurExtra['wave_up']
            assert not wave_up is None
            fParser.put("wave_up",wave_up,sell_pct)


        bars,code = souces.nextBars()

    ##打印因子分布的后面几天的sell_pct和buy_pct的分布情况

    dimen_list = list(dimen_sell_pct_list_map.keys())

    dist_list = []
    sell_pct_result = []
    buy_pct_result = []
    up_list = []
    down_list = []
    maxSell = 0
    minBuy = 0
    for key in dimen_list:
        down_encode = (int(key / MyCollectModel.FLOAT_ENCOLDE.mask())) % MyCollectModel.FLOAT_ENCOLDE.mask()
        up_encode = key % MyCollectModel.FLOAT_ENCOLDE.mask()
        sell_value_list = np.array(dimen_sell_pct_list_map[key])
        buy_value_list = np.array(dimen_buy_pct_list_map[key])
        _min1,_max1 = MyCollectModel.FLOAT_ENCOLDE.parseEncode(up_encode)
        _min2,_max2 = MyCollectModel.FLOAT_ENCOLDE.parseEncode(down_encode)
        dist = (_min1 + _max1) / 2 - (_min2 + _max2) / 2
        count = len(sell_value_list)

        if count > 500:
            sell_pct = sell_value_list.mean()
            buy_pct = buy_value_list.mean()
            if sell_pct > maxSell:
                maxSell = sell_pct
            if minBuy > buy_pct:
                minBuy = buy_pct

            desc = f"wave_up[{_min1},{_max1})-wave_down[{_min2},{_max2}), count:{count},dist=%.2f" % dist
            print(f"{desc}，sell_pct={sell_value_list.mean()},buy_pct={buy_value_list.mean()}")
            dist_list.append(dist)
            up_list.append((_min1 + _max1) / 2)
            down_list.append((_min2 + _max2) / 2)
            sell_pct_result.append(sell_value_list.mean())
            buy_pct_result.append(buy_value_list.mean())
            pass

    print(f"maxSell={maxSell},minBuy={minBuy}")

    import talib
    dist_list = np.array(dist_list)
    sell_pct_result = np.array(sell_pct_result)
    buy_pct_result = np.array(buy_pct_result)
    up_list = np.array(up_list)
    down_list = np.array(down_list)

    r1 = talib.CORREL(dist_list, sell_pct_result, timeperiod=len(dist_list))
    r2 = talib.CORREL(dist_list, buy_pct_result, timeperiod=len(dist_list))
    r3 = talib.CORREL(up_list, sell_pct_result, timeperiod=len(dist_list))
    r4 = talib.CORREL(down_list, buy_pct_result, timeperiod=len(dist_list))

    print(f"size:{len(dist_list)},{dist_list}")
    print(f"sell与dist的相关性:{r1[-1]}")
    print(f"buy与dist的相关性:{r2[-1]}")
    print(f"sell与up_list的相关性:{r3[-1]}")
    print(f"buy与down_list的相关性:{r4[-1]}")

    fParser.savePng()
    pass

"""
统计因子值得分布。
"""
def parse_wave_disbute():
    start = datetime(2015, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    bars, code = souces.nextBars()
    imgeDir = "files/zz500_wave_distbute"
    if not os.path.exists(imgeDir):
        os.makedirs(imgeDir)

    chart = Chart()
    period_list = [9,12,20,25]
    count = 0
    fParser = FactoryParser()
    while not bars is None:
        indicator = Indicator(40)
        last_33bars = np.full(33, None)
        for bar in bars:
            if not BarUtils.isOpen(bar):
                continue
            indicator.update_bar(bar)
            last_33bars[:-1] = last_33bars[1:]
            last_33bars[-1] = bar
            if indicator.count > 34:
                count += 1
                if count %10000 == 0:
                    print(f"progress: {count}")
                    #break
                #v = indicator.macd_rao(period=30)
                for p in period_list:
                    aroon_down, aroon_up = indicator.aroon(p)
                    if aroon_down > 0  or aroon_up < 100:
                        continue
                    wave_down, wave_up = Factory.wave(p, indicator.close,indicator.high,indicator.low)
                    fParser.put(f"p{p}_wave_down",wave_down,0.0)
                    fParser.put(f"p{p}_wave_up",wave_up,0.0)
        bars, code = souces.nextBars()

    fParser.printRange()

    pass


if __name__ == "__main__":
    #parse_wave_disbute()
   parse_wave_ability_disbute()
