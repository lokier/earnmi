from abc import abstractmethod, ABC
from datetime import datetime, timedelta

class Market:
    """
        市场.
    """

    @abstractmethod
    def buy(self, code:str,price: float, volume: float):
        """
          买入股票
        """
        pass

    @abstractmethod
    def sell(self,code:str, price: float, volume: float):
        """
          卖出股票
        """
        pass

    @abstractmethod
    def today(self)->datetime:
        pass


class Portfolio:
    """
        证券账户.
    """
    pass

"""
回溯环境
"""
class BackTestContext:
    start_date:datetime = None
    end_date:datetime = None

class StockStrategy(ABC):

    #是否在运行到回撤里面。
    mRunOnBackTest = False
    backtestContext:BackTestContext = None

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
    def on_market_prepare_open(self,market:Market):
        """
            市场准备开始（比如：竞价）.
        """
        pass


    @abstractmethod
    def on_market_open(self,market:Market):
        """
            市场开市.
        """
        pass

    @abstractmethod
    def on_market_prepare_close(self,market:Market):
        """
            市场准备关市.
        """
        pass

    @abstractmethod
    def on_market_close(self,market:Market):
        """
            市场关市.
        """
        pass

    @abstractmethod
    def on_bar_per_minute(self,time:datetime,market:Market):
        """
            市场开市后的每分钟。
        """
        pass

    def write_log(self,msg):
        print(f"StockStrategy: {msg}")
        pass


