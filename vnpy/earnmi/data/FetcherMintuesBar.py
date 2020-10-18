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


class FetcherMintuesBar:

    def __init__(self, code: str,batch_size = 900):
        self.__database_manager: "BaseDatabaseManager" = None
        self.__code = code
        self.__update_batch_size = batch_size
        self.__code_jq = utils.to_jq_symbol(code)
        self.__exchange = utils.getExchange(self.__code)
        self.__initDataManager()

    def __initDataManager(self):

        database = f"minute_bar_{self.__code}_{self.__exchange.value.__str__()}.db"
        path = str(get_file_path(database))
        db = SqliteDatabase(path)
        self.__database_manager = init_by_sql_databease(db)

    def clearAll(self):
        self.__database_manager.clean(self.__code)

    def fetch(self, day:datetime) -> Sequence["BarData"]:

        database_manager = self.__database_manager

        if not self.hasBar(day):
            self.__update_bar_data_from_jqdata(day)
        start_date = utils.to_start_date(day)
        end_date = utils.to_end_date(day)
        pool_data = database_manager.load_bar_data(self.__code, self.__exchange, Interval.MINUTE, start_date, end_date)
        return pool_data

    """
      从jqdata更新数据并更新数据库。
    """

    def __update_bar_data_from_jqdata(self, day: datetime):
        from earnmi.uitl.jqSdk import jqSdk
        jq = jqSdk.get()

        from earnmi.uitl.utils import utils

        start_date = utils.to_start_date(day)
        end_date = utils.to_end_date(day)

        print("###########[Minute] update_bar_data_from_jqdata:code =%s" % self.__code)
        # 1m : 60 * 4 = 240, 240 * 4 = 960 =>4 day
        # 1h : 1* 4 = 4, 200 * 4 = 800, => 200day
        # 1d : 900day
        # interval.__str__()
        batch_day = self.__update_batch_size
        jq_frequency = '1d'
        interval = Interval.MINUTE
        database_manager = self.__database_manager

        prices = jq.get_price(self.__code_jq, start_date=start_date, end_date=end_date, fields=['open', 'close', 'high', 'low', 'volume'], frequency='1m')


        if not prices is None:
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
            print("save size:%d" % bars.__len__())
            database_manager.save_bar_data(bars)

        now = utils.to_start_date(datetime.now());
        save_has_check = day < now

        if save_has_check:
            has_check_bar = BarData(
                    symbol="day_code",
                    exchange=self.__exchange,
                    datetime=day,
                    interval=Interval.DAILY,
                    volume=0.0,
                    open_price=0.0,
                    high_price=0.0,
                    low_price=0.0,
                    close_price=0.0,
                    open_interest=0.0,
                    gateway_name="DB"
                )
            database_manager.save_bar_data([has_check_bar])

    def hasBar(self,day:datetime) ->bool:
        start_date = utils.to_start_date(day)
        end_date = utils.to_end_date(day)
        pool_data = self.__database_manager.load_bar_data("day_code", self.__exchange, Interval.DAILY, start_date, end_date)
        if pool_data is None:
            return False
        return len(pool_data) > 0

if __name__ == "__main__":
    code = "300004"
    start = datetime.now() - timedelta(days=1)
    end = datetime.now()

    fetcher = FetcherMintuesBar(code)
    #fetcher.clearAll()
    bars = fetcher.fetch(start)
    print(f"len:{len(bars)}")




