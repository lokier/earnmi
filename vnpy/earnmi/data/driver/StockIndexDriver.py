from datetime import datetime
from abc import abstractmethod

from earnmi.core.Context import Context
from earnmi.data.BarDriver import JoinQuantBarDriver
from earnmi.data.BarStorage import BarStorage
from earnmi.model.bar import LatestBar
from vnpy.trader.constant import Interval


class StockIndexDriver(JoinQuantBarDriver):
    INDEX_SYMBOL = '000001.XSHG'

    NAME:str = 'A股指数'
    DESCRIPTION:str = 'A股指数:上证指数、深证指数、创业指数'
    SYMBOAL_MAP = {
        INDEX_SYMBOL:'上证指数',
    }


    @abstractmethod
    def get_name(self):
        return StockIndexDriver.NAME

    def get_description(self):
        return StockIndexDriver.DESCRIPTION

    @abstractmethod
    def get_symbol_lists(self):
        return list(StockIndexDriver.SYMBOAL_MAP.keys())

    @abstractmethod
    def get_symbol_name(self,symbol:str)->str:
        return StockIndexDriver.SYMBOAL_MAP.get(symbol)

    @abstractmethod
    def support_interval(self,interval:Interval)->bool:
        return interval == Interval.DAILY

    @abstractmethod
    def download_bars_from_net(self,context:Context, start_date: datetime, end_date: datetime,storage: BarStorage)->int:
        """
        只下载日行情。
        """
        return super().download_bars_daily(context,start_date,end_date,storage)

    @abstractmethod
    def fetch_latest_bar(self,code:str)->LatestBar:
        """
        获取今天的行情数据。如果今天没有开盘的话，换回None。
        """
        pass