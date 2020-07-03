from typing import List, Dict

from earnmi.data.Market import Market
from earnmi.data.import_tradeday_from_jqdata import TRAY_DAY_VT_SIMBOL, TRAY_DAY_SIMBOL, save_tradeday_from_jqdata
from earnmi.strategy.StockStrategy import StockStrategy, BackTestContext, Portfolio, Position
from earnmi.uitl.utils import utils
from vnpy.app.portfolio_strategy import StrategyTemplate, StrategyEngine, BacktestingEngine

import copy
from datetime import datetime, timedelta

from vnpy.trader.constant import Interval, Exchange, Status, Direction, Offset
from vnpy.trader.database import database_manager
from vnpy.trader.object import TickData, BarData, OrderData, TradeData



"""
turnover = trade.volume * size * trade.price   持有仓位资金。
self.slippage += trade.volume * size * slippage   滑点的损失值。
self.commission += turnover * rate    交易费用
self.holding_pnl = self.start_pos * (self.close_price - self.pre_close) * size  * 当天持仓盈利（未交易的情况）
self.trading_pnl += pos_change * (self.close_price - trade.price) * size    交易后的持仓盈利
self.total_pnl = self.trading_pnl + self.holding_pnl  当天盈利
self.net_pnl = self.total_pnl - self.commission - self.slippage  扣除费用之后的盈利
"""

