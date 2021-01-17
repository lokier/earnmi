import datetime
from typing import Sequence

from earnmi.core.Context import Context
from earnmi.data.BarDataDriver import BarDataDriver
from earnmi.model.bar import LatestBar
from vnpy.trader.constant import Interval
from vnpy.trader.object import BarData


class Market:
    
    """
    行情数据市场。
    为了加快访问，数据库存储的行情数据。
    """
    def __init__(self,context:Context):
        self.context:Context = context

    def registerDriver(self,driver:BarDataDriver):
        """
        注册股票池行情驱动器
        """
        pass

    def ueregisterDriver(self,driver:BarDataDriver):
        pass

    def updateFromNet(self,start:datetime,end:datetime,force_update = False):
        """
        更新数据库。
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
        """
        pass

    def getNow(self)->datetime:
        """
         返回行情的now时间，now时间的不同，对应的实时行情和历史行情也不同。
        """
        return self.context.now();

    def nextMarketDay(self):
        """
        跳转下一个交易日
        """
        pass


class MarketDataBarStorage:

    """
    市场行情数据库。
    """
    def __init__(self):
        pass