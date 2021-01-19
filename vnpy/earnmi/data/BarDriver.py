
"""
行情数据驱动器。
"""
import datetime
from abc import abstractmethod
from typing import Callable
from earnmi.model.bar import LatestBar
from vnpy.trader.constant import Interval


class BarDriver:

    """
    股票驱动名称。
    """
    @abstractmethod
    def get_name(self):
        """
        股票池驱动的名称。
        """
        pass

    def get_description(self):
        """
        该驱动器的描述
        """
        pass

    @abstractmethod
    def get_symbol_lists(self):
        """
        支持的股票代码列表
        """
        pass


    @abstractmethod
    def get_symbol_name(self,symbol:str):
        """
          对应股票代码的名称。
        """
        pass

    @abstractmethod
    def support_interval(self,interval:Interval)->bool:
        """
        是否支持的行情粒度。分为分钟、小时、天、周
        """
        return False



    @abstractmethod
    def download_bars_from_net(self, start_date: datetime, end_date: datetime, save_bars: Callable):
        """
        下载历史行情数据到数据库。
        参数:
            start_date： 开始日期
            end_date:  结束日期
            save_bars: 回调函数
        """
        pass

    @abstractmethod
    def fetch_latest_bar(self,code:str)->LatestBar:
        """
        获取今天的行情数据。如果今天没有开盘的话，换回None。
        """
        pass








