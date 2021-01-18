
"""
行情数据驱动器。
（行情数据保存到sqlite数据库)
"""
import datetime
from abc import abstractmethod
from typing import Sequence

from earnmi.data.BarStorage import BarStorage
from earnmi.model.bar import LatestBar
from vnpy.trader.constant import Interval
from vnpy.trader.object import BarData


class BarDriver:

    """
    股票驱动名称。
    """
    @abstractmethod
    def getName(self):
        """
        股票池驱动的名称。
        """
        pass

    @abstractmethod
    def getSymbolLists(self):
        """
        支持的股票代码列表
        """
        pass

    def getDescription(self):
        pass

    def getSymbolName(self,symbol:str):
        """
          对应股票代码的名称。
        """
        pass

    def support_interval(self,interval:Interval)->bool:
        """
        是否支持的行情粒度。分为分钟、小时、天、周
        """
        return False



    @abstractmethod
    def download_bars_from_net(self, start_date: datetime, end_date: datetime, storage: BarStorage):
        """
        下载历史行情数据到数据库。
        """
        pass

    @abstractmethod
    def fetch_latest_bar(self,code:str)->LatestBar:
        """
        获取今天的行情数据。如果今天没有开盘的话，换回None。
        """
        pass


class BarDriverManager:
    pass





