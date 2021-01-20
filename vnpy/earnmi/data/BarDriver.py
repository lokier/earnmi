
"""
行情数据驱动器。
"""
from datetime import timedelta,datetime
from abc import abstractmethod
from enum import Enum
from typing import Sequence
from earnmi.core.Context import Context
from earnmi.data.BarStorage import BarStorage
from earnmi.model.bar import LatestBar, BarData
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval
import numpy as np


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
    def support_interval(self, interval: Interval) -> bool:
        """
        是否支持的行情粒度。分为分钟、小时、天、周
        """
        return False

    def load_bars(self, symbol: str,interval:Interval, start: datetime,end:datetime, storage: BarStorage) -> Sequence["BarData"]:
        """
        从数据库加载行情。
        """
        return storage.load_bar_data(symbol,self.get_name(),interval,start,end)

    def load_newest_bar(self,symbol: str,interval:Interval,storage: BarStorage) -> BarData:
        return storage.get_newest_bar_data(symbol,self.get_name(),interval)

    def load_oldest_bar(self,symbol: str,interval:Interval,storage: BarStorage) -> BarData:
        return storage.get_oldest_bar_data(symbol,self.get_name(),interval)


    @abstractmethod
    def download_bars_from_net(self, context:Context,start_date: datetime, end_date: datetime, storage: BarStorage):
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



class JoinQuantBarDriver(BarDriver):

    def to_jq_code(self,symbol:str)->str:
        return symbol

    @abstractmethod
    def download_bars_daily(self, context: Context,start_date: datetime, end_date: datetime,
                               storage: BarStorage) -> int:
        """
        只下载日行情。
        """
        download_cnt = 0
        start_date = utils.to_start_date(start_date)
        end_date = utils.to_end_date(end_date)
        for symbol in self.get_symbol_lists():
            newest_bar = storage.get_newest_bar_data(symbol, self.get_name(), Interval.DAILY)
            if newest_bar is None:
                # 不含数据，全量更新
                download_cnt += self._download_bars_from_jq(context, symbol, start_date, end_date, Interval.DAILY,
                                                              storage)
            else:
                # 已经含有数据，增量更新
                oldest_bar = storage.get_oldest_bar_data(symbol, self.get_name(), Interval.DAILY)
                assert not oldest_bar is None
                oldest_datetime = utils.to_end_date(oldest_bar.datetime - timedelta(days=1))
                if start_date < oldest_datetime:
                    download_cnt += self._download_bars_from_jq(context, symbol, start_date, oldest_datetime,
                                                                  Interval.DAILY, storage)
                newest_datetime = utils.to_start_date(newest_bar.datetime + timedelta(days=1))  ##第二天一开始
                if newest_datetime < end_date:
                    download_cnt += self._download_bars_from_jq(context, symbol, newest_datetime, end_date,
                                                                  Interval.DAILY, storage)

        return download_cnt

    def _download_bars_from_jq(self, context:Context,symbol:str, start_date: datetime, end_date: datetime,interval:Interval,storage: BarStorage)->int:
        from earnmi.uitl.jqSdk import jqSdk
        jq = jqSdk.get()
        frequency = "1d"
        batch_day = 900
        if interval == Interval.DAILY:
            frequency = "1d"
            batch_day = 900
        elif interval == Interval.MINUTE:
            frequency = '1m'
            batch_day = 4
        elif interval == Interval.HOUR:
            frequency = "1h"
            batch_day = 200
        else:
            raise RuntimeError(f"unsupport interval:{interval}")

        interval = Interval.DAILY
        batch_start = start_date
        saveCount = 0
        jq_code = self.to_jq_code(symbol)
        while (batch_start.__lt__(end_date)):
            batch_end = batch_start + timedelta(days=batch_day)
            batch_end = utils.to_end_date(batch_end)
            if (batch_end.__gt__(end_date)):
                batch_end = end_date

            prices = jq.get_price(jq_code, start_date=start_date, end_date=end_date,
                                  fields=['open', 'close', 'high', 'low', 'volume'], frequency=frequency)
            if (prices is None):
                break
            bars = []
            lists = np.array(prices)
            for rowIndex in range(0, lists.shape[0]):
                bar = self.toBarData(symbol,prices,rowIndex,interval)
                if not bar is None:
                    bars.append(bar)
            saveCount += bars.__len__()
            storage.save_bar_data(bars)
            batch_start = batch_end  # + timedelta(days = 1)
        context.log_i(f"_download_bars_from_jq() :driver:{self.get_name()} jq_code={jq_code} start={start_date},end={end_date},count={saveCount}")
        return saveCount

    def toBarData(self,jq_code,prices,rowIndex:int,interval)->BarData:
        open_interest = 0
        row = prices.iloc[rowIndex]
        wd = prices.index[rowIndex]
        date = datetime(year=wd.year, month=wd.month, day=wd.day, hour=wd.hour, minute=wd.minute, second=wd.second);
        volume = row['volume']
        if np.math.isnan(volume):
            ##该天没有值
            return None
        return BarData(
            symbol=jq_code,
            _driver=self.get_name(),
            datetime=date,
            interval=interval,
            volume=row['volume'],
            open_price=row['open'],
            high_price=row['high'],
            low_price=row['low'],
            close_price=row['close'],
            open_interest=open_interest,
        )


