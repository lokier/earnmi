from earnmi.data.MarketImpl import MarketImpl
from earnmi.data.import_tradeday_from_jqdata import TRAY_DAY_VT_SIMBOL
from earnmi.strategy.CtaStrategyBridge import CtaStrategyBridage
from earnmi.strategy.FundsFavouriteStrategy import FundsFavouriteStrategy
from earnmi.strategy.StockStrategy import StockStrategy, Portfolio
from earnmi.strategy.TestMultiStrategy import TestMultiStrategy
from vnpy.app.cta_strategy import StopOrder
from vnpy.app.cta_strategy.strategies.test_strategy import TestStrategy
from vnpy.event import Event
from vnpy.trader.constant import Interval

from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import (
    AtrRsiStrategy
)
from datetime import datetime

from vnpy.trader.object import OrderData, TradeData


def is_same_day(d1: datetime, d2: datetime) -> bool:
    return d1.day == d2.day and d1.month == d2.month and d1.year == d2.year

def is_same_minitue(d1: datetime, d2: datetime) -> bool:
    return is_same_day(d1,d2) and d1.hour == d2.hour and d1.minute == d2.minute


class StrategyTest(StockStrategy):

    market_open_count = 0
    start_trade_time = None
    end_trade_time =None

    def __init__(
            self,

    ):
       pass

    def on_create(self):
        """
        决策初始化.
        """
        self.market_open_count = 0
        self.market = MarketImpl()


        self.market.addNotice("601318") ##工商银行

        if (not self.backtestContext is None):
            # 从网络上面准备数据。
            self.write_log(f"on_create from backtestEngine, start={self.backtestContext.start_date},end={self.backtestContext.end_date}")
        else:
            self.write_log("on_create")
        pass

    def on_destroy(self):
        """
            决策结束.（被停止之后）
        """
        self.write_log("on_destroy")
        pass

    def on_market_prepare_open(self,protfolio:Portfolio,toady:datetime):
        """
            市场准备开始（比如：竞价）.
        """
        assert is_same_day(toady,self.market.getToday())

        if(self.start_trade_time is None) :
            self.start_trade_time = toady
        self.end_trade_time = toady

        pass




    def on_market_open(self,protfolio:Portfolio):
        """
            市场开市.
        """
        self.market_open_count = self.market_open_count + 1

        # 中国平安601318 在datetime(2019, 2, 26, 10, 28)时刻，最低到达 low_price=67.15
        # 中国平安601318 在datetime(2019, 2, 27, 9, 48)时刻，最高到达 high_price=68.57
        if(is_same_day(datetime(2019, 2, 26, 10, 28),self.market.getToday())):
            protfolio.buy("601318",67.15,10000)

        if (is_same_day(datetime(2019, 2, 27, 10, 28), self.market.getToday())):
            protfolio.sell("601318", 68.57, 10000)
        pass

    def on_market_prepare_close(self,protfolio:Portfolio):
        """
            市场准备关市.
        """

        pass

    def on_market_close(self,protfolio:Portfolio):
        """
            市场关市.
        """

        pass

    def on_bar_per_minute(self, time: datetime,protfolio:Portfolio):
        """
            市场开市后的每分钟。
        """
        assert is_same_minitue(time,self.market.getToday())

        #self.write_log(f"     on_bar_per_minute:{time}" )
        pass

    def on_order(self, order: OrderData):
        print(f"{self.market.getToday()}：onOrder: {order}")


    def on_trade(self, trade: TradeData):
        print(f"{self.market.getToday()}：on_trade: {trade}")

        # 中国平安601318 在datetime(2019, 2, 26, 10, 28)时刻，最低到达 low_price=67.15
        # 中国平安601318 在datetime(2019, 2, 27, 9, 48)时刻，最高到达 high_price=68.57
        buy_trade_time = datetime(2019, 2, 26, 10, 28)
        if (is_same_day(buy_trade_time, self.market.getToday())):
             assert self.market.getToday() >= buy_trade_time

        # if (is_same_minitue(datetime(2019, 2, 27, 10, 28), self.market.getToday())):
        #      protfolio.sell("601318", 68.57, 10000)

    def on_stop_order(self, stop_order: StopOrder):
        print(f"{self.market.getToday()}：on_stop_order: {stop_order}")


###------------------main---------------------------

engine = BacktestingEngine()
strategy = StrategyTest()

"""
 交易日开始时间 2019, 2, 25 ，交易日结束时间：2019, 4, 24
  
"""
start = datetime(2019, 2, 23)
end = datetime(2019, 4, 24)


engine.set_parameters(
    vt_symbol=TRAY_DAY_VT_SIMBOL,
    interval=Interval.DAILY,
    start=start,
    end=end,
    rate=0.3/10000,
    slippage=0.2,
    size=300,
    pricetick=0.2,
    capital=1_000_000,
)
engine.add_strategy(CtaStrategyBridage, { "strategy":strategy})
engine.load_data()
engine.run_backtesting()
# df = engine.calculate_result()
# engine.calculate_statistics()

assert is_same_day(datetime(year=2019,month=2,day=25),strategy.start_trade_time)
assert is_same_day(datetime(year=2019,month=4,day=24),strategy.end_trade_time)

assert  strategy.market_open_count == 42

for trade in engine.trades.values():
    print(trade)



