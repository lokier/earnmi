from datetime import datetime

from peewee import SqliteDatabase

from earnmi.data.BarParallel import DefaultBarParallel
from vnpy.trader.constant import Interval
from earnmi.core.Context import Context, ContextWrapper
from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarMarket import BarMarket
from earnmi.data.BarSoruce import BarSource, DefaultBarSource, BarSource
from earnmi.data.BarStorage import BarStorage
from earnmi.data.BarUpdator import BarUpdator

__all__ = [
    # Super-special typing primitives.
    'BarManager',
]

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

    def createBarSoruce(self, driver:BarDriver, start: datetime = None, end: datetime = None) -> BarSource:
        return BarSource(driver, self._storage, start, end)

    """
    创建数据加工数据。
    """
    def transfrom(self,transform,rebuild = False)->BarDriver:
        transformBarDriver = BarManager._TransformBarDriver(transform)

        driver_name = transformBarDriver.get_name()
        if rebuild:
            self._storage.clean(driver=driver_name)
        transform.onTransform(self._storage,driver_name)
        return transformBarDriver

    # def createBarParallel(self, drvier:BarDriver, start: datetime, end: datetime):
    #     source = DefaultBarParallel( self._storage,drvier,start,end)
    #     return source

    def createUpdator(self)->BarUpdator:
        updator = BarUpdator(self.context,self._storage);
        return updator

    class _TransformBarDriver(BarDriver):

        def __init__(self,tranfrom):
            self.transform = tranfrom
            self.origin_driver = tranfrom.driver
            self.name = f"__t__{tranfrom.driver.get_name()}"

        def get_name(self):
            return self.name

        def get_symbol_lists(self):
            return self.origin_driver.get_symbol_lists();

        def get_symbol_name(self, symbol: str):
            return self.origin_driver.get_symbol_name()







