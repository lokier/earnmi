from earnmi.strategy.StockStrategy import StockStrategy
from earnmi.strategy.StrategyTest import StrategyTest
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData
)

from time import time

from vnpy.app.cta_strategy.base import EngineType
from datetime import datetime, timedelta


class CtaStrategyWrapper(CtaTemplate):
    myStragey:StockStrategy = StrategyTest()

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(CtaStrategyWrapper, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        #self.myStrategy = StrategyTest()
        self.isCreated = False

    def __on_bar_dump(self, bar: BarData):
        pass

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        #self.write_log("策略初始化")
        #应该是初始化bar
        #super.callback = self.__on_bar_dump
        self.load_bar(0)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        #self.write_log("策略启动: " + self.get_engine_type().__str__());
        self.isCreated = True
        self.myStragey.on_create()
        #;


    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.isCreated = False
        self.myStragey.on_destroy()
        #self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        if self.test_all_done:
            return

        self.last_tick = tick

        self.tick_count += 1
        if self.tick_count >= self.test_trigger:
            self.tick_count = 0

            if self.test_funcs:
                test_func = self.test_funcs.pop(0)

                start = time()
                test_func()
                time_cost = (time() - start) * 1000
                self.write_log("耗时%s毫秒" % (time_cost))
            else:
                self.write_log("测试已全部完成")
                self.test_all_done = True

        self.put_event()

    __privous_on_bar_datime = None

    def on_bar(self, bar: BarData):

        if(not self.isCreated):
            return

        if (EngineType.BACKTESTING == self.get_engine_type()):

            self.myStragey.on_market_prepare_open()
            self.myStragey.on_market_open()

            day = bar.datetime
            tradeTime = datetime(year=day.year, month=day.month, day=day.day, hour=9, minute=30, second=1)
            end_date = datetime(year=day.year, month=day.month, day=day.day, hour=11, minute=30, second=1)

            while (tradeTime.__le__(end_date)):
                self.myStragey.on_bar_per_minute(tradeTime)
                tradeTime = tradeTime + timedelta(minutes=1)

            tradeTime = datetime(year=day.year, month=day.month, day=day.day, hour=13, minute=0, second=1)
            end_date = datetime(year=day.year, month=day.month, day=day.day, hour=15, minute=0, second=1)
            while (tradeTime.__le__(end_date)):
                self.myStragey.on_bar_per_minute(tradeTime)
                tradeTime = tradeTime + timedelta(minutes=1)

            self.myStragey.on_market_prepare_close()
            self.myStragey.on_market_close()

            pass

        """
        Callback of new bar data update.
        """
        pass

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()

    def test_market_order(self):
        """"""
        self.buy(self.last_tick.limit_up, 1)
        self.write_log("执行市价单测试")

    def test_limit_order(self):
        """"""
        self.buy(self.last_tick.limit_down, 1)
        self.write_log("执行限价单测试")

    def test_stop_order(self):
        """"""
        self.buy(self.last_tick.ask_price_1, 1, True)
        self.write_log("执行停止单测试")

    def test_cancel_all(self):
        """"""
        self.cancel_all()
        self.write_log("执行全部撤单测试")
