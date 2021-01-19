import datetime
from abc import abstractmethod
from typing import Callable

from earnmi.data.BarDriver import BarDriver
from earnmi.model.bar import LatestBar
from vnpy.trader.constant import Interval


class StockIndexDriver(BarDriver):

    NAME:str = 'A股指数'
    DESCRIPTION:str = 'A股指数:上证指数、深证指数、创业指数'
    SYMBOAL_MAP = {
        '1A001':'上证指数',
        '399001': '上证指数',
        '399006': '创业板',
    }

    @abstractmethod
    def get_name(self):
        return StockIndexDriver.NAME

    def get_description(self):
        return StockIndexDriver.DESCRIPTION

    @abstractmethod
    def get_symbol_lists(self):
        return StockIndexDriver.SYMBOAL_MAP.keys()

    @abstractmethod
    def get_symbol_name(self,symbol:str)->str:
        return StockIndexDriver.SYMBOAL_MAP.get(symbol)

    @abstractmethod
    def support_interval(self,interval:Interval)->bool:
        return interval == Interval.DAILY

    @abstractmethod
    def download_bars_from_net(self, start_date: datetime, end_date: datetime, save_bars: Callable):
        """
        下载历史行情数据到数据库。
        """
        save_bars()
        pass

    @abstractmethod
    def fetch_latest_bar(self,code:str)->LatestBar:
        """
        获取今天的行情数据。如果今天没有开盘的话，换回None。
        """
        pass