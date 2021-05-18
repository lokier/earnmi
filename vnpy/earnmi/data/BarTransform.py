"""

bar加工变换对象。
"""
from abc import abstractmethod

from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarManager import BarManager
from earnmi.data.BarStorage import  BarV2Storage


class BarTransfrom:


    def __init__(self,driver:BarDriver):
        self.driver = driver

    """
        storge:bar存储库
        driver_name：该transfrom对应的driver_name
    """
    @abstractmethod
    def onTransform(self,manager:BarManager,storage: BarV2Storage,driver_name:str):

        ####开始加工数据
        ###storage.save_bar_data()

        pass
