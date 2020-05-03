from abc import abstractmethod, ABC
from copy import copy
from typing import Any

from datetime import datetime, timedelta


class StockStrategy(ABC):

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
    def on_market_prepare_open(self):
        """
            市场准备开始（比如：竞价）.
        """
        pass


    @abstractmethod
    def on_market_open(self):
        """
            市场开市.
        """
        pass

    @abstractmethod
    def on_market_prepare_close(self):
        """
            市场准备关市.
        """
        pass

    @abstractmethod
    def on_market_close(self):
        """
            市场关市.
        """
        pass

    @abstractmethod
    def on_bar_per_minute(self,time:datetime):
        """
            市场开市后的每分钟。
        """
        pass

    def write_log(self,msg):
        print(f"StockStrategy: {msg}")
        pass


class Market:
    """
        市场.
    """

    @abstractmethod
    def buy(self):
        """
        """
        pass

    def sell(self):
        pass


class Portfolio:
    """
        证券账户.
    """
    pass