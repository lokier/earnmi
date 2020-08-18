from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, BollItem, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from vnpy.trader.object import BarData


class Item(IndicatorItem):

    def getNames(self) -> List:
        return ["adx"]


    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        n = 14
        if indicator.count >= n:
            values["adx"] = indicator.adxr(14)
        else:
            values["adx"] = 0.0
        return values

    def getColor(self, name: str):
        return 'r'

code = "600155"
#code = '000300'
#801161.XSHG
market = MarketImpl()
market.addNotice(code)
market.setToday(datetime.now())


bars = market.getHistory().getKbars(code,80)

print(f"bar.size = {bars.__len__()}")


chart = Chart()
chart.show(bars, Item())
