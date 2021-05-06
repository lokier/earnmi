from datetime import datetime

from werkzeug.routing import Map
from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Factory import Factory
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.core.analysis.FloatRange import FloatRange
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
    indicator = Indicator(40)
    the_buy_price = None
    for bar in bars:
        indicator.update_bar(bar)
        if indicator.count < 34:
            continue
        dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True)
        ##金叉出现
        if (macd_bar[-1] >= 0 and macd_bar[-2] <= 0):
            if the_buy_price is None:
                the_buy_price = bar.close_price * 1.01  # 上一个交易日的收盘价作为买入价
            ##死叉出现
        if (macd_bar[-1] <= 0 and macd_bar[-2] >= 0):
            if not the_buy_price is None:
                sell_Price = bars[-1].close_price * 0.99  # 上一个交易日的收盘价作为买如价
                the_pct = 100 * (sell_Price - the_buy_price) / the_buy_price
                pct_list.append(the_pct)

    bars, symbol = bar_source.nextBars()

float_range = FloatRange(-1,1,1)  #生成浮点值范围区间对象
dist = float_range.calculate_distribute(pct_list)

dist.showPipChart()
print(f"size = {len(pct_list)},dist:{dist.toStr()}")

