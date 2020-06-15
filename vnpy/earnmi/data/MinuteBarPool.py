from typing import Sequence
from datetime import datetime, timedelta

from vnpy.trader.object import BarData

from vnpy.trader.constant import Exchange, Interval
from earnmi.data.import_data_from_jqdata import save_bar_data_from_jqdata
from vnpy.trader.database import database_manager




"""
  每分钟数据线。
"""
class MinuteBarPool:

    _today:datetime

    def __init__(self, code: str):
        self.code = code

    def setToday(self,today:datetime):
        self._today = today
        start = datetime(year=today.year,month=today.month,day=today.day,hour=1,minute=0)
        end = datetime(year=today.year,month=today.month,day=today.day,hour=23,minute=0)
        save_bar_data_from_jqdata(self.code, Interval.MINUTE, start_date=start, end_date=end)

    def getData(self)-> Sequence["BarData"]:
        exchange = Exchange.SZSE
        today = self._today
        start = datetime(year=today.year, month=today.month, day=today.day, hour=1, minute=0)
        end = datetime(year=today.year, month=today.month, day=today.day, hour=23, minute=0)
        if self.code.startswith("6"):
            exchange = Exchange.SSE

        return database_manager.load_bar_data(self.code, exchange, Interval.MINUTE, start, end)





