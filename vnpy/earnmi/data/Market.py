from abc import abstractmethod
from datetime import datetime
from typing import Sequence, Any

from vnpy.trader.object import TickData,BarData


class Market:
    """
        实时相关的数据
    """

    class RealTime:
        """
            返回当前Tick数据。
        """
        @abstractmethod
        def getTick(self, code: str) -> BarData:
            pass

        """
        返回 今天[hour,mintue,second]到现在的k线图。（24小时）
        """

        @abstractmethod
        def getKBar(self, code: str, hour: int = 0, minute: int= 0, second: int = 30) -> BarData:
            pass

        @abstractmethod
        def getTime(self) -> datetime:
            pass

    """
     历史相关的数据
     """

    class History:
        """
        返回到今天的k线图。（不包含今天）
        """
        @abstractmethod
        def getKbars(self, code: str, count: int)-> Sequence["BarData"]:
            pass

        @abstractmethod
        def clean(self,code):
            pass
        """
         返回到今天的k线图。（不包含今天）
        """
        @abstractmethod
        def getKbarFrom(self, code: str, start: datetime)-> Sequence["BarData"]:
            pass

    __notice_data_map = {}
    __today:datetime = None

    """
    返回实时数据。
    """
    @abstractmethod
    def getRealTime(self)->RealTime:
        pass

    """
       返回历史数据。
    """
    @abstractmethod
    def getHistory(self) -> History:
        pass

    """
    状态跳转到下个交易日
    """
    @abstractmethod
    def nextTradeDay(self):
        pass

    """
       状态跳转到上个交易日
    """
    @abstractmethod
    def privoueTradeDay(self):
        pass

    """
    返回当前时间。
    """
    def getToday(self) -> datetime:
        return self.__today

    def setToday(self,today:datetime):
        self.__today = today


    def addNotice(self,code:str):
        if(not self.isNotice(code)):
            self.__notice_data_map[code] = {}


    def removeNotice(self,code:str):
        if (self.isNotice(code)):
            self.__notice_data_map.__delitem__(code)

    def isNotice(self,code:str)->bool:
        return self.__notice_data_map.__contains__(code)

    def getNoticeData(self, code: str, key: str) -> Any:
        if(not self.isNotice(code)):
            raise RuntimeError(f"{code} is not in notice map")
        notice_data = self.__notice_data_map[code]
        return notice_data.get(key)

    def putNoticeData(self, code: str, key: str, value:Any):
        if (not self.isNotice(code)):
            raise RuntimeError(f"{code} is not in notice map")
        self.__notice_data_map[code][key] = value













