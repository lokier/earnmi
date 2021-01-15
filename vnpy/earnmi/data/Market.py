import datetime
from typing import Sequence
from earnmi.model.bar import LatestBar
from vnpy.trader.constant import Interval
from vnpy.trader.object import BarData


class Market:
    """
    行情数据市场。
    需要设置BardataHander和股票池。
    """
    pass


    def getLatestBar(self, code: str) -> LatestBar:
        """
        返回某个股票的实时行情。
        """
        pass

    def getBarDataList(self, code: str,interval:Interval, start: datetime,end:datetime = None) -> Sequence["BarData"]:
        """
        返回股票的历史行情。不包含今天now的行情数据。
        """
        pass

    def setNow(self):
        """
        设置行情的now时间，now时间的不同，对应的实时行情和历史行情也不同。
        """
        pass

    def getNow(self)->datetime:
        pass

    def nextMarketDay(self):
        """
        跳转下一个交易日
        """
        pass