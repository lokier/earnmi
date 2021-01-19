from peewee import SqliteDatabase

from earnmi.core.Context import Context
from earnmi.data.BarStorage import BarStorage


class BarManager:

    def __init__(self,context:Context):
        self.context = context
        storageFilePath = context.getFilePath("BarManager","bar_storage.db")
        self._storage:BarStorage = BarStorage(SqliteDatabase(storageFilePath))

    def getStorage(self)->BarStorage:
        """
        返回行情存储器
        """
        return self._storage

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






