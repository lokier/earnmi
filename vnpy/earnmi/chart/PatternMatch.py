from datetime import datetime

import numpy as np
import talib
from werkzeug.routing import Map

from earnmi.chart.Indicator import Indicator
from vnpy.trader.object import BarData
from typing import Tuple, Union

"""
各种K线指标库
"""
class PatternMatch(object):

    def p2_2crow(indictor:Indicator) ->int:
        return 0


def getData(barList:[],start:int, end:int):
    high = []
    low = []
    close = []
    open = []

    # bars = np.array(barList)
    bars = barList[start:end]

    for i in range(0, len(bars)):
        bar: BarData = bars[i]
        bar.index = i
        high.append(bar.high_price)
        low.append(bar.low_price)
        close.append(bar.close_price)
        open.append(bar.open_price)


    return bars,np.array(high),np.array(low),np.array(close),np.array(open)



if __name__ == "__main__":
    from earnmi.data.MarketImpl import MarketImpl
    from earnmi.data.SWImpl import SWImpl
    from earnmi.chart.Chart import Chart, IndicatorItem, Signal


    class pos(IndicatorItem):
        def __init__(self, integes):
            IndicatorItem.__init__(self,False)
            self.integes = integes

        def getValues(self, indicator: Indicator, bar: BarData, signal: Signal) -> Map:

            index = bar.index
            value = self.integes[index]
            if value == -100:
                signal.sell = True
            elif value == 100:
                signal.buy = True
            return {}

    sw = SWImpl()
    lists = sw.getSW2List()

    code = "801743"

    start = datetime(2018, 5, 1)
    end = datetime(2020, 8, 17)

    #for code in lists:
    barList = sw.getSW2Daily(code, start, end)
    # print(f"barlist size ={len(barList)}")

    bars, high, low, close, open = getData(barList, 320, 358)

    integes = talib.CDL3BLACKCROWS(open, high, low, close)
    print(f"code:{code},orign size:{len(open)},v size:{len(integes)},value={integes}")




    chart = Chart()
    chart.show(bars,pos(integes))