from datetime import datetime

from werkzeug.routing import Map
from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Factory import Factory
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.model.bar import BarData
from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.constant import Interval





drvier1 = StockIndexDriver()
drvier2 = SW2Driver()
app = App()
start = datetime(year=2020,month=1,day=1)
end = datetime(year=2021,month=3,day=20)
bar_source = app.getBarManager().createBarSoruce([drvier2],Interval.DAILY,start,end)
bars,symbol = bar_source.nextBars()
chart = Chart()
pct_list = []
while not bars is None:

    low, high, open, close, volume = BarUtils.to_np_array(bars)
    ad_diff2 = Factory.ad_diff2(close, high, low, volume);
    ad_diff = Factory.ad_diff(close, high, low, volume);
    for i in range(len(bars)):
        bars[i].ad_diff2 = ad_diff2[i]
        bars[i].ad_diff = ad_diff[i]

    #chart.show(bars,Item())
    print(f"{symbol}: size = {len(bars)}")
    n_bar_list = to_nbar_list(bars,5)

    chart.show(n_bar_list)

    bars, symbol = bar_source.nextBars()

