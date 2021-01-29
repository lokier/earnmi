from datetime import datetime
from abc import abstractmethod
from typing import Sequence

from earnmi.core.Context import Context
from earnmi.data.BarDriver import DayRange
from earnmi.data.BarStorage import BarStorage
from earnmi.data.driver.JoinQuantBarDriver import JoinQuantBarDriver
from earnmi.data.driver.SinaUtil import SinaUtil
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
    def download_bars_from_net(self, context:Context, days:DayRange, storage: BarStorage):
        """
        只下载日行情。
        """
        return super().download_bars_daily(context,days.start(),days.end(),storage)

    @abstractmethod
    def fetch_latest_bar(self,symbol_list:['str'])->Sequence["LatestBar"]:
        assert len(symbol_list) == 1
        assert symbol_list[0] == StockIndexDriver.INDEX_SYMBOL
        """
        获取今天的行情数据。如果今天没有开盘的话，换回None。
        """
        return SinaUtil.fetch_latest_bar(['sh000001'])

if __name__ == "__main__":
    pass