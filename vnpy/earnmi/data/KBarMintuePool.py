from typing import Sequence, Tuple
from datetime import datetime, timedelta

from vnpy.trader.object import BarData

from vnpy.trader.constant import Exchange, Interval
from earnmi.data.import_data_from_jqdata import save_bar_data_from_jqdata
from vnpy.trader.database import database_manager




"""
  每分钟数据线。
"""
class KBarMintuePool:

    __pool_day:datetime = None
    __pool_day_data:Sequence["BarData"] = None
    __pool_start:datetime = None
    __pool_end:datetime = None


    def __init__(self, code: str):
        self.code = code
        self.exchange = Exchange.SZSE
        if self.code.startswith("6"):
            self.exchange = Exchange.SSE
        database_manager.delete_bar_data(self.code,self.exchange,Interval.MINUTE)

    """
    返回一整天的数据。
    """
    def getAtDay(self,day:datetime)-> Sequence["BarData"]:

        if self.__pool_day:
            if self.__is_same_day(day,self.__pool_day):
                return self.__pool_day_data
            ###从数据库里面获取
            if(self.__pool_start<= day and day <= self.__pool_end):
                start = self._buidl_start_date(day)
                end = self._buidl_end_date(day)

                self.__pool_day_data = database_manager.load_bar_data(self.code, self.exchange, Interval.MINUTE, start, end)
                self.__pool_day = day
                return self.__pool_day_data

        ###从网络创建缓存
        self.__pool_start,self.__pool_end = self.__makePollSize(day)
        if (self.__pool_start <= day and day <= self.__pool_end):
            start = self._buidl_start_date(day)
            end = self._buidl_end_date(day)

            self.__pool_day_data = database_manager.load_bar_data(self.code, self.exchange, Interval.MINUTE, start, end)
            self.__pool_day = day
            return self.__pool_day_data
        raise RuntimeError("shuld not run here .(__makePollSize error)")



    def __makePollSize(self,start:datetime) ->Tuple[datetime, datetime]:
        end = start + timedelta(days=3)
        print(f"__makePollSize:{start}, {end}")
        start = self._buidl_start_date(start)
        end = self._buidl_end_date(end)

        database_manager.delete_bar_data(self.code,self.exchange,Interval.MINUTE)
        save_bar_data_from_jqdata(self.code, Interval.MINUTE, start_date=start, end_date=end)
        return start,end

    def __is_same_day(self,d1:datetime,d2:datetime)->bool:
        return d1.day == d2.day and d1.month == d2.month and d1.year == d2.year

    def _buidl_start_date(self, d: datetime) -> datetime:
        return datetime(year=d.year, month=d.month, day=d.day, hour=00, minute=00, second=1)

    def _buidl_end_date(self, d: datetime) -> datetime:
        return datetime(year=d.year, month=d.month, day=d.day, hour=23, minute=59, second=59)

if __name__ == "__main__":
    code = "300004"

    has_data_day1 = datetime(year=2020,month=5,day=8)
    no_data_day = datetime(year=2020,month=5,day=9)
    has_data_day2 = datetime(year=2020,month=5,day=11)

    bar_pool = KBarMintuePool(code)

    datas1 = bar_pool.getAtDay(has_data_day1)
    datas2 = bar_pool.getAtDay(no_data_day)
    datas3 = bar_pool.getAtDay(has_data_day2)
    datas4 = bar_pool.getAtDay(has_data_day1)

    assert len(datas1) >= 200
    assert len(datas2) == 0
    assert len(datas3) >= 200

    pre_min_bar =None
    for min_bar in datas1:
        if pre_min_bar:
            d1 = pre_min_bar.datetime
            d2 =min_bar.datetime
            assert d1.day == d2.day and d1.month == d2.month and d1.year == d2.year
            assert min_bar.interval == Interval.MINUTE
            assert pre_min_bar.datetime < min_bar.datetime
        pre_min_bar = min_bar


    for i in range(len(datas1)):
        assert datas1[i].datetime == datas4[i].datetime




