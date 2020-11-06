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
统计因子值在某个范围，对应未来3天的平均收盘价。
"""
"""
valuesList[0]:, max:48.00,min:0.00,count:196750
                分布:[[min:0.00)=0.00%,[0.00:9.60)=69.39%,[9.60:19.20)=25.04%,[19.20:28.80)=5.27%,[28.80:38.40)=0.29%,[38.40:48.00)=0.01%,[48.00:max)=0.00%,]
    valuesList[1]:, max:46.08,min:0.00,count:196750
                分布:[[min:0.00)=0.00%,[0.00:9.22)=71.59%,[9.22:18.43)=24.26%,[18.43:27.65)=3.87%,[27.65:36.86)=0.27%,[36.86:46.08)=0.00%,[46.08:max)=0.00%,]
"""
def parse_wave_ability_disbute():
    start = datetime(2015, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    bars, code = souces.nextBars()
    class MyCollectModel(CollectModel):
        FLOAT_ENCOLDE = FloatEncoder([-1,0,2,4,6,8,10,20,35,50],minValue=-1,maxValue=100)
        def onCollectStart(self, code: str) -> bool:
            self.indicator = Indicator(54)
            return True
        def onCollectTrace(self, bar: BarData) -> CollectData:
            if not BarUtils.isOpen(bar):
                return None
            self.indicator.update_bar(bar)
            if not self.indicator.inited:
                return None
            wave_down, wave_up = Factory.obv_wave(30, self.indicator.close, self.indicator.high, self.indicator.low,self.indicator.volume)
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
            if len(data.predictBars) >= 7:
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
            sell_pct = BarUtils.getAvgClosePct(cData.predictBars,basePrice)
            buy_pct = sell_pct
            sell_pct_list.append(sell_pct)
            buy_pct_list.append(buy_pct)
            wave_up = cData.occurExtra['wave_up']
            assert not wave_up is None
            fParser.put("wave_up", wave_up, sell_pct)
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
            print(f"{desc}，sell_pct={sell_pct},buy_pct={buy_pct}")
            up_list.append((_min1 + _max1) / 2 )
            down_list.append((_min2 + _max2) / 2 )
            dist_list.append(dist)
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
    #
    # r1 = talib.CORREL(dist_list, sell_pct_result, timeperiod=len(dist_list))
    # r2 = talib.CORREL(dist_list, buy_pct_result, timeperiod=len(dist_list))
    # r3 = talib.CORREL(up_list, sell_pct_result, timeperiod=len(dist_list))
    # r4 = talib.CORREL(down_list, buy_pct_result, timeperiod=len(dist_list))
    #
    # print(f"size:{len(dist_list)},{dist_list}" )
    # print(f"sell与dist的相关性:{r1[-1]}")
    # print(f"buy与dist的相关性:{r2[-1]}")
    # print(f"sell与up_list的相关性:{r3[-1]}" )
    # print(f"buy与down_list的相关性:{r4[-1]}" )

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
    period_list = [33]
    value_list_map = {}
    for p in period_list:
        value_list_map[p] = [
            [],#wave_down
            [],#wave_up
        ]
    count = 0
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
                    #aroon_down, aroon_up = indicator.aroon(p)
                    # if aroon_down > 0  or aroon_up < 100:
                    #     continue
                    wave_down, wave_up = Factory.obv_wave(p, indicator.close,indicator.high,indicator.low,indicator.volume)
                    value_list_map[p][0].append(wave_down)
                    value_list_map[p][1].append(wave_up)
                    # value_list_map[p].append(v)
                    # if p == 30:
                    #     if  v< -0.85:
                    #         print(f"find:{v}")
                    #         chart.show(last_33bars,
                    #             savefig=f"{imgeDir}/z80_1_minus_{bar.symbol}time_{bar.datetime.year}_{bar.datetime.month}_{bar.datetime.day}.jpg")
                    #
        bars, code = souces.nextBars()


    for period, value_list_array in value_list_map.items():
        print(f"===period:{period}===============")
        for i in range(0,len(value_list_array)):
            value_list = np.array(value_list_array[i])
            _min, _max = [value_list.min(), value_list.max()]
            print(f"    valuesList[{i}]:, max:%.2f,min:%.2f,count:{len(value_list)}" % (_max, _min))
            N = 5
            spli_list = []
            for i in range(0, N + 1):
                spli_list.append(_min + i * (_max - _min) / N)
            # spli_list = [ 0,100]
            dif_encoder = FloatEncoder(spli_list)
            print(f"                分布:{FloatRange.toStr(dif_encoder.computeValueDisbustion(value_list), dif_encoder)}")
    pass


if __name__ == "__main__":
    #parse_wave_disbute()
    parse_wave_ability_disbute()
