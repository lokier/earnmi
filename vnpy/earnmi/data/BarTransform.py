"""

bar加工变换对象。
"""
from abc import abstractmethod
from datetime import datetime
from typing import Sequence

from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarSoruce import BarSource
from earnmi.data.BarStorage import  BarV2Storage
from earnmi.model.bar import BarV2, BarData

class BarTransformStorage:
    """
    变换后的bar存储器。
    """
    def __init__(self,manager,stoarge:BarV2Storage,transform_dervier:BarDriver):
        self._storage = stoarge
        self._transform_driver = transform_dervier
        self._manager = manager

    def getBarDriver(self)->BarDriver:
        return self._transform_driver

    def createBarV2(self,bar:BarData)->BarV2:
        return BarV2.copy(bar,self.getBarDriver().get_name())

    def save_bar_data(self, datas: Sequence[BarV2]):
        self._storage.save_bar_data(datas)

    def clear(self):
        self._storage.clean(driver=self.getBarDriver().get_name())

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
        transform_driver：该transfrom对应的BarDrvier
    """
    @abstractmethod
    def onTransform(self,manager,storage:BarTransformStorage):
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