class PortfolioImpl(Portfolio):

    class Locking_Data:
        order_id: str
        code:str
        lock_price: float = 0.0  # 冻结的资金。
        lock_pos: float = 0.0  # 冻结的筹码。


    """
    账户交易资金
    """
    engine:StrategyEngine
    strategy: StrategyTemplate
    market:Market

    commit_rate = 0.0  # 交易费用
    a_hand_size = 0.0  # 每手有多少个
    valid_captical = 0.0 #可用资金
    slippage = 0.0
    pricetick=0.01  #四舍五入的精度

    __daylyTradeCodeSet = {} # 每天有交易的code
    __locking_data:dict[str, Locking_Data] = {}  #冻结的资金或者筹码

    __longPositions:dict[str,Position] = {}
    __shortPositions:dict[str,Position] = {}

    def __init__(
            self,
            engine: StrategyEngine,
            strategy:StrategyTemplate,
            market: Market
    ):
        self.engine = engine
        self.valid_captical = self.engine.capital
        self.commit_rate = self.engine.rates[TRAY_DAY_VT_SIMBOL]
        self.a_hand_size = self.engine.sizes[TRAY_DAY_VT_SIMBOL]
        self.slippage = self.engine.slippages[TRAY_DAY_VT_SIMBOL]
        self.pricetick =self.engine.priceticks[TRAY_DAY_VT_SIMBOL]
        self.strategy = strategy
        self.market = market

    def getLongPosition(self, code) -> Position:
        return self.getLongPositionBySymbol(utils.to_vt_symbol(code),code)

    def getLongPositionBySymbol(self, symbol:str,code:str = None) -> Position:
        pos = self.__longPositions.get(symbol)
        if(pos is None):
            if code is None:
                raise RuntimeError("none error")
            pos = Position(code = code, is_long=True)
            pos.price = 0
            pos.symobl = symbol
            self.__longPositions[symbol] = pos
        return pos

    """
        做空持仓清空
    """
    def getShortPosition(self, code) -> Position:
        return self.getShortPositionBySymbol(utils.to_vt_symbol(code))

    def getShortPositionBySymbol(self, symbol:str,code:str = None) -> Position:
        pos = self.__shortPositions.get(symbol)
        if (pos is None):
            if code is None:
                raise RuntimeError("none error")
            pos = Position(code=code, is_long=False)
            pos.price = 0
            pos.symobl = symbol
            self.__shortPositions[symbol] = pos
        return pos

    def buy(self, code: str, price: float, volume: float) ->bool:
        """
        买入股票
        """
        need_capital = (1 + self.commit_rate) * price * volume * self.a_hand_size
        if (need_capital >= self.valid_captical):
            print(f"     ==> buy {code} fail,可用资金不够：需要：{need_capital},可用{self.valid_captical}")
            return False
        symbol = utils.to_vt_symbol(code)
        self.__initTrade(code,symbol)
        self.valid_captical = self.valid_captical - need_capital
        vt_order_ids = self.strategy.buy(symbol, price, volume, False)

        ###冻结资金
        lockingDagta = PortfolioImpl.Locking_Data(order_id = vt_order_ids[0], code=code)
        lockingDagta.lock_price = need_capital
        self.__locking_data[lockingDagta.order_id] = lockingDagta


        return True

    def sell(self, code: str, price: float, volume: float)->bool:

        hasVolume = self.getLongPosition(code).pos_available / self.a_hand_size

        if (hasVolume < volume):
            print(f"     <== sell {code} fail,仓位不够：需要：{volume},可用{hasVolume}")
            return False
        symbol = utils.to_vt_symbol(code)
        self.__initTrade(code,symbol)
        vt_order_ids = self.strategy.sell(symbol, price, volume, False)

        ###冻结仓位，今天不可以再交易
        lockingDagta = PortfolioImpl.Locking_Data(order_id=vt_order_ids[0], code=code)
        lockingDagta.lock_pos = volume * self.a_hand_size
        self.__locking_data[lockingDagta.order_id] = lockingDagta

        return True

    def short(self, code: str, price: float, volume: float) -> bool:
        """
          做空股票：开仓
        """
        pass

    def cover(self, code: str, price: float, volume: float) -> bool:
        """
        做空股票：平仓
        """
        pass

    def __initTrade(self,code:str, symbol: str):
        self.engine.priceticks[symbol] = self.pricetick
        self.engine.rates[symbol] = self.commit_rate
        self.engine.slippages[symbol] = self.slippage
        self.engine.sizes[symbol] = self.a_hand_size
        self.__daylyTradeCodeSet[code] = True

    def cancel_all_order(self):
        vt_orderids = list(self.engine.active_limit_orders.keys())
        for vt_orderid in vt_orderids:
             self.engine.cancel_order(self.strategy, vt_orderid)


    def getValidCapital(self) -> float:
        return self.valid_captical

    def getHoldCapital(self,refresh:bool = False)->float:

        if (refresh):
            self._refresh_holde_order_price()

        hold_captital = 0
        for hold_order in list(self.__holding_orders.values()):
            if hold_order.volume > 0:
                hold_captital = hold_order.volume * hold_order.price * self.a_hand_size
        return hold_captital

    def _on_today_start(self):
        ##新的一天是所有订单是空的
        assert len(self.engine.active_limit_orders) == 0
        self.__locking_data.clear()
        self.__daylyTradeCodeSet.clear()

    def _on_today_end(self,bars: Dict[str, BarData]):
        self.cancel_all_order()

        code_ids = list(self.__daylyTradeCodeSet.keys())
        for code in code_ids:
            bar = self.market.getRealTime().getKBar(code)
            if (not bar is None):
                symbol = utils.to_vt_symbol(code)
                bars[symbol] = bar

        ##所有的订单都得处理完
        assert len(self.engine.active_limit_orders) == 0
        self.__daylyTradeCodeSet.clear()
        self.__locking_data.clear()

    def _on_update_trade(self, trade: TradeData) -> None:
        """
        Callback of new trade data update.
        """
        pass

    def _on_update_order(self, order: OrderData) -> None:
        is_buy = order.direction == Direction.LONG and order.offset == Offset.OPEN
        is_sell = order.direction == Direction.SHORT and order.offset == Offset.CLOSE
        is_short = order.direction == Direction.SHORT and order.offset == Offset.OPEN
        is_cover = order.direction == Direction.LONG and order.offset == Offset.CLOSE

        if (order.status == Status.CANCELLED or order.status == Status.REJECTED):
            if (is_buy or is_short):
                #恢复冻结的资金
                locking_data = self.__locking_data.pop(order.vt_orderid)
                assert not locking_data is None
                self.valid_captical = self.valid_captical + locking_data.lock_price
            pass
        elif order.status == Status.PARTTRADED:
            # 回撤中，没有部分成交的情况
            assert False
        elif order.status == Status.ALLTRADED:
            if (is_buy):
                ##冻结资金生效
                locking_data = self.__locking_data.pop(order.vt_orderid)
                assert not locking_data is None

                ##增加仓位
                pos = self.getLongPositionBySymbol(order.symbol)
                new_pos_size = order.volume * self.a_hand_size
                pos.pos_total += new_pos_size
                pos.pos_lock += new_pos_size

            elif (is_sell):
                #新可用资金
                new_valid_caption = (1 - self.commit_rate) * order.price * order.volume * self.a_hand_size
                self.valid_captical = self.valid_captical + new_valid_caption

                ##减少仓位
                pos = self.getLongPositionBySymbol(order.symbol)
                pos_size = order.volume * self.a_hand_size
                pos.pos_total -= pos_size
                assert pos.pos_total>= 0
                assert pos.pos_total>= pos.pos_lock


        elif order.status == Status.NOTTRADED or order.status == Status.SUBMITTING:
            pass
        else:
            ##回撤中，没有其它为处理的情况
            assert False

    def _refresh_holde_order_price(self):


        for hold_order in list(self.__holding_orders.values()):
            if hold_order.volume > 0:
                hold_order.price = self.market.getRealTime().getTick(hold_order.symbol).close_price



