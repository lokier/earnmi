from typing import List, Dict

from earnmi.data.import_tradeday_from_jqdata import TRAY_DAY_VT_SIMBOL, TRAY_DAY_SIMBOL, save_tradeday_from_jqdata
from earnmi.strategy.StockStrategy import StockStrategy, BackTestContext, Portfolio
from earnmi.uitl.utils import utils
from vnpy.app.portfolio_strategy import StrategyTemplate, StrategyEngine, BacktestingEngine

import copy
from datetime import datetime, timedelta

from vnpy.trader.constant import Interval, Exchange, Status, Direction
from vnpy.trader.database import database_manager
from vnpy.trader.object import TickData, BarData, OrderData, TradeData

class TradeOrderHold:
    symbol:str

    pass



class StockStrategyBridge(StrategyTemplate,Portfolio):

    myStrategy:StockStrategy = None
    __privous_on_bar_datime = None

    __daylyTradeSymbolset = {} # 每天有交易的code
    __vt_symbol_for_back_testing = {}

    _valid_captical = 0.0

    _commit_rate = 0.0 #交易费用
    _a_hand_size = 0.0 #每手有多少个
    __order_summitting_price = {}
    __holding_orders = {}

    def __init__(
            self,
            strategy_engine: StrategyEngine,
            strategy_name: str,
            vt_symbols: List[str],
            setting: dict
    ):
        super().__init__(strategy_engine, [TRAY_DAY_VT_SIMBOL], vt_symbols, setting)

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


    def on_init(self):
        """
        Callback when strategy is inited.
        """
        # self.write_log("策略初始化")
        # 应该是初始化bar
        # super.callback = self.__on_bar_dump
        self.myStrategy.mRunOnBackTest = isinstance(self.strategy_engine,BacktestingEngine)
        if(self.myStrategy.mRunOnBackTest):
            context = BackTestContext()
            context.start_date = self.strategy_engine.start
            context.end_date = self.strategy_engine.end
            self._valid_captical = self.strategy_engine.capital
            self._commit_rate = self.strategy_engine.rates[TRAY_DAY_VT_SIMBOL]
            self._a_hand_size = self.strategy_engine.sizes[TRAY_DAY_VT_SIMBOL]

            self.myStrategy.backtestContext = context
            self.__init_tradeDay(context.start_date,context.end_date)
            self.__holding_orders.clear()
        else:
            self.myStrategy.backtestContext = None

        self.load_bars(0)

    def __init_tradeDay(self,start:datetime,end:datetime):

        code = TRAY_DAY_SIMBOL

        db_bar_start = database_manager.get_oldest_bar_data(code,Exchange.SSE,Interval.DAILY)
        db_bar_end = database_manager.get_newest_bar_data(code,Exchange.SSE,Interval.DAILY)

        print(f"StrategyBridage: __init_tradeDay(), start={start},end={end}")

        if((not db_bar_start is None ) and (not db_bar_end is None)):
            if(start >= db_bar_start.datetime and end <= db_bar_end.datetime):
                return

        print(f"StrategyBridage: __init_tradeDay(), update tradeDay!!!!")
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

    def on_tick(self, tick: TickData) -> None:
        pass

    def on_bars(self, bars: Dict[str, BarData]) -> None:

        if(not self.isCreated):
            return

        if (self.myStrategy.mRunOnBackTest):

            self.__cancel_all_order()
            self.__order_summitting_price.clear()
            self.__daylyTradeSymbolset.clear()
            bar = bars[TRAY_DAY_VT_SIMBOL]

            bar.low_price = 100
            bar.high_price = 100
            bar.open_price = 100
            bar.close_price = 100
            bar.open_interest = 0

            day = datetime(year=bar.datetime.year, month=bar.datetime.month, day=bar.datetime.day, hour=9, minute=25, second=1)
            self.today = day
            self.strategy_engine.datetime = day
            self.myStrategy.market.setToday(self.today)

            self.myStrategy.on_market_prepare_open(self,self.today)
            self.myStrategy.on_market_open(self)

            tradeTime = datetime(year=day.year, month=day.month, day=day.day, hour=9, minute=30, second=1)
            end_date = datetime(year=day.year, month=day.month, day=day.day, hour=11, minute=30, second=1)

            while (tradeTime.__le__(end_date)):
                self.today = tradeTime
                self.strategy_engine.datetime = tradeTime
                self.myStrategy.market.setToday(tradeTime)
                self.myStrategy.on_bar_per_minute(tradeTime,self)
                tradeBar = copy.deepcopy(bar)
                tradeBar.datetime = tradeTime
                self.__cross_order_by_per_miniute(tradeBar)
                tradeTime = tradeTime + timedelta(minutes=1)

            tradeTime = datetime(year=day.year, month=day.month, day=day.day, hour=13, minute=0, second=1)
            end_date = datetime(year=day.year, month=day.month, day=day.day, hour=15, minute=0, second=1)
            while (tradeTime.__le__(end_date)):
                self.today = tradeTime
                self.strategy_engine.datetime = tradeTime
                self.myStrategy.market.setToday(tradeTime)
                self.myStrategy.on_bar_per_minute(tradeTime,self)
                tradeBar = copy.deepcopy(bar)
                tradeBar.datetime = tradeTime
                self.__cross_order_by_per_miniute(tradeBar)
                tradeTime = tradeTime + timedelta(minutes=1)

            self.myStrategy.on_market_prepare_close(self)
            self.myStrategy.on_market_close(self)

            ###每次成完之后，把订单里的成交情况放在bars里面
            code_ids = list(self.__daylyTradeSymbolset.keys())
            for code in code_ids:
                self.__vt_symbol_for_back_testing[self.__to_vt_symbol(code)] = True
                bar = self.myStrategy.market.getRealTime().getKBar(code)
                if(not bar is None):
                    symbol = self.__to_vt_symbol(code)
                    bars[symbol] = bar
            self.__daylyTradeSymbolset.clear()

            ##情况当前订单
            self.__cancel_all_order()
            self.__order_summitting_price.clear()

            pass

        """
        Callback of new bar data update.
        """
        pass

    def __cancel_all_order(self):
        assert self.myStrategy.mRunOnBackTest == True

        vt_orderids = list(self.strategy_engine.active_limit_orders.keys())
        for vt_orderid in vt_orderids:
            self.strategy_engine.cancel_order(self, vt_orderid)


    def __cross_order_by_per_miniute(self, tradeBar: BarData):
        """
        交割订单
        """
        assert self.myStrategy.mRunOnBackTest == True
        symobSet = {}
        for order in list(self.strategy_engine.active_limit_orders.values()):
            symobSet[order.symbol] = True

        orderSymbolSet = list(symobSet.keys())

        for symbol in orderSymbolSet:
            bar = self.myStrategy.market.getRealTime().getTick(symbol)
            if( bar is None):
                ###还没开始，或者已经停牌
                continue


            self.strategy_engine.cross_limit_order_by_bar(bar)

        pass

    def update_order(self, order: OrderData) -> None:
        super().update_order(order)
        if self.myStrategy.mRunOnBackTest == True:
            if(order.status == Status.CANCELLED or order.status == Status.REJECTED ):

                if(order.direction ==Direction.LONG):
                    order_price = self.__order_summitting_price.pop(order.vt_orderid)
                    assert  not order_price is None
                    self._valid_captical = self._valid_captical + order_price
                pass
            elif order.status == Status.PARTTRADED:
                #回撤中，没有部分成交的情况
                assert False
            elif order.status == Status.ALLTRADED:
                if (order.direction == Direction.LONG):
                    order_price = self.__order_summitting_price.pop(order.vt_orderid)
                    holdOrder = self.__holding_orders.get(order.symbol)
                    if holdOrder is None:
                        holdOrder = copy.deepcopy(order)
                        holdOrder.volume = 0
                        self.__holding_orders[order.symbol] = holdOrder

                    holdOrder.volume = holdOrder.volume + order.volume

                    assert not order_price is None
                elif (order.direction == Direction.SHORT):
                    new_valid_caption = (1 - self._commit_rate) * order.price * order.volume  * self._a_hand_size
                    self._valid_captical = self._valid_captical+ new_valid_caption
                    holdOrder = self.__holding_orders.get(order.symbol)
                    assert not holdOrder is None
                    holdOrder.volume = holdOrder.volume - order.volume


            elif order.status == Status.NOTTRADED or order.status == Status.SUBMITTING:
                pass
            else :
                ##回撤中，没有其它为处理的情况
                assert False

        self.myStrategy.on_order(order)

    def update_trade(self, trade: TradeData) -> None:
        """
        Callback of new trade data update.
        """
        super().update_trade(trade)
        self.myStrategy.on_trade(trade)


    def buy(self, code: str, price: float, volume: float) ->bool:
        """
        买入股票
        """
        symbol = self.__to_vt_symbol(code)

        if self.myStrategy.mRunOnBackTest == True:
            self.__daylyTradeSymbolset[code] = True
            self.strategy_engine.priceticks[symbol] = self.strategy_engine.priceticks[TRAY_DAY_VT_SIMBOL]
            self.strategy_engine.rates[symbol] = self.strategy_engine.rates[TRAY_DAY_VT_SIMBOL]
            self.strategy_engine.slippages[symbol] = self.strategy_engine.slippages[TRAY_DAY_VT_SIMBOL]
            self.strategy_engine.sizes[symbol] = self.strategy_engine.sizes[TRAY_DAY_VT_SIMBOL]

            need_capital =  (1 + self._commit_rate) * price * volume * self._a_hand_size

            if(need_capital >= self._valid_captical):
                print(f"     ==> buy {code} fail,可用资金不够：需要：{need_capital},可用{self._valid_captical}")
                return False
            self._valid_captical = self._valid_captical -  need_capital
            vt_order_id = super().buy(symbol, price, volume, False)
            self.__order_summitting_price[vt_order_id[0]] = need_capital

        else:
            super().buy(symbol, price, volume, False)

        return True

    def sell(self, code: str, price: float, volume: float)->bool:
        symbol = self.__to_vt_symbol(code)

        if self.myStrategy.mRunOnBackTest == True:
            hasVolume = 0
            holdOrder = self.__holding_orders.get(code)
            if not holdOrder is None:
                hasVolume = holdOrder.volume

            if(hasVolume < volume):
                print(f"     <== sell {code} fail,仓位不够：需要：{volume},可用{hasVolume}")
                return False

            self.__daylyTradeSymbolset[code] = True
            self.strategy_engine.priceticks[symbol] = self.strategy_engine.priceticks[TRAY_DAY_VT_SIMBOL]
            self.strategy_engine.rates[symbol] = self.strategy_engine.rates[TRAY_DAY_VT_SIMBOL]
            self.strategy_engine.slippages[symbol] = self.strategy_engine.slippages[TRAY_DAY_VT_SIMBOL]
            self.strategy_engine.sizes[symbol] = self.strategy_engine.sizes[TRAY_DAY_VT_SIMBOL]
            super().sell(symbol,price,volume,False)
        else:
            super().sell(symbol,price,volume,False)

        return True

    def getValidCapital(self) -> float:
        if self.myStrategy.mRunOnBackTest == True:
            return self._valid_captical

    def getHoldCapital(self) -> float:
        pass

    def write_log(self, msg):
        print(f"CtaStrategyBridage: {msg}")
        pass

    def __to_vt_symbol(self,code:str)->str:
       return utils.to_vt_symbol(code)

