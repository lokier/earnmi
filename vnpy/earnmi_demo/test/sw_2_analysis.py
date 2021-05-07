from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from earnmi.chart.Chart import Chart
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.core.analysis.FloatRange import FloatRange
from earnmi.data.BarSoruce import BarSource
from earnmi.data.BarTrader import SimpleTrader
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from vnpy.trader.constant import Interval

'''
买入卖出策略类。 计算买入点和卖出点的
'''
class BuyOrSellStrategy:

    def onBegin(self,code:str):
        self.indicator = Indicator(40)

    def onEnd(self,code:str):
        pass
    '''
     当天的交易情况： true表示买入点，false表示卖出点，None表示不操作。
    '''
    def is_buy_or_sell(self,bar:BarSource)->bool:
        return None

class macd_Strategy(BuyOrSellStrategy):

    def is_buy_or_sell(self, bar: BarSource) -> bool:
        self.indicator.update_bar(bar)
        if self.indicator.count > 34:
            dif, dea, macd_bar = self.indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True)
            if (macd_bar[-1] >= 0 and macd_bar[-2] <= 0):
                ##金叉出现
                return True
            elif (macd_bar[-1] <= 0 and macd_bar[-2] >= 0):
                ##死叉出现
                return False
            return None


def analysis_buy_or_sell_strategy(source: BarSource, strategy: BuyOrSellStrategy, trader: SimpleTrader):
    source.reset()
    bars, symbol = bar_source.nextBars()
    while not bars is None:
        code = bars[0].symbol
        print(f"start:{code}")
        strategy.onBegin(code)
        for bar in bars:
            _buy_or_sell = strategy.is_buy_or_sell(bar)
            ###是否持有
            if _buy_or_sell is None:
                pass
            elif _buy_or_sell:
                ## 买入
                if not trader.hasBuy(bar.symbol):
                    the_buy_price = bar.close_price * 1.001  # 上一个交易日的收盘价作为买入价
                    trader.buy(bar.symbol, the_buy_price, bar.datetime)
            else:
                ## 卖出
                if trader.hasBuy(bar.symbol):
                    sell_Price = bars[-1].close_price * 0.999  # 上一个交易日的收盘价作为买如价
                    trader.sell(bar.symbol, sell_Price, bar.datetime)
            trader.watch(bar.datetime)
        trader.resetWatch()
        strategy.onEnd(code)
        bars, symbol = bar_source.nextBars()


drvier1 = StockIndexDriver()
drvier2 = SW2Driver()
app = App()
start = datetime(year=2020,month=1,day=1)
end = datetime(year=2021,month=3,day=20)
bar_source = app.getBarManager().createBarSoruce([drvier2],Interval.DAILY,start,end)


trader = SimpleTrader()
analysis_buy_or_sell_strategy(bar_source,macd_Strategy(),trader)
trader.print()
