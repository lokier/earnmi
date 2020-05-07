from abc import abstractmethod, ABC
from copy import copy
from datetime import datetime
from typing import Any

from earnmi.strategy.StockStrategy import StockStrategy, Market
from vnpy.trader.utility import virtual


class StrategyTest(StockStrategy):

    def __init__(
            self,

    ):
       pass


    def on_create(self):
        """
        决策初始化.
        """
        self.write_log("on_create")
        pass

    def on_destroy(self):
        """
            决策结束.（被停止之后）
        """
        self.write_log("on_destroy")
        pass

    def on_market_prepare_open(self,market:Market):
        """
            市场准备开始（比如：竞价）.
        """
        self.write_log("on_market_prepare")

        market.buy("000034",344.23,200)

        pass




    def on_market_open(self,market:Market):
        """
            市场开市.
        """
        self.write_log("on_market_open")

        pass

    def on_market_prepare_close(self,market:Market):
        """
            市场准备关市.
        """
        self.write_log("on_market_prepare_close")
        market.sell("000034",344.23,200)

        pass

    def on_market_close(self,market:Market):
        """
            市场关市.
        """
        self.write_log("on_market_close")

        pass

    def on_bar_per_minute(self,time:datetime,market:Market):
        """
            市场开市后的每分钟。
        """
        self.write_log(f"on_bar_per_minute:{time}" )
        pass


