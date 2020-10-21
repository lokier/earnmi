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
if __name__ == "__main__":
    start = datetime(2015, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    bars,code = souces.nextBars()
    dif_list = []
    dea_list = []
    while not bars is None:
        indicator = Indicator(40)
        for bar in bars:
            indicator.update_bar(bar)
            if indicator.count > 33:
                dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=False)
                dif_value = dif/bar.close_price * 100
                dea_value = dea / bar.close_price * 100
                dif_list.append(dif_value)
                dea_list.append(dea_value)
                if abs(dif_value) > 20:
                    print(f"dif:{dif_value},code={code},bar = {bar}")
                if abs(dea_value) > 20:
                    print(f"dea:{dea_value},code={code},bar = {bar}")

        bars, code = souces.nextBars()
    dif_list = np.array(dif_list)
    dea_list = np.array(dea_list)
    def_min,def_max = [dea_list.min(),dea_list.max()]
    dif_min,dif_max = [dif_list.min(),dif_list.max()]
    print(f"dif_max:{dif_max},dif_min:{dif_min},count:{len(dif_list)}")
    print(f"dea_max:{def_max},dea_min:{def_min}")

    N = 5
    dif_spli_list = []
    for i in range(0,N+1):
        dif_spli_list.append(dif_min + i * (dif_max - dif_min) / N)
    dif_spli_list = [-10,-5, -2.5,2.5,5,10]
    dea_spli_list = []
    for i in range(0,N+1):
        dea_spli_list.append(def_min + i * (def_max - def_min) / N)
    dea_spli_list = [-10,-5,-2.5,2.5,5,10]
    dif_encoder = FloatEncoder(dif_spli_list)
    dea_encoder = FloatEncoder(dea_spli_list)

    print(f"dif分布:{FloatRange.toStr(dif_encoder.computeValueDisbustion(dif_list),dif_encoder)}")
    print(f"dea分布:{FloatRange.toStr(dea_encoder.computeValueDisbustion(dea_list),dea_encoder)}")

    pass

