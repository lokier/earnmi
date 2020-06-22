import talib
import numpy
from vnpy.trader.object import BarData

from vnpy.trader.constant import Exchange

from earnmi.chart.Indicator import IndexLib

import pandas as pd
import numpy as np

def myMACD(price, fastperiod=12, slowperiod=26, signalperiod=9):
   # ewma12 = pd.ewm(price,span=fastperiod)
   # ewma60 = pd.ewm(price,span=slowperiod)
    price = pd.DataFrame(data=price)
   #  ewma12 = pd.DataFrame.ewm(price, span=fastperiod).mean()
   #  ewma60 = pd.DataFrame.ewm(price, span=slowperiod).mean()
    ewma12 = price.ewm(span=fastperiod).mean
    ewma60 = price.ewm(span=slowperiod).mean

    dif = ewma12.icol(0)-ewma60.icon(0)

    #dea = pd.ewma(dif,span=signalperiod)
    #dea = pd.DataFrame.ewm(dif, span=signalperiod).mean()
    dea =dif.ewm(span=signalperiod).mean()
    bar = (dif-dea) #有些地方的bar = (dif-dea)*2，但是talib中MACD的计算是bar = (dif-dea)*1
    return dif,dea,bar


indexes = IndexLib(50)
close=[4.7,4.49,4.73,4.71,4.8,4.77,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15,4.89,4.79,4.95,5.01,5.01,5.15,4.97,4.77,4.84,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15,4.89,4.79,4.95,5.01,5.01,5.15,4.97,4.77,4.84,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15,4.89,4.79,4.95,5.01,5.01,5.15,4.97,4.77,4.84,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15,4.89,4.79,4.95,5.01,5.01,5.15,4.97,4.77,4.84,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15];
close = np.array(close)

bars = []
for i in range(close.__len__()):
    bar = BarData(
        symbol="test",
        exchange=Exchange.SSE,
        datetime=None,
        gateway_name="unkonw",
        open_price=884,
        high_price=0,
        low_price=0,
        close_price=close[i]
    )
    bars.append(bar)

indexes.update_bar(bars)
print(f"index.init = {indexes.inited},count ={indexes.count}")

macd, signal, hist = indexes.macd(fast_period=12, slow_period=26, signal_period=9, array=True)


# macd, signal, hist = talib.MACD(
#     numpy.array(close), fastperiod=12, slowperiod=26, signalperiod=9)

print(macd[-1])
print(signal[-1])
print(hist[-1])

print(f"macd-signal = {macd[-1] - signal[-1]}")