from typing import Sequence

from earnmi.data.import_tradeday_from_jqdata import TRAY_DAY_VT_SIMBOL, TRAY_DAY_SIMBOL, save_tradeday_from_jqdata
from earnmi.strategy.StockStrategy import StockStrategy, BackTestContext, Portfolio
from earnmi.strategy.StrategyTest import StrategyTest
from earnmi_demo.Strategy1 import Strategy1
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData
)

from time import time
import copy
from vnpy.app.cta_strategy.base import EngineType
from datetime import datetime, timedelta

from vnpy.trader.constant import Direction, Offset, Interval, Exchange
from vnpy.trader.database import database_manager


class CtaStrategyBridage(CtaTemplate,Portfolio):
    myStrategy:StockStrategy = None
    __privous_on_bar_datime = None

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(CtaStrategyBridage, self).__init__(
            cta_engine, strategy_name, TRAY_DAY_VT_SIMBOL, setting
        )
        strategy = setting['strategy']

        if(strategy is None):
            raise RuntimeError("must set setting: 'strategy' ")

        if ( not isinstance(strategy,StockStrategy)):
            raise RuntimeError("must set setting: 'strategy' is StockStrategy object  ")

        self.myStrategy = strategy
        self.isCreated = False
        self.today= None

        if (self.myStrategy is None):
            raise RuntimeError("must set setting: 'strategy' ")


    def __on_bar_dump(self, bar: BarData):
        pass

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        # self.write_log("策略初始化")
        # 应该是初始化bar
        # super.callback = self.__on_bar_dump
        self.myStrategy.mRunOnBackTest = EngineType.BACKTESTING == self.get_engine_type();
        if(self.myStrategy.mRunOnBackTest):
            context = BackTestContext()
            context.start_date = self.cta_engine.start
            context.end_date = self.cta_engine.closeMarket
            self.myStrategy.backtestContext = context
            if(self.cta_engine.interval != Interval.DAILY):
                raise RuntimeError(f"error interval : {self.cta_engine.interval}")
            self.__init_tradeDay(context.start_date,context.end_date)

        else:
            self.myStrategy.backtestContext = None

        self.load_bar(0)

    def __init_tradeDay(self,start:datetime,end:datetime):

        code = TRAY_DAY_SIMBOL

        db_bar_start = database_manager.get_oldest_bar_data(code,Exchange.SSE,Interval.DAILY)
        db_bar_end = database_manager.get_newest_bar_data(code,Exchange.SSE,Interval.DAILY)

        print(f"CtaStrategyBridage: __init_tradeDay(), start={start},end={end}")

        if((not db_bar_start is None ) and (not db_bar_end is None)):
            if(start >= db_bar_start.datetime and end <= db_bar_end.datetime):
                return

        print(f"CtaStrategyBridage: __init_tradeDay(), update tradeDay!!!!")
        database_manager.delete_bar_data(code,Exchange.SSE,Interval.DAILY)

        start = start - timedelta(days=15)
        end = end + timedelta(days=15)
        save_tradeday_from_jqdata(start,end)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        #self.write_log("策略启动: " + self.get_engine_type().__str__());
        self.isCreated = True
        self.myStrategy.on_create()
        if(self.myStrategy.market is None):
            raise  RuntimeError("must set market")
        #;


    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.isCreated = False
        self.myStrategy.on_destroy()
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


    def on_bar(self, bar: BarData):

        if(not self.isCreated):
            return

        if (EngineType.BACKTESTING == self.get_engine_type()):

            #取消所有订单。
            self.cta_engine.cancel_all(self)

            self.today = bar.datetime
            self.myStrategy.market.setToday(bar.datetime)
            day = bar.datetime

            self.myStrategy.on_market_prepare_open(self,self.today)
            self.myStrategy.on_market_open(self)

            tradeTime = datetime(year=day.year, month=day.month, day=day.day, hour=9, minute=30, second=1)
            end_date = datetime(year=day.year, month=day.month, day=day.day, hour=11, minute=30, second=1)

            while (tradeTime.__le__(end_date)):
                self.myStrategy.market.setToday(tradeTime)
                self.myStrategy.on_bar_per_minute(tradeTime,self)
                tradeBar = copy.deepcopy(bar)
                tradeBar.datetime = tradeTime
                self.__cross_order_by_per_miniute(tradeBar)
                tradeTime = tradeTime + timedelta(minutes=1)

            tradeTime = datetime(year=day.year, month=day.month, day=day.day, hour=13, minute=0, second=1)
            end_date = datetime(year=day.year, month=day.month, day=day.day, hour=15, minute=0, second=1)
            while (tradeTime.__le__(end_date)):
                self.myStrategy.market.setToday(tradeTime)
                self.myStrategy.on_bar_per_minute(tradeTime,self)
                tradeBar = copy.deepcopy(bar)
                tradeBar.datetime = tradeTime
                self.__cross_order_by_per_miniute(tradeBar)
                tradeTime = tradeTime + timedelta(minutes=1)

            self.myStrategy.on_market_prepare_close(self)
            self.myStrategy.on_market_close(self)

            pass

        """
        Callback of new bar data update.
        """
        pass

    def __cross_order_by_per_miniute(self, tradeBar: BarData):
        """
        交割订单
        """
        for order in list(self.cta_engine.active_limit_orders.values()):

            bar = self.myStrategy.market.getRealTime().getKBar(order.symbol);

            if( bar is None):
                ###还没开始，或者已经停牌
                continue

            self.cta_engine.cross_limit_order_byBar(bar)

        pass

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
       # self.write_log("on_order")
        self.myStrategy.on_order(order)
        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.myStrategy.on_trade(trade)
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.myStrategy.on_stop_order(stop_order)
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

    def buy(self, code: str, price: float, volume: float):
            """
              买入股票
            """
            self.write_log(f"buy,code={code},price={price},volume={volume}")
            if self.trading:
                vt_orderids = self.cta_engine.send_limit_order(code, Direction.LONG, Offset.OPEN, price, volume)
                return vt_orderids
            else:
                return []

    def sell(self, code: str, price: float, volume: float):
        if self.trading:
            self.write_log(f"sell,code={code},price={price},volume={volume}")
            vt_orderids = self.cta_engine.send_limit_order(code, Direction.SHORT, Offset.CLOSE, price, volume)
            return vt_orderids
        else:
            return []




    def write_log(self, msg):
        print(f"CtaStrategyBridage: {msg}")
        pass


