from abc import abstractmethod, ABC
from datetime import datetime
from typing import Sequence
from earnmi.data.Market import Market
from vnpy.app.cta_strategy import StopOrder
from vnpy.trader.object import TradeData, OrderData


class Portfolio:
    """
        证券账户.
    """

    """
       返回可用资金
    """
    @abstractmethod
    def getValidCapital(self)->float:
        pass

    """"
      返回持仓资金
    """
    @abstractmethod
    def getHoldCapital(self,refresh:bool = False)->float:
        pass

    def getTotalCapital(self)->float:
        return self.getHoldCapital() + self.getValidCapital()

    @abstractmethod
    def buy(self, code: str, price: float, volume: float)->bool:
        """
          买入股票
        """
        pass

    @abstractmethod
    def sell(self, code: str, price: float, volume: float) ->bool:
        """
          卖出股票
        """
        pass


    pass

"""
每一个交易日账户
"""
class DaliyPortfolio:

    """
    返回某个日期的交易记录
    """
    @abstractmethod
    def getTradeData(self) -> Sequence["TradeData"]:
        pass

    """
    返回某个日期的订单记录
    """
    @abstractmethod
    def getOrderData(self) -> Sequence["OrderData"]:
        pass

    @abstractmethod
    def today(self) -> datetime:
        pass

"""
回溯环境
"""
class BackTestContext:
    start_date:datetime = None
    end_date:datetime = None
    daily_results:{}
    size = 100
    rate = 0.0
    slippage = 0.0
    inverse = False
    capital = 0




"""
股票策略模块
"""
class StockStrategy(ABC):

    #是否在运行到回撤里面。
    mRunOnBackTest = False
    backtestContext:BackTestContext = None
    market:Market = None

    def __init__(
            self
    ):
       pass

    @abstractmethod
    def on_create(self):
        """
        决策初始化.
        """
        pass

    @abstractmethod
    def on_destroy(self):
        """
            决策结束.（被停止之后）
        """
        pass

    @abstractmethod
    def on_market_prepare_open(self,protfolio:Portfolio,toady:datetime):
        """
            市场准备开始（比如：竞价）.
        """
        pass


    @abstractmethod
    def on_market_open(self,protfolio:Portfolio):
        """
            市场开市.
        """
        pass

    @abstractmethod
    def on_market_prepare_close(self,protfolio:Portfolio):
        """
            市场准备关市.
        """
        pass

    @abstractmethod
    def on_market_close(self,protfolio:Portfolio):
        """
            市场关市.
        """
        pass

    @abstractmethod
    def on_bar_per_minute(self,time:datetime,protfolio:Portfolio):
        """
            市场开市后的每分钟。
        """
        pass

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        pass

    def on_stop_order(self, stop_order: StopOrder):
        pass

    def write_log(self,msg):
        print(f"StockStrategy: {msg}")
        pass


