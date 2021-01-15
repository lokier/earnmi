
"""
行情数据驱动器。
（行情数据保存到sqlite数据库)
"""
import datetime
from abc import abstractmethod
from typing import Sequence

from earnmi.model.bar import LatestBar
from vnpy.trader.constant import Interval
from vnpy.trader.object import BarData


class BarDataDriver:

    """
    某个股票池的行情数据库。
    """

    @abstractmethod
    def getCodes(self):
        """
        支持的股票代码池
        """
        pass

    def getCodeName(self,code:str):
        """
          对应股票代码的名称。
        """
        pass

    @abstractmethod
    def fetchBarData(self,code:str, start_date:datetime, end_date:datetime,interval:Interval)-> Sequence["BarData"]:
        """
        获取历史行情数据。
        """
        pass

    @abstractmethod
    def fetchLatestBar(self,code:str)->LatestBar:
        """
        获取今天的行情数据。如果今天没有开盘的话，换回None。
        """
        pass

