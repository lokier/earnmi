
from datetime import datetime
from earnmi.core.App import App
from earnmi.data.BarSoruce import BarSource
from earnmi.data.BarTrader import SimpleTrader
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.strategy.BarStrategy import BuyOrSellStrategy, analysis_BuyOrSellStrategy
from vnpy.trader.constant import Interval



'''
买入点：kd金叉
卖出点：kd都超过80（止盈点），或者kd死叉（止损点）
'''
class kdj1_Strategy(BuyOrSellStrategy):

    def is_buy_or_sell(self, bar: BarSource) -> bool:
        self.indicator.update_bar(bar)
        if self.indicator.count > 20:
            k, d, j = self.indicator.kdj(fast_period=9, slow_period=3,array=True)
            gold_cross = k[-1] > d[-1] and k[-2] <= d[-2]
            if gold_cross:
                return True
            deadCorss = k[-1] < d[-1] and k[-2] >= d[-2]
            if deadCorss or (k[-1]>80 and d[-1]>80):
                return False

        return None

'''
macd 与 kdj结合。
'''
class macd_kdj_Strategy(BuyOrSellStrategy):

    def is_buy_or_sell(self, bar: BarSource) -> bool:
        self.indicator.update_bar(bar)
        if self.indicator.count > 34:
            dif, dea, macd_bar = self.indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True)
            if macd_bar[-1] < 0:
                ##金叉出现
                return None
            k, d, j = self.indicator.kdj(fast_period=9, slow_period=3,array=True)
            gold_cross = k[-1] > d[-1] and k[-2] <= d[-2]
            if gold_cross:
                return True
            deadCorss = k[-1] < d[-1] and k[-2] >= d[-2]
            if deadCorss:
                return False
        return None

class macd_Strategy(BuyOrSellStrategy):

    def is_buy_or_sell(self, bar: BarSource) -> bool:
        self.indicator.update_bar(bar)
        if self.indicator.count > 34:
            dif, dea, macd_bar = self.indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True)
            if (macd_bar[-1] >= 0 and macd_bar[-2] <= 0):
                ##金叉出现
                return False
            elif (macd_bar[-1] <= 0 and macd_bar[-2] >= 0):
                ##死叉出现
                return True
        return None






drvier1 = StockIndexDriver()
drvier2 = SW2Driver()
app = App()
start = datetime(year=2020,month=1,day=1)
end = datetime(year=2021,month=3,day=20)
bar_source = app.getBarManager().createBarSoruce([drvier2],Interval.DAILY,start,end)


analysis_BuyOrSellStrategy(bar_source,macd_Strategy())
