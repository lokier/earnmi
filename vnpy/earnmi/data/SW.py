""""
申万行业数据
"""
from abc import abstractmethod
from datetime import datetime
from typing import List, Sequence

from vnpy.trader.object import BarData


class SW:

    """
    返回申万二级行业数据
    """
    def getSW2List(self)-> Sequence["str"]:
        pass

    """
    返回申万二级成分股
    """
    def getSW2Stocks(self,sw2_code:str) -> Sequence["str"]:
        pass

    """
    返回某个行业数据的日k线图
    """
    @abstractmethod
    def getSW2Daily(self, code:str, start:datetime, end:datetime) -> Sequence["BarData"]:
        pass

    @abstractmethod
    def getSw2Name(self,code:str)->str:
        pass
    """
       返回某个行业数据的分时图
    """
    @abstractmethod
    def getSW2Mintuely(self, code: str,date:datetime) -> Sequence["BarData"]:
        pass