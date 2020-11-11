from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence

from peewee import *
from vnpy.trader.object import BarData


@dataclass
class OpOrder:
    id = None
    code:str
    buy_price:float
    sell_price:float
    create_time:datetime;

    pass



class OpOrderDataBase:

    def __init__(self,dbFile:str):
        db = SqliteDatabase(dbFile)
        self.dao = OpOrderDataBase.init_models(db)

    def loadById(self,id)->Optional["OpOrder"]:
        s = (
            self.dao.select()
                .where(
                (self.dao.id == id)
            )
            .first()
        )
        if s:
            return s.to_data()
        return None

    def load(self,start: datetime,end: datetime) -> Sequence["OpOrder"]:
        s = (
            self.dao.select()
                .where(
                (self.dao.create_time >= start)
                & (self.dao.create_time <= end)
            )
                .order_by(self.dao.create_time)
        )
        data = [db_bar.to_data() for db_bar in s]
        return data

    def save(self,data:OpOrder):

        self.dao.save_all([self.dao.from_data(data)])

    def saveAll(
        self,
        datas: Sequence["OpOrder"],
    ):
        ds = [self.dao.from_data(i) for i in datas]
        self.dao.save_all(ds)

    def clean(self, code:str):
        self.dao.delete().where(self.dao.code == code).execute()

    def cleanAll(self):
        self.dao.delete().execute()

    def count(self):
        return self.dao.select().count()

    def init_models(db: Database):
        class OpOrderData(Model):
            """
            Candlestick bar data for database storage.

            Index is defined unique with datetime, interval, symbol
            """
            id = AutoField()
            code: str = CharField()
            create_time: datetime = DateTimeField()
            buy_price: float = FloatField()
            sell_price: float = FloatField()

            def to_dict(self):
                return self.__data__

            class Meta:
                database = db
                indexes = ((("code", "create_time"), True),)



            @staticmethod
            def from_data(bar: OpOrder):
                """
                Generate DbBarData object from BarData.
                """
                db_bar = OpOrderData()
                db_bar.id = bar.id
                db_bar.code = bar.code
                db_bar.create_time = bar.create_time
                db_bar.buy_price = bar.buy_price
                db_bar.sell_price = bar.sell_price
                return db_bar

            def to_data(self):
                """
                Generate BarData object from DbBarData.
                """
                bar = OpOrder(
                    code=self.code,
                    create_time=self.create_time,
                    sell_price=self.sell_price,
                    buy_price=self.buy_price,
                )
                bar.id = self.id
                return bar

            @staticmethod
            def save_all(objs: List["OpOrderData"]):
                """
                save a list of objects, update if exists.
                """
                dicts = [i.to_dict() for i in objs]
                with db.atomic():
                    for c in chunked(dicts, 50):
                            OpOrderData.insert_many(
                                c).on_conflict_replace().execute()


        db.connect()
        db.create_tables([OpOrderData])
        return OpOrderData