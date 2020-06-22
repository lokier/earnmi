import talib
import numpy
from vnpy.trader.object import BarData

from vnpy.trader.constant import Exchange

from earnmi.chart.IndexLib import IndexLib

indexes = IndexLib(50)
close=[4.7,4.49,4.73,4.71,4.8,4.77,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15,4.89,4.79,4.95,5.01,5.01,5.15,4.97,4.77,4.84,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15,4.89,4.79,4.95,5.01,5.01,5.15,4.97,4.77,4.84,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15,4.89,4.79,4.95,5.01,5.01,5.15,4.97,4.77,4.84,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15,4.89,4.79,4.95,5.01,5.01,5.15,4.97,4.77,4.84,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82,4.87,4.93,4.93,4.94,5.43,5.15,4.89,4.79,4.95,5.01,5.01,5.15,4.97,4.77,4.84,4.8,4.72,4.69,4.46,4.54,4.33,4.48,4.71,4.82];

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
print(f"index.init = ${indexes.inited}")

macd, signal, hist = indexes.macd(fast_period=12, slow_period=26, signal_period=9, array=True)

# macd, signal, hist = talib.MACD(
#     numpy.array(close), fastperiod=12, slowperiod=26, signalperiod=9)

print(macd)
print(signal)
print(hist)