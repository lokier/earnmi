from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence
from earnmi.data.Market import Market
from vnpy.app.cta_strategy import StopOrder
from vnpy.trader.object import TradeData, OrderData

@dataclass
class Position:
    symobl: str
    is_long: bool = True
    pos_total: int = 0
    pos_lock: int = 0  #冻结的仓位

class Portfolio:
    """
        账户信息.
    """

    """
       返回可用资金
    """
    @abstractmethod
    def getValidCapital(self)->float:
        pass

    """"
      返回持仓市值
    """
    @abstractmethod
    def getHoldCapital(self,refresh:bool = False)->float:
        pass
    """
    返回资金总市值
    """
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

    @abstractmethod
    def short(self, code: str, price: float, volume: float) -> bool:
        """
          做空股票：开仓
        """
        pass

    @abstractmethod
    def cover(self, code: str, price: float, volume: float) ->bool:
        """
        做空股票：平仓
        """
        pass

    """
       做多持仓情况
    """
    @abstractmethod
    def getLongPosition(self, code) -> Position:
        pass

    """
        做空持仓清空
    """
    @abstractmethod
    def getShortPosition(self,code) -> Position:
        pass


"""
回溯环境
"""
class BackTestContext:
    start_date:datetime = None
    end_date:datetime = None
    # daily_results:{}
    # size = 100
    # rate = 0.0
    # slippage = 0.0
    # inverse = False
    # capital = 0




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