class StockStrategyBridge(StrategyTemplate):

    myStrategy:StockStrategy = None
    __privous_on_bar_datime = None
    __portfolio:PortfolioImpl = None

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

            self.myStrategy.backtestContext = context
            self.__init_tradeDay(context.start_date,context.end_date)
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
        self.__portfolio = PortfolioImpl(self.strategy_engine,self,self.myStrategy.market)



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

            self.__portfolio._on_today_start()


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

            self.myStrategy.on_market_prepare_open(self.__portfolio,self.today)
            self.myStrategy.on_market_open(self.__portfolio)

            tradeTime = datetime(year=day.year, month=day.month, day=day.day, hour=9, minute=30, second=1)
            end_date = datetime(year=day.year, month=day.month, day=day.day, hour=11, minute=30, second=1)

            while (tradeTime.__le__(end_date)):
                self.today = tradeTime
                self.strategy_engine.datetime = self.today
                self.myStrategy.market.setToday(self.today)
                self.myStrategy.on_bar_per_minute(tradeTime,self.__portfolio)
                self.__cross_order_by_per_miniute()
                tradeTime = tradeTime + timedelta(minutes=1)

            tradeTime = datetime(year=day.year, month=day.month, day=day.day, hour=13, minute=0, second=1)
            end_date = datetime(year=day.year, month=day.month, day=day.day, hour=14, minute=26, second=1)
            while (tradeTime.__le__(end_date)):
                self.today = tradeTime
                self.strategy_engine.datetime = self.today
                self.myStrategy.market.setToday(self.today)
                self.myStrategy.on_bar_per_minute(tradeTime,self.__portfolio)
                self.__cross_order_by_per_miniute()
                tradeTime = tradeTime + timedelta(minutes=1)

            #parea close
            self.today = datetime(year=day.year, month=day.month, day=day.day, hour=14, minute=57, second=1)
            self.strategy_engine.datetime = self.today
            self.myStrategy.market.setToday(self.today)
            self.myStrategy.on_market_prepare_close(self.__portfolio)
            self.__cross_order_by_per_miniute()


            #close
            self.today = datetime(year=day.year, month=day.month, day=day.day, hour=15, minute=0, second=1)
            self.strategy_engine.datetime = self.today
            self.myStrategy.market.setToday(self.today)
            self.myStrategy.on_market_close(self.__portfolio)
            self.__cross_order_by_per_miniute()


            ##情况当前订单
            self.__portfolio._on_today_end(bars)


            pass

        """
        Callback of new bar data update.
        """
        pass




    def __cross_order_by_per_miniute(self):
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

        self.__portfolio._refresh_holde_order_price()
        pass

    def update_order(self, order: OrderData) -> None:
        super().update_order(order)
        self.__portfolio._on_update_order(order)
        self.myStrategy.on_order(order)

    def update_trade(self, trade: TradeData) -> None:
        """
        Callback of new trade data update.
        """
        super().update_trade(trade)
        self.__portfolio._on_update_trade(trade)
        self.myStrategy.on_trade(trade)



    def write_log(self, msg):
        print(f"CtaStrategyBridage: {msg}")
        pass



