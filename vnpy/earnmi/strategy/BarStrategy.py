
'''
单个股票的买入卖出策略类。 计算买入点和卖出点的 。
缺点：
+ 可能持有周期太长，没有止损点操作，对于买入点产出之后的中途走势异样没有修正。
+ 卖出点没有细分：止损点和止盈点，比较粗糙。

'''
from earnmi.chart.Indicator import Indicator
from earnmi.data.BarSoruce import BarSource
from earnmi.data.BarTrader import SimpleTrader


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

def analysis_BuyOrSellStrategy(source: BarSource, strategy: BuyOrSellStrategy, trader: SimpleTrader):
    source.reset()
    bars, symbol = source.nextBars()
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
        bars, symbol = source.nextBars()