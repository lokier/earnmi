from datetime import datetime, timedelta

from peewee import SqliteDatabase

from earnmi.data.BarTransform import BarTransform, BarTransformHandle
from earnmi.core.Context import Context, ContextWrapper
from earnmi.data.BarDriver import BarDriver, BarStorageGroup
from earnmi.data.BarMarket import BarMarket
from earnmi.data.BarSoruce import BarSource, DefaultBarSource, BarSource
from earnmi.data.BarStorage import BarStorage, BarV2Storage
from earnmi.data.BarUpdator import BarUpdator

__all__ = [
    # Super-special typing primitives.
    'BarManager',
]

V2_DRIVER_NAME = "_bar_v2_"

class _BarStorageGroup(BarStorageGroup):

    def __init__(self,v1:BarStorage,v2:BarV2Storage):
        self.v1 = v1;
        self.v2 = v2

    def getStorage(self, driver: BarDriver) -> BarStorage:
        if V2_DRIVER_NAME == driver.getDriverGroupName():
            return self.v2
        else:
            return self.v1


class BarManager:

    @staticmethod
    def get(context:Context):
        if isinstance(context, ContextWrapper):
            return context._context.bar_manager
        return context.bar_manager

    def __init__(self,context:Context):
        self.context = context
        storageFilePath = context.getFilePath("BarManager","bar_storage.db")
        storageV2FilePath = context.getFilePath("BarManager","bar_v2_storage.db")
        self._storageGroup = _BarStorageGroup(BarStorage(SqliteDatabase(storageFilePath))
                                                ,BarV2Storage(SqliteDatabase(storageV2FilePath)))

    def getStorageGroup(self)->BarStorageGroup:
        """
        返回行情存储器分组。
        不同的driver会存储到不同的平台。
        """
        return self._storageGroup

    def createBarMarket(self, index_driver:BarDriver, drivers:['BarDriver'])->BarMarket:
        """
        创建行情市场对象
        参数:
            index_driver： 行情指数驱动器
            drivers: 各种股票池行情数据驱动器
        """
        market = BarMarket(self.context, self.getStorageGroup())
        market.init(index_driver, drivers)
        return market

    def createBarSoruce(self, driver:BarDriver, start: datetime = None, end: datetime = None) -> BarSource:
        storage = self.getStorageGroup().getStorage(driver)
        return BarSource(driver, storage, start, end)

    def createBarTransform(self,hander:BarTransformHandle)->BarTransform:
        return BarManager.__Iner_BarTransform(hander,self)


    def createUpdator(self)->BarUpdator:
        updator = BarUpdator(self.context, self.getStorageGroup());
        return updator

    class _BarTransformHandleDriver(BarDriver):

        def __init__(self,handle):
            self.handle = handle

        def getDriverGroupName(self):
            return V2_DRIVER_NAME

        def get_name(self):
            return self.handle.get_name()

        def get_symbol_lists(self):
            return self.handle.get_symbol_lists();


    class __Iner_BarTransform(BarTransform):

        def __init__(self,handle:BarTransformHandle,manager):
            self.manager:BarManager = manager
            self.handle = handle
            self.driver:BarManager._BarTransformHandleDriver = BarManager._BarTransformHandleDriver(self.handle)

        """
           创建数据加工数据。
           """

        def transfrom(self,rebuild=False) -> BarDriver:
            transformBarDriver = self.driver
            storage:BarV2Storage = self.manager.getStorageGroup().getStorage(transformBarDriver)
            driver_name = transformBarDriver.get_name()
            if rebuild:
                storage.clean(driver=driver_name)
            self.handle.onTransform(self.manager, storage, driver_name)
            return transformBarDriver

        def getBarDriver(self):
            return self.driver



        def createBarSource(self, start: datetime = None, end: datetime = None) -> BarSource:
            return self.manager.createBarSoruce(self.getBarDriver(),start,end)





