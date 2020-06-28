from datetime import datetime
from typing import Sequence

from earnmi.data.KBarMintuePool import KBarMintuePool
from earnmi.data.KBarPool import KBarPool
from earnmi.data.Market import Market
from vnpy.trader.constant import Exchange
from vnpy.trader.object import BarData, TickData


class RealTimeImpl(Market.RealTime):
    market: Market = None

    def __init__(self, market: Market):
        self.market = market

    def getTick(self, code: str) -> TickData:
        raise RuntimeError("unimplment yet!")

    def getKBar(self, code: str, hour: int = 0, minute: int = 1, second: int= 1) -> BarData:

        today = self.market.getToday()

        if (today is None):
            raise RuntimeError("market doese not set current time")

        # buy_trade_time = datetime(2019, 2, 26, 10, 28)
        # sell_trade_time = datetime(2019, 2, 27, 1, 5)
        # if (today >= sell_trade_time):
        #     bar = BarData(
        #         symbol=code,
        #         exchange=Exchange.SSE,
        #         datetime=None,
        #         gateway_name="unkonw",
        #         open_price=67.99,
        #         high_price=68.58,
        #         low_price=68.10,
        #         close_price=68.20
        #     )
        #     return bar
        # elif (today >= buy_trade_time):
        #     bar = BarData(
        #         symbol=code,
        #         exchange=Exchange.SSE,
        #         datetime=None,
        #         gateway_name="unkonw",
        #         open_price=67.45,
        #         high_price=67.90,
        #         low_price=67.15,
        #         close_price=67.50
        #
        #     )
        #     return bar

        pool = self.getKBarMintuePool(code)
        bars  = pool.getAtDay(today)
        if len(bars) == 0:
            return None

        start = datetime(year=today.year,month=today.month,day=today.day,hour=hour,minute = minute,second = second)
        if(start > today):
            return None

        ret_bar = None
        for bar in bars:
            if bar.datetime >= start and bar.datetime <= today:
                if ret_bar is None:
                    ret_bar = BarData(
                        symbol=code,
                        exchange=bar.exchange,
                        datetime=None,
                        interval = bar.interval,
                        gateway_name=bar.gateway_name,
                        open_price=bar.open_price,
                        high_price=bar.high_price,
                        low_price=bar.low_price,
                        volume = bar.volume,
                        open_interest = bar.open_interest,
                        close_price=  bar.close_price
                    )
                    ret_bar.datetime = today
                else :
                    ret_bar.high_price = max(ret_bar.high_price, bar.high_price)
                    ret_bar.low_price = min(ret_bar.low_price, bar.low_price)
                    ret_bar.close_price = bar.close_price
                    ret_bar.volume += int(bar.volume)
                    ret_bar.open_interest = bar.open_interest

        return ret_bar



    def getTime(self) -> datetime:
        return self.market.getToday()



    def getKBarMintuePool(self,code:str)->KBarMintuePool:
        bar_poll = self.market.getNoticeData(code,"real_time_bar_poll")
        if bar_poll is None:
            bar_poll = KBarMintuePool(code)
            self.market.putNoticeData(code,"real_time_bar_poll",bar_poll)
        return bar_poll


class HistoryImpl(Market.History):
    market:Market = None

    def __init__(self, market:Market):
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




class MarketImpl(Market):

    history:HistoryImpl =None
    realtime:RealTimeImpl = None

    def __init__(self):
        self.history = HistoryImpl(self)
        self.realtime = RealTimeImpl(self)

    def getRealTime(self) -> Market.RealTime:
        return self.realtime

    def getHistory(self) -> Market.History:
        return self.history

    def nextTradeDay(self):
        raise RuntimeError("umimplement")

    def privoueTradeDay(self):
        raise RuntimeError("umimplement")


    def _checkOk(self, code: str):
        if (self._today is None):
            raise RuntimeError(f"you mut setToday() first.")
        if (not self.isNotice(code)):
            raise RuntimeError(f"you have not trace code = {code} yet.")