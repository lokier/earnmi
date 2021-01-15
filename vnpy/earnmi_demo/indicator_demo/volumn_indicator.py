from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, BollItem, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import Market2Impl
from vnpy.trader.object import BarData


class Item(IndicatorItem):

    def getNames(self) -> List:
        return ["obv","ad","adsoc"]


    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        n = 15
        if indicator.count >= n:
            values["obv"] = indicator.adosc()
            values["ad"] = indicator.adosc()
            values["adsoc"] =indicator.adosc()
        else:
            values["obv"] = bar.volume
            values["ad"] = bar.volume
            values["adsoc"] = bar.volume
        return values

    def getColor(self, name: str):
        if name == "obv":
            return 'r'
        elif name =='ad':
            return 'b'
        return 'y'

code = "600155"
#code = '000300'
#801161.XSHG
market = Market2Impl()
market.addNotice(code)
market.setToday(datetime.now())


bars = market.getHistory().getKbars(code,80)

print(f"bar.size = {bars.__len__()}")


chart = Chart()
#chart.open_obv = True
chart.show(bars, Item())
#chart.showCompare(bars,"000300")