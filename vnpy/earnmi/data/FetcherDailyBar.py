from datetime import datetime, timedelta
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


class FetcherDailyBar:

    __code :str = None
    __code_jq :str = None
    __exchange:Exchange = None
    __database_manager: "BaseDatabaseManager" = None
    __update_batch_size = 900
    __newest_bar_data:"BarData" = None
    __oldest_bar_data:"BarData" = None


    def __init__(self, code: str,batch_size = 900):
        self.__code = code
        self.__update_batch_size = batch_size
        self.__code_jq = utils.to_jq_symbol(code)
        self.__exchange = utils.getExchange(self.__code)
        self.__initDataManager()

    def __initDataManager(self):

        database = f"daily_bar_{self.__code}_{self.__exchange.value.__str__()}.db"
        path = str(get_file_path(database))
        db = SqliteDatabase(path)
        self.__database_manager = init_by_sql_databease(db)
        self.__updateBar()

    def clearAll(self):
        self.__database_manager.clean(self.__code)
        self.__updateBar()

    def fetch(self, start: datetime, end: datetime) -> Sequence["BarData"]:

        database_manager = self.__database_manager

        if self.__oldest_bar_data is None:
            self.__update_bar_data_from_jqdata(start, end)
        else:
            start = utils.to_start_date(start)
            end = utils.to_end_date(end)
            data_start = utils.to_start_date(self.__oldest_bar_data.datetime)
            data_end = utils.to_end_date(self.__newest_bar_data.datetime)
            now = utils.to_end_date(datetime.now())
            if end > now:
                end = now
            if start < data_start:
                update_end = data_start - timedelta(days=1)
                deltaDay = (update_end - start).days
                if deltaDay < self.__update_batch_size:
                    deltaDay = self.__update_batch_size
                update_start = update_end - timedelta(days=deltaDay)
                if update_end > now:
                    update_end = now
                assert update_start <= update_end
                self.__update_bar_data_from_jqdata(update_start, update_end)
            if end >  data_end:
                update_start = data_end + timedelta(days=1)
                deltaDay = (end - update_start).days
                if deltaDay < self.__update_batch_size:
                    deltaDay = self.__update_batch_size
                update_end = update_start + timedelta(days=deltaDay)
                if update_end > now:
                    update_end = now
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

        print("########### update_bar_data_from_jqdata:code =%s" % self.__code)
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

        self.__updateBar();
        assert self.__newest_bar_data.datetime >= start_date
        assert self.__oldest_bar_data.datetime <= end_date
        return saveCount

    def __updateBar(self):
        self.__newest_bar_data = self.__database_manager.get_newest_bar_data(self.__code, self.__exchange,
                                                                             Interval.DAILY)
        self.__oldest_bar_data = self.__database_manager.get_oldest_bar_data(self.__code, self.__exchange,
                                                                             Interval.DAILY)


if __name__ == "__main__":
    code = "300004"
    start = datetime.now() - timedelta(days=330)
    end = datetime.now()

    fetcher = FetcherDailyBar(code)
    #fetcher.clearAll()
    bars = fetcher.fetch(start,end)
    print(f"len:{len(bars)}")




