from datetime import datetime
from typing import Sequence
from earnmi.data.HistoryBarPool import HistoryBarPool
from earnmi.data.KBarPool import KBarPool
from earnmi.data.Market2 import Market2
from vnpy.trader.object import BarData, TickData


class HistoryImpl(Market2.History):
    market:Market2 = None

    def __init__(self, market:Market2):
        self.market = market

    def getKbars(self, code: str, count: int) -> Sequence["BarData"]:
        if(count >= 1000):
            raise RuntimeError(f"count must < 1000")
        today = self.market.getToday()
        if(today is None):
            raise RuntimeError("market doese not set current time")
        bar_pool = self.getKBarPool(code)
        return bar_pool.getData(today,count)

    def getKbarFrom(self, code: str, start: datetime) -> Sequence["BarData"]:
        today = self.market.getToday()
        if (today is None):
            raise RuntimeError("market doese not set current time")
        if(start >= today):
            raise RuntimeError("start time must be < today")

        bar_pool = self.getKBarPool(code)
        return bar_pool.getDataFrom(start,today)

    def getKBarPool(self,code:str)->KBarPool:
        bar_poll = self.market.getNoticeData(code,"history_bar_poll")
        if bar_poll is None:
            bar_poll = KBarPool(code)
            self.market.putNoticeData(code,"history_bar_poll",bar_poll)
        return bar_poll




class MarketImpl(Market2):
    class RealtimeImpl(Market2.RealTime):
        def getTick(self, code: str) -> TickData:
            pass

        def getKBar(self, code: str) -> BarData:
            pass

        def getTime(self) -> datetime:
            pass


    history:HistoryImpl =None

    def __init__(self):
        self.history = HistoryImpl(self)

    def getRealTime(self) -> Market2.RealTime:
        pass

    def getHistory(self) -> Market2.History:
        return self.history

    def nextTradeDay(self):
        pass

    def privoueTradeDay(self):
        pass

    def getCurrentTradeDay(self) -> datetime:
        pass



    def _checkOk(self, code: str):
        if (self._today is None):
            raise RuntimeError(f"you mut setToday() first.")
        if (not self.isNotice(code)):
            raise RuntimeError(f"you have not trace code = {code} yet.")