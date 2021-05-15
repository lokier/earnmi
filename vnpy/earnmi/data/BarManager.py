from datetime import datetime

from numba import deprecated
from peewee import SqliteDatabase

from earnmi.data.BarParallel import DefaultBarParallel
from vnpy.trader.constant import Interval

from earnmi.core.Context import Context, ContextWrapper
from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarMarket import BarMarket
from earnmi.data.BarSoruce import BarSource, DefaultBarSource
from earnmi.data.BarStorage import BarStorage
from earnmi.data.BarUpdator import BarUpdator


class BarManager:

    @staticmethod
    def get(context:Context):
        if isinstance(context, ContextWrapper):
            return context._context.bar_manager
        return context.bar_manager

    def __init__(self,context:Context):
        self.context = context
        storageFilePath = context.getFilePath("BarManager","bar_storage.db")
        self._storage:BarStorage = BarStorage(SqliteDatabase(storageFilePath))


    def getStorage(self)->BarStorage:
        """
        返回行情存储器
        """
        return self._storage

    def createBarMarket(self, index_driver:BarDriver, drivers:['BarDriver'])->BarMarket:
        """
        创建行情市场对象
        参数:
            index_driver： 行情指数驱动器
            drivers: 各种股票池行情数据驱动器
        """
        market = BarMarket(self.context, self._storage)
        market.init(index_driver, drivers)
        return market

    @deprecated(version='1.0', reason="This function will be removed soon")
    def createBarSoruce(self, drivers: ['BarDriver'], interval: Interval, start: datetime, end: datetime) -> BarSource:
        """
        创建行情市场对象
        参数:
            drivers: 各种股票池行情数据驱动器
        """
        source = DefaultBarSource(self.context, self._storage,drivers,interval,start,end)
        return source

    def createBarParallel(self, drvier:BarDriver, start: datetime, end: datetime):
        source = DefaultBarParallel(self.context, self._storage,drvier,start,end)
        return source

    def createUpdator(self)->BarUpdator:
        updator = BarUpdator(self.context,self._storage);
        return updator

    """
     行情管理器
     """

    # def registerDriver(self, driver: BarDriver):
    #     pass
    #
    # def unregisterDriver(self, driver: BarDriver):
    #     pass
    #
    # def getDrivers(self):
    #     pass







