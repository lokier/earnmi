from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from earnmi.chart.Chart import Chart
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.core.analysis.FloatRange import FloatRange
from earnmi.data.BarTrader import SimpleTrader
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from vnpy.trader.constant import Interval



drvier1 = StockIndexDriver()
drvier2 = SW2Driver()
app = App()
start = datetime(year=2020,month=1,day=1)
end = datetime(year=2021,month=3,day=20)
bar_source = app.getBarManager().createBarSoruce([drvier2],Interval.DAILY,start,end)
bars,symbol = bar_source.nextBars()
trader = SimpleTrader()
while not bars is None:
    indicator = Indicator(40)
    print(f"start:{bars[0].symbol}")
    for bar in bars:
        indicator.update_bar(bar)
        if indicator.count < 34:
            continue
        dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True)
        ##金叉出现
        if (macd_bar[-1] >= 0 and macd_bar[-2] <= 0):
            if not trader.hasBuy(bar.symbol):
                the_buy_price = bar.close_price * 1.001  # 上一个交易日的收盘价作为买入价
                trader.buy(bar.symbol,the_buy_price,bar.datetime)
            ##死叉出现
        elif (macd_bar[-1] <= 0 and macd_bar[-2] >= 0):
            if trader.hasBuy(bar.symbol):
                sell_Price = bars[-1].close_price * 0.999  # 上一个交易日的收盘价作为买如价
                trader.sell(bar.symbol,sell_Price,bar.datetime)
        trader.watch(bar.datetime)
    trader.resetWatch()
    bars, symbol = bar_source.nextBars()

trader.print()
