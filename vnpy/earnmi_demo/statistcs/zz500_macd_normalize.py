import os

from earnmi.chart.Chart import Chart
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange
from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from datetime import datetime, timedelta
import talib
import numpy as np
from earnmi.model.BarDataSource import ZZ500DataSource

"""
不同的股票价格的macd的数值不同，macd是跟价格相关的。这样不同股票的价格的macd数值就不好做个比较。
所以要标准化，不同价格的macd的值要标准进行可比较。
标准化的步骤就是： macd值处于最后一天的收盘价。
这里统计下中证500的macd标准化之后的数据统计情况
"""
def parse_macd_disbute():
    start = datetime(2015, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    bars, code = souces.nextBars()
    dif_list = []
    dea_list = []
    last_33bars = np.full(33, None)
    imgeDir = "files/zz500_macd_large_20"
    # if not os.path.exists(dirPath):

    if not os.path.exists(imgeDir):
        os.makedirs(imgeDir)
    chart = Chart()
    while not bars is None:
        indicator = Indicator(40)
        for bar in bars:
            indicator.update_bar(bar)
            last_33bars[:-1] = last_33bars[1:]
            last_33bars[-1] = bar

            if indicator.count > 33:
                dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=False)
                dif_value = dif / bar.close_price * 100
                dea_value = dea / bar.close_price * 100
                dif_list.append(dif_value)
                dea_list.append(dea_value)
                if dif_value < -20:
                    chart.show(last_33bars,
                               savefig=f"{imgeDir}/dif_{bar.symbol}__minus_20_time_{bar.datetime.year}_{bar.datetime.month}_{bar.datetime.day}.jpg")
                if dea_value < -20:
                    chart.show(last_33bars,
                               savefig=f"{imgeDir}/dea_{bar.symbol}__minus_20_time_{bar.datetime.year}_{bar.datetime.month}_{bar.datetime.day}.jpg")

                if abs(dif_value) > 20:
                    print(f"dif:{dif_value},code={code},bar = {bar}")
                if abs(dea_value) > 20:
                    print(f"dea:{dea_value},code={code},bar = {bar}")

        bars, code = souces.nextBars()
    dif_list = np.array(dif_list)
    dea_list = np.array(dea_list)
    def_min, def_max = [dea_list.min(), dea_list.max()]
    dif_min, dif_max = [dif_list.min(), dif_list.max()]
    print(f"dif_max:{dif_max},dif_min:{dif_min},count:{len(dif_list)}")
    print(f"dea_max:{def_max},dea_min:{def_min}")

    N = 5
    dif_spli_list = []
    for i in range(0, N + 1):
        dif_spli_list.append(dif_min + i * (dif_max - dif_min) / N)
    dif_spli_list = [-10, -5, -2.5, 2.5, 5, 10]
    dea_spli_list = []
    for i in range(0, N + 1):
        dea_spli_list.append(def_min + i * (def_max - def_min) / N)
    dea_spli_list = [-10, -5, -2.5, 2.5, 5, 10]
    dif_encoder = FloatEncoder(dif_spli_list)
    dea_encoder = FloatEncoder(dea_spli_list)
    print(f"dif分布:{FloatRange.toStr(dif_encoder.computeValueDisbustion(dif_list), dif_encoder)}")
    print(f"dea分布:{FloatRange.toStr(dea_encoder.computeValueDisbustion(dea_list), dea_encoder)}")
    pass

def parse_macd_rao_disbute():
    start = datetime(2015, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    bars, code = souces.nextBars()
    value_list = []
    last_33bars = np.full(33, None)
    imgeDir = "files/zz500_macd_rao"
    if not os.path.exists(imgeDir):
        os.makedirs(imgeDir)
    chart = Chart()
    while not bars is None:
        indicator = Indicator(40)
        for bar in bars:
            indicator.update_bar(bar)
            last_33bars[:-1] = last_33bars[1:]
            last_33bars[-1] = bar
            if indicator.count > 32:
                v = indicator.macd_rao(period=30)
                value_list.append(v)
                if v > 80:
                     chart.show(last_33bars,
                                savefig=f"{imgeDir}/z80_{bar.symbol}time_{bar.datetime.year}_{bar.datetime.month}_{bar.datetime.day}.jpg")
                #
        bars, code = souces.nextBars()
    value_list = np.array(value_list)
    _min, _max = [value_list.min(), value_list.max()]
    print(f"max:{_max},min:{_min},count:{len(value_list)}")

    N = 5
    spli_list = []
    for i in range(0, N + 1):
        spli_list.append(_min + i * (_max - _min) / N)
    spli_list = [ -100,-80,-50,-30,-10,-5,5,10,30,50,80,100]
    dif_encoder = FloatEncoder(spli_list)
    print(f"分布:{FloatRange.toStr(dif_encoder.computeValueDisbustion(value_list), dif_encoder)}")
    pass

if __name__ == "__main__":
    #parse_macd_disbute()
    parse_macd_rao_disbute()
