from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, BollItem, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from vnpy.trader.object import BarData


class Item(IndicatorItem):

    def __init__(self):
        self.names = [
            "adx",
            "-di","+di",
            "adxr"]
        self.colors = ['b','g','r','black']

    def getNames(self) -> List:
        return self.names


    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        n = 20
        if indicator.count >= n:
            values["adx"] = indicator.adx(14)
            values["-di"] = indicator.minus_di(14)
            values["+di"] = indicator.plus_di(14)
            values["adxr"] = indicator.adxr(14)
        else:
            values["adx"] = 0
            values["-di"] = 0
            values["+di"] = 0
            values["adxr"] =0
        return values

    def getColor(self, name: str):
        index = self.names.index(name)
        if index >= 0:
            return self.colors[index]
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
