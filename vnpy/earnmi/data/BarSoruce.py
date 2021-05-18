
"""
行情数据驱动器。
"""
from abc import abstractmethod
from datetime import datetime, timedelta
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval

from earnmi.core.Context import Context
from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarStorage import BarStorage
from earnmi.model.bar import LatestBar, BarData
from typing import Tuple, Sequence
__all__ = [
    # Super-special typing primitives.
    'BarSource',
    'DefaultBarSource',
]

class BarSource:

    def __init__(self,driver:BarDriver,storage:BarStorage,start: datetime = None, end: datetime = None):
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(days=730)
        assert start <= end
        self._driver = driver
        self._storage = storage
        self.start = start
        self.end = end

    def get_bars(self, symbol: str,interval:Interval = Interval.DAILY, start: datetime = None,end:datetime = None) -> Sequence["BarData"]:
        """
        返回股票的历史行情。
        """
        if start is None:
            start = self.start
        if end is None:
            end = self.end
        return self._driver.load_bars(symbol,interval,start,end,self._storage)

    """
    串行返回bar行情 。默认返回近两年数据。
    """
    @abstractmethod
    def itemsSequence(self,interval:Interval = Interval.DAILY):

        source = DefaultBarSource(self._storage, [self._driver], interval, self.start, self.end)
        return source.items()

    """
    并行返回bar行情。默认返回近两年数据。
    """
    def itemsParallel(self):
        # if not Interval.DAILY == self._interval:
        #     raise RuntimeError("itemsParallel unsupoort intrvale: " + self._interval.__str__())
        source = DefaultBarParallel(self._storage, self._driver, self.start, self.end)
        return source.items()

class Bar_iter:

    def __init__(self, dataSource):
        self.dataSource = dataSource

    def __iter__(self):
        return self

    def __next__(self):
        value = self.dataSource.nextBars()
        if value[0] is None:
            raise StopIteration
        return value

class DefaultBarSource(BarSource):

    def __init__(self,storage:BarStorage,drivers:[],interval:Interval,start:datetime,end:datetime):
       """
       参数：
            context:
            storage:
            indexDriver: 指数行情驱动器，比如:A股的指数是上证指数。
            drivers:  各种股票池行情驱动器。
       """
       self._storage = storage
       self._inteval = interval
       self._start = start
       self._end = end
       self._drviers:[] = drivers
       self._driver_index = 0
       self._current_symbol_list_index = 0
       self._current_symol_list:[] = None
       assert len(drivers) > 0

    def items(self) -> Tuple[str,Sequence['BarData']]:
        return Bar_iter(self)

    def nextBars(self) -> Tuple[Sequence['BarData'], str]:
        if self._driver_index >= len(self._drviers):
            return [None,None]
        driver: BarDriver = self._drviers[self._driver_index]
        if self._current_symol_list is None:
            assert self._current_symbol_list_index == 0
            self._current_symol_list = list(driver.get_symbol_lists())
        if self._current_symbol_list_index < len(self._current_symol_list):
            symbol = self._current_symol_list[self._current_symbol_list_index]
            self._current_symbol_list_index += 1
            bars = driver.load_bars(symbol,self._inteval,self._start,self._end,self._storage)
            return [ symbol,bars]
        else:
            self._current_symol_list = None
            self._current_symbol_list_index = 0
            self._driver_index +=1
            return self.nextBars()

    def reset(self):
        self._driver_index = 0
        self._current_symbol_list_index = 0
        self._current_symol_list = None


class BarParallel:

    @abstractmethod
    def items(self) -> Tuple[datetime,Sequence['BarData']]:
        pass


class Dayly_iter:

    def __init__(self, dataSource):
        self.dataSource = dataSource
    def __iter__(self):
        return self

    def __next__(self):
        value = self.dataSource.nextBars()
        if value is None:
            raise StopIteration
        return value

class DefaultBarParallel(BarParallel):

    def __init__(self,storage:BarStorage,driver:BarDriver,start:datetime,end:datetime):
       """
       参数：
            context:
            storage:
            indexDriver: 指数行情驱动器，比如:A股的指数是上证指数。
            drivers:  各种股票池行情驱动器。
       """
       self.storage = storage
       self.start = start
       self.end = end
       self.driver:BarDriver = driver
       self.__current_day = start
       self.__current_bar_index = 0
       self.__current_bar_cache_list = []

    def items(self) -> Tuple[Sequence['BarData'], str]:
        return Dayly_iter(self)

    def nextBars(self) -> Tuple[datetime,Sequence['BarData']]:

        ###使用缓存下的。
        if self.__current_bar_index < len(self.__current_bar_cache_list):
            _cur_index  = self.__current_bar_index
            self.__current_bar_index +=1
            return self.__current_bar_cache_list[_cur_index]
        ##更新缓存
        cache_list = self._nextBarsCache()
        if len(cache_list) < 1:
            return None
        self.__current_bar_index = 0
        self.__current_bar_cache_list = cache_list
        return self.nextBars()

    def _nextBarsCache(self)->[]:

        if self.__current_day >= self.end:
            ##遍历完成。
            return []

        query_start = self.__current_day
        self.__current_day = query_start + timedelta(days=8)
        query_end = utils.to_end_date(query_start + timedelta(days=7))
        if query_end > self.end:
            query_end = self.end

        bars = self.driver.load_bars(None,Interval.DAILY, query_start, query_end, self.storage)

        if bars is None or len(bars) < 1:
            return self._nextBarsCache();

        ###整理成[day,bars的方式]
        day_bars_cache_list = []
        _cur_bar_day = bars[0].datetime - timedelta(days=1)
        _cur_bar_list = None
        for bar in bars:
            _day = bar.datetime
            is_new_day =  not utils.is_same_day(_day,_cur_bar_day)
            if is_new_day:
                _cur_bar_list = []
                _cur_bar_day = _day
                day_bars_cache_list.append([_cur_bar_day,_cur_bar_list])
            _cur_bar_list.append(bar)
        return day_bars_cache_list


