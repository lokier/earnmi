from datetime import datetime, timedelta
from typing import List

from ibapi.common import BarData
from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, BollItem, IndicatorItem, Signal, HoldBarMaker
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl
from earnmi.model.BarDataSource import ZZ500DataSource

"""
 RSI指标
"""
class IndicatorLine(IndicatorItem):

    maker:HoldBarMaker = HoldBarMaker()

    def getNames(self) -> List:
        return ["a"]


    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        if indicator.count>1:
            obv = indicator.obv(array=False)
            values["a"] = obv
        else:
            values["a"] = 50
        return values

    def getColor(self, name: str):
        if name == "fast":
            return 'r'
        return 'y'

    def isLowerPanel(self) ->bool:
        return True

"""
 RSI指标
"""
class kdj(IndicatorItem):

    maker:HoldBarMaker = HoldBarMaker()
    def __init__(self):
        super().__init__(False)

    def getNames(self) -> List:
        return ["k","d","j"]


    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        if indicator.count>20:
            k,d,j = indicator.kdj(fast_period=9,slow_period=3,array=True)
            values["k"] = k[-1]
            values["d"] = d[-1]
            values["j"] = j[-1]

            if k[-2] < d[-2] and k[-1] >= d[-1]:
                signal.buy = True

        else:
            values["k"] = 50
            values["d"] = 50
            values["j"] = 50
        return values

    def getColor(self, name: str):
        if name == "k":
            return 'r'
        elif name == 'd':
            return 'b'
        return 'y'

    def isLowerPanel(self) ->bool:
        return True

code = "600196"

start = datetime(2020, 5, 1)
end = datetime.now();
#end = datetime(2020, 8, 17)

#code = '000300'
#801161.XSHG
#market = MarketImpl()
#market.addNotice(code)
#market.setToday(datetime.now())
#bars = market.getHistory().getKbarFrom(code,start)


source = ZZ500DataSource(start,end)

bars,code = source.nextBars();


print(f"bar.size = {bars.__len__()}")


chart = Chart()

chart.show(bars,kdj())
#chart.showCompare(bars,"000300")