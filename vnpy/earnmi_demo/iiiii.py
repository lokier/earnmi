from dataclasses import dataclass
from datetime import datetime

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.data.BarV2 import BarV2Market, BarV2
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.model.bar import BarData

app = App()
start = datetime(year=2020,month=1,day=6)
end = datetime(year=2021,month=2,day=5)
drvier = SW2Driver()
index_driver = StockIndexDriver()  ##A股指数驱动
market = app.getBarManager().createBarMarket(index_driver,[drvier])
v2_market = BarV2Market(market)

class KDJItem(IndicatorItem):

    def getNames(self):
        #return ["avg","sell","buy"]
        return ["power_rate","0"]

    def getValues(self, indicator: Indicator,bar:BarV2,signal:Signal) -> Map:
        values = {}
        values["avg"] = bar.avg_price
        values["sell"] = bar.sell_price
        values["buy"] = bar.buy_price
        values["power_rate"] = bar.power_rate
        values["0"] = 0

        return values

    def getColor(self, name: str):
        if name == "power_rate":
            return 'r'
        if name == "sell":
            return 'g'
        return 'b'

    def isLowerPanel(self):
        return True

symbol_list = drvier.get_symbol_lists()
for symbol in symbol_list:
    print(f"symbol: {symbol}")
    # try:
    bars = v2_market.get_bars(symbol, start, end)
    chart = Chart()
    chart.show(bars, KDJItem())
    # except AssertionError:
    #     print(f"    -->:error assert")






