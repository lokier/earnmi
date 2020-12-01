import math
from datetime import datetime, timedelta
from math import nan
from typing import Tuple, Sequence

from vnpy.trader.constant import Exchange, Interval

from vnpy.trader.object import BarData

from vnpy.trader.utility import get_file_path
from peewee import (
    AutoField,
    CharField,
    Database,
    DateTimeField,
    FloatField,
    Model,
    MySQLDatabase,
    PostgresqlDatabase,
    SqliteDatabase,
    chunked,
    fn
)
from vnpy.trader.database.database_sql import init_by_sql_databease
from earnmi.uitl.utils import utils
import numpy as np


""""
不包含今天
"""
class FetcherDailyBar:


    def __init__(self, code: str,batch_size = 900,file_preffix="daily_bar_v2_"):
        self.__database_manager: "BaseDatabaseManager" = None
        self.__update_batch_size = 900
        self.__oldest_bar_datetime: datetime = None
        self.__newest_bar_datetime: datetime = None


        self.__code = code
        self.__update_batch_size = batch_size
        self.__code_jq = utils.to_jq_symbol(code)
        self.__exchange = utils.getExchange(self.__code)
        self.__initDataManager(file_preffix)

    def __initDataManager(self,file_preffix):

        database = f"{file_preffix}{self.__code_jq}.db"
        path = str(get_file_path(database))
        db = SqliteDatabase(path)
        self.__database_manager = init_by_sql_databease(db)
        self.__updateNewestTime()

    def clearAll(self):
        codeTime = f"Time_{self.__code}"
        self.__database_manager.clean(codeTime)
        self.__database_manager.clean(self.__code)
        self.__updateNewestTime()
        assert self.__newest_bar_datetime == None
        assert self.__oldest_bar_datetime == None

    """
    end不包含今天
    """
    def fetch(self, start: datetime, end: datetime) -> Sequence["BarData"]:

        database_manager = self.__database_manager

        now = datetime.now()
        yestoday = utils.to_end_date(now - timedelta(days=1))
        #end不包含今天
        if end.__gt__(yestoday):
            end = yestoday

        if self.__oldest_bar_datetime is None:
            self.__update_bar_data_from_jqdata(start, end)
        else:
            start = utils.to_start_date(start)
            end = utils.to_end_date(end)
            data_start = utils.to_start_date(self.__oldest_bar_datetime)
            data_end = utils.to_end_date(self.__newest_bar_datetime)
            now = utils.to_end_date(datetime.now())
            if end > now:
                end = now
            if start < data_start:
                update_end = data_start - timedelta(days=1)
                update_start = start
                assert update_end < now
                assert update_start <= update_end
                self.__update_bar_data_from_jqdata(update_start, update_end)
            if end >  data_end:
                update_start = data_end + timedelta(days=1)
                update_end = end
                assert update_end < now
                assert update_start <= update_end
                self.__update_bar_data_from_jqdata(update_start, update_end)

        pool_data = database_manager.load_bar_data(self.__code, self.__exchange, Interval.DAILY, start, end)
        return pool_data

    """
      从jqdata更新数据并更新数据库。
    """

    def __update_bar_data_from_jqdata(self, start_date: datetime, end_date: datetime) -> int:
        from earnmi.uitl.jqSdk import jqSdk
        jq = jqSdk.get()

        from earnmi.uitl.utils import utils

        start_date = utils.to_start_date(start_date)
        end_date = utils.to_end_date(end_date)

        print("###########[Daily] update_bar_data_from_jqdata:code =%s" % self.__code)
        # 1m : 60 * 4 = 240, 240 * 4 = 960 =>4 day
        # 1h : 1* 4 = 4, 200 * 4 = 800, => 200day
        # 1d : 900day
        # interval.__str__()
        batch_day = self.__update_batch_size
        jq_frequency = '1d'
        interval = Interval.DAILY
        batch_start = start_date
        saveCount = 0
        database_manager = self.__database_manager
        while (batch_start.__lt__(end_date)):
            batch_end = batch_start + timedelta(days=batch_day)
            batch_end = utils.to_end_date(batch_end)
            if (batch_end.__gt__(end_date)):
                batch_end = end_date

            prices = jq.get_price(self.__code_jq, start_date=batch_start, end_date=batch_end,
                                  fields=['open', 'close', 'high', 'low', 'volume'], frequency='1d')

            if (prices is None):
                break

            bars = []
            lists = np.array(prices)
            for rowIndex in range(0, lists.shape[0]):
                open_interest = 0
                row = prices.iloc[rowIndex]
                wd = prices.index[rowIndex]
                date = datetime(year=wd.year, month=wd.month, day=wd.day, hour=wd.hour, minute=wd.minute,
                                second=wd.second);
                volume = row['volume']
                if math.isnan(volume):
                    ##该天没有值
                    continue
                bar = BarData(
                    symbol=self.__code,
                    exchange=self.__exchange,
                    datetime=date,
                    interval=interval,
                    volume=row['volume'],
                    open_price=row['open'],
                    high_price=row['high'],
                    low_price=row['low'],
                    close_price=row['close'],
                    open_interest=open_interest,
                    gateway_name="DB"
                )
                bars.append(bar)
            saveCount += bars.__len__()
            print("save size:%d" % bars.__len__())
            database_manager.save_bar_data(bars)
            batch_start = batch_end  # + timedelta(days = 1)

        ##更新缓存时间段:
        codeTime = f"Time_{self.__code}"
        min_start_date = start_date
        max_end_date = end_date
        if not self.__newest_bar_datetime is None:
            min_start_date = min(self.__oldest_bar_datetime,min_start_date)
            max_end_date = max(self.__newest_bar_datetime,max_end_date)
        database_manager.clean(codeTime)
        starDateBar = BarData(symbol=codeTime, exchange=self.__exchange, datetime=min_start_date,interval=Interval.DAILY,volume=1, open_price=1,
                      high_price=1,low_price=1, close_price=1, open_interest=0,gateway_name="DB" )
        endDateBar = BarData(symbol=codeTime, exchange=self.__exchange, datetime=max_end_date, interval=Interval.DAILY,
                              volume=1, open_price=1,
                              high_price=1, low_price=1, close_price=1, open_interest=0, gateway_name="DB")
        database_manager.save_bar_data([starDateBar,endDateBar])

        self.__updateNewestTime();
        assert self.__newest_bar_datetime >= start_date
        assert self.__oldest_bar_datetime <= end_date
        return saveCount

    def __updateNewestTime(self):
        codeTime = f"Time_{self.__code}"
        __newest_bar_data = self.__database_manager.get_newest_bar_data(codeTime, self.__exchange,
                                                                             Interval.DAILY)
        __oldest_bar_data = self.__database_manager.get_oldest_bar_data(codeTime, self.__exchange,
                                                                             Interval.DAILY)
        if not __newest_bar_data is None:
            self.__newest_bar_datetime = __newest_bar_data.datetime
            self.__oldest_bar_datetime = __oldest_bar_data.datetime
        else:
            self.__newest_bar_datetime = None
            self.__oldest_bar_datetime = None


if __name__ == "__main__":
    from earnmi.chart.Chart import Chart

    code = "000050"
    #start = datetime.now() - timedelta(days=200)
    start = datetime(2015, 10, 1)
    end = datetime.now() + timedelta(days=10)

    # start_1 = datetime.now() -timedelta(days=1000)
    # end_1 = datetime.now() -timedelta(days=500)
    #
    fetcher = FetcherDailyBar(code)
    #fetcher.clearAll()
    # bars = fetcher.fetch(start_1,end_1)
    bars = fetcher.fetch(start,end)
    chart = Chart()
    #chart.show(bars)
    print(f"len:{len(bars)},end = {bars[-1].datetime}")




