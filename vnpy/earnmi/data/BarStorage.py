import datetime
from typing import List, Sequence, Optional, Dict

from peewee import AutoField, CharField, DateTimeField, FloatField, Model, Database, chunked

from earnmi.model.bar import BarData
from vnpy.trader.constant import Interval, Exchange


def _init_Bar_Model(db: Database):


    class DbBarData(Model):
        """
        Candlestick bar data for database storage.

        Index is defined unique with datetime, interval, symbol
        """

        id = AutoField()
        symbol: str = CharField()
        driver: str = CharField()
        datetime: datetime = DateTimeField()
        interval: str = CharField()

        volume: float = FloatField()
        open_interest: float = FloatField()
        open_price: float = FloatField()
        high_price: float = FloatField()
        low_price: float = FloatField()
        close_price: float = FloatField()

        class Meta:
            database = db
            indexes = ((("symbol", "driver", "interval", "datetime"), True),)

        def to_dict(self):
            return self.__data__

        @staticmethod
        def from_bar(bar: BarData):
            """
            Generate DbBarData object from BarData.
            """
            db_bar = DbBarData()

            db_bar.symbol = bar.symbol
            db_bar.driver = bar._driver
            db_bar.datetime = bar.datetime
            db_bar.interval = bar.interval.value
            db_bar.volume = bar.volume
            db_bar.open_interest = bar.open_interest
            db_bar.open_price = bar.open_price
            db_bar.high_price = bar.high_price
            db_bar.low_price = bar.low_price
            db_bar.close_price = bar.close_price

            return db_bar

        def to_bar(self):
            """
            Generate BarData object from DbBarData.
            """
            bar = BarData(
                symbol=self.symbol,
                datetime=self.datetime,
                interval=Interval(self.interval),
                volume=self.volume,
                open_price=self.open_price,
                high_price=self.high_price,
                open_interest=self.open_interest,
                low_price=self.low_price,
                close_price=self.close_price,
                _driver=self.driver
            )
            return bar

        @staticmethod
        def save_all(objs: List["DbBarData"]):
            """
            save a list of objects, update if exists.
            """
            dicts = [i.to_dict() for i in objs]
            with db.atomic():
                for c in chunked(dicts, 50):
                        DbBarData.insert_many(
                            c).on_conflict_replace().execute()

    barModel = DbBarData
    if db.is_closed():
        db.connect()
    db.create_tables([DbBarData])
    return barModel

class BarStorage:

    def __init__(self,db: Database):
        self.class_bar = _init_Bar_Model(db)


    def load_bar_data(
            self,
            symbol: str,
            driver: str,
            interval: Interval,
            start: datetime,
            end: datetime,
    ) -> Sequence[BarData]:
        s = (
            self.class_bar.select()
                .where(
                (self.class_bar.symbol == symbol)
                & (self.class_bar.driver == driver)
                & (self.class_bar.interval == interval.value)
                & (self.class_bar.datetime >= start)
                & (self.class_bar.datetime <= end)
            )
                .order_by(self.class_bar.datetime)
        )
        data = [db_bar.to_bar() for db_bar in s]
        return data




    def save_bar_data(self, datas: Sequence[BarData]):
        ds = [self.class_bar.from_bar(i) for i in datas]
        self.class_bar.save_all(ds)


    def get_newest_bar_data(
            self, symbol: str, driver: str, interval: "Interval"
    ) -> Optional["BarData"]:
        s = (
            self.class_bar.select()
                .where(
                (self.class_bar.symbol == symbol)
                & (self.class_bar.driver == driver)
                & (self.class_bar.interval == interval.value)
            )
                .order_by(self.class_bar.datetime.desc())
                .first()
        )
        if s:
            return s.to_bar()
        return None


    def get_oldest_bar_data(
            self, symbol: str, driver: str, interval: "Interval"
    ) -> Optional["BarData"]:
        s = (
            self.class_bar.select()
                .where(
                (self.class_bar.symbol == symbol)
                & (self.class_bar.driver == driver)
                & (self.class_bar.interval == interval.value)
            )
                .order_by(self.class_bar.datetime.asc())
                .first()
        )
        if s:
            return s.to_bar()
        return None





    def delete_bar_data(
            self,
            symbol: str,
            driver: str,
            interval: "Interval"
    ) -> int:
        """
        Delete all bar data with given symbol + exchange + interval.
        """
        query = self.class_bar.delete().where(
            (self.class_bar.symbol == symbol)
            & (self.class_bar.driver == driver)
            & (self.class_bar.interval == interval.value)
        )
        count = query.execute()
        return count


    def clean(self, symbol: str):
        self.class_bar.delete().where(self.class_bar.symbol == symbol).execute()
