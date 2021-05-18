
"""
行情数据驱动器。
"""
from datetime import datetime
from abc import abstractmethod
from typing import Sequence
from earnmi.core.Context import Context,ContextWrapper
from earnmi.data.BarStorage import BarStorage
from earnmi.model.bar import LatestBar, BarData
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval

__all__ = [
    # Super-special typing primitives.
    'DayRange',
    'BarDriver',
]

class DayRange:

    def start(self)->datetime:
        pass

    def end(self)->datetime:
        pass

    def items(self)->Sequence['datetime']:
        pass


class BarDriver:

    """
    股票驱动名称。
    """
    @abstractmethod
    def get_name(self):
        """
        股票池驱动的名称。
        """
        raise RuntimeError("未实现")

    def get_description(self):
        """
        该驱动器的描述
        """
        return ""

    @abstractmethod
    def get_symbol_lists(self):
        """
        该驱动名称的成分股代码(成分股可能是指数，行业代码，股票代码，合约代码)
        """
        raise RuntimeError("未实现")

    @abstractmethod
    def get_symbol_name(self, symbol: str):
        """
          对应成分股代码的名称。
        """
        raise RuntimeError("未实现")

    @abstractmethod
    def get_sub_symbol_lists(self,symobl:str):
        """
        参数：返回该成分股下的所有的子成分股
        """
        return None



    @abstractmethod
    def support_interval(self, interval: Interval) -> bool:
        """
        支持的行情粒度。分为分钟、小时、天、周
        """
        raise RuntimeError("未实现")


    @abstractmethod
    def download_bars_from_net(self, context:Context, symbol:str, days:DayRange, storage: BarStorage):
        """
        下载历史行情数据到数据库。
        参数:
            day_list： 下载的所有日期
            storage：下载完成之后保存的数据库对象
        """
        raise RuntimeError("未实现")

    @abstractmethod
    def fetch_latest_bar(self,symbol_list:['str'])->Sequence["LatestBar"]:
        """
        获取今天的行情数据。如果今天没有开盘的话，换回None。
        """
        raise RuntimeError("未实现")

    @abstractmethod
    def fetch_latest_bar_for_backtest(self, symbol_list: ['str'],now_time:datetime,storage:BarStorage) -> Sequence["LatestBar"]:
        """
        获取回测环境的今天的行情数据。如果今天没有开盘的话，换回None。
        """
        if self.support_interval(Interval.MINUTE):
            raise RuntimeError("分钟行情方式，待实现")
        elif not self.support_interval(Interval.DAILY):
            raise RuntimeError("该driver 无法在回测环境使用")

        if now_time.hour ==14 and now_time.minute < 49 or now_time.hour < 14:
            raise RuntimeError("由于只含有日行情，在回测环境必须在14:49以上时间回调")
        start = utils.to_start_date(now_time)
        end = utils.to_end_date(now_time)
        laterst_bars = []
        for symbol in symbol_list:
            bars = self.load_bars(symbol,Interval.DAILY,start,end,storage)
            if len(bars) > 0:
                bar:BarData = bars[0]
                latestBar = LatestBar(code=bar.symbol,datetime=now_time)
                latestBar.name = self.get_symbol_name(symbol)
                latestBar.volume = bar.volume
                latestBar.open_price = bar.open_price
                latestBar.high_price = bar.high_price
                latestBar.low_price = bar.low_price
                latestBar.close_price = bar.close_price
                laterst_bars.append(latestBar)
            else:
                laterst_bars.append(None)
        return laterst_bars

    def load_bars(self, symbol: str,interval:Interval, start: datetime,end:datetime, storage: BarStorage) -> Sequence["BarData"]:
        """
        从数据库加载行情。
        """
        return storage.load_bar_data(symbol,self.get_name(),interval,start,end)

    def load_newest_bar(self,symbol: str,interval:Interval,storage: BarStorage) -> BarData:
        return storage.get_newest_bar_data(symbol,self.get_name(),interval)

    def load_oldest_bar(self,symbol: str,interval:Interval,storage: BarStorage) -> BarData:
        return storage.get_oldest_bar_data(symbol,self.get_name(),interval)

    """
        驱动器分组名称，同一个GroupName名称会保存在同一个数据库文件。
    """
    def getDriverGroupName(self):
        return "__default__"

class BarStorageGroup:

    @abstractmethod
    def getStorage(self,driver:BarDriver) -> BarStorage:
        pass


