from dataclasses import dataclass
from datetime import datetime

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.data.BarV2 import BarV2Market, BarV2
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.data.tranfrom.BarV2Transfrom import BarV2Transform
from earnmi.model.bar import BarData
from vnpy.trader.constant import Interval

app = App()
start = datetime(year=2020,month=1,day=6)
end = datetime(year=2021,month=2,day=5)
drvier = SW2Driver()
transfrom = BarV2Transform()
transfrom_driver = app.getBarManager().transfrom(transfrom)

sources = app.getBarManager().createBarSoruce(transfrom_driver,start,end)

for symbol,bars in sources.itemsSequence():
    print(f"symbol:{symbol}, len = {len(bars)}")






