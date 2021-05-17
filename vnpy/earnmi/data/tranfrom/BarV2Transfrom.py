from datetime import datetime

from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarManager import BarManager
from earnmi.data.BarStorage import BarStorage
from earnmi.data.BarTransform import BarTransfrom

"""
BarV2变换器
"""
class BarV2Transform(BarTransfrom):


    def onTransform(self,manager:BarManager,storage: BarStorage,driver_name:str):

        targetDriver = self.driver

        market = manager.createBarMarket()