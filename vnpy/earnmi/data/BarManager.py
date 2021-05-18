from datetime import datetime

from peewee import SqliteDatabase

from vnpy.trader.constant import Interval
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

    """
    创建数据加工数据。
    """
    def transfrom(self,transform,rebuild = False)->BarDriver:
        transformBarDriver = BarManager._TransformBarDriver(transform)

        storage = self.getStorageGroup().getStorageV2() if transformBarDriver.isBarV2() else self.getStorageGroup().getStorage()
        driver_name = transformBarDriver.get_name()
        if rebuild:
            storage.clean(driver=driver_name)
        transform.onTransform(self,storage,driver_name)
        return transformBarDriver


    def createUpdator(self)->BarUpdator:
        updator = BarUpdator(self.context, self.getStorageGroup());
        return updator

    class _TransformBarDriver(BarDriver):

        def __init__(self,tranfrom):
            self.transform = tranfrom
            self.origin_driver = tranfrom.driver
            self.name = f"__t__{tranfrom.driver.get_name()}"

        def getDriverGroupName(self):
            return V2_DRIVER_NAME

        def get_name(self):
            return self.name

        def get_symbol_lists(self):
            return self.origin_driver.get_symbol_lists();

        def get_symbol_name(self, symbol: str):
            return self.origin_driver.get_symbol_name()







