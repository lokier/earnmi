"""

bar加工变换对象。
"""
from abc import abstractmethod
from datetime import datetime

from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarSoruce import BarSource
from earnmi.data.BarStorage import  BarV2Storage



class BarTransformHandle:

    @abstractmethod
    def get_name(self):
        raise RuntimeError("未实现")

    def get_symbol_lists(self):
        """
        该转化器变化处理的股票池。
        """
        raise RuntimeError("未实现")

    """
        storge:bar存储库
        driver_name：该transfrom对应的driver_name
    """
    @abstractmethod
    def onTransform(self,manager,storage: BarV2Storage,driver_name:str):
        raise RuntimeError("未实现")


class BarTransform:

    @abstractmethod
    def transform(self,rebuild = True):
        pass

    @abstractmethod
    def getBarDriver(self)->BarDriver:
        pass

    @abstractmethod
    def createBarSource(self, start: datetime = None, end: datetime = None) -> BarSource:
        pass