
"""
行情数据驱动器。
"""
from abc import abstractmethod
from datetime import datetime

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

    @abstractmethod
    def nextBars(self) -> Tuple[Sequence['BarData'], str]:
        pass

    @abstractmethod
    def reset(self):
        pass

class DefaultBarSource(BarSource):

    def __init__(self,context:Context,storage:BarStorage,drivers:[],interval:Interval,start:datetime,end:datetime):
       """
       参数：
            context:
            storage:
            indexDriver: 指数行情驱动器，比如:A股的指数是上证指数。
            drivers:  各种股票池行情驱动器。
       """
       self.context = context
       self._storage = storage
       self._inteval = interval
       self._start = start
       self._end = end
       self._drviers:[] = drivers
       self._driver_index = 0
       self._current_symbol_list_index = 0
       self._current_symol_list:[] = None
       assert len(drivers) > 0

    def nextBars(self) -> Tuple[Sequence['BarData'], str]:
        if self._driver_index >= len(self._drviers):
            return None,None
        driver: BarDriver = self._drviers[self._driver_index]
        if self._current_symol_list is None:
            assert self._current_symbol_list_index == 0
            self._current_symol_list = list(driver.get_symbol_lists())
        if self._current_symbol_list_index < len(self._current_symol_list):
            symbol = self._current_symol_list[self._current_symbol_list_index]
            self._current_symbol_list_index += 1
            bars = driver.load_bars(symbol,self._inteval,self._start,self._end,self._storage)
            return bars, symbol
        else:
            self._current_symol_list = None
            self._current_symbol_list_index = 0
            self._driver_index +=1
            return self.nextBars()

    def reset(self):
        self._driver_index = 0
        self._current_symbol_list_index = 0
        self._current_symol_list = None





