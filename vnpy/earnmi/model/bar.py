from dataclasses import dataclass
from datetime import datetime,timedelta
from typing import List, Sequence

from peewee import Model, AutoField, CharField, DateTimeField, FloatField, Database, SqliteDatabase, chunked

from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.jqSdk import jqSdk
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

"""
最新的bar
"""
@dataclass
class LatestBar(object):
    code: str
    datetime: datetime
    volume: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    def __post_init__(self):
        """"""
        pass

    def toBarData(self)->BarData:
        return BarData(
                symbol=self.code,
                exchange=Exchange.SSE,
                datetime=self.datetime,
                interval=Interval.WEEKLY,
                volume=self.volume,
                open_price=self.open_price,
                high_price=self.high_price,
                low_price=self.low_price,
                close_price=self.close_price,
                gateway_name='arrangePrice'
            )

class LatestBarModel(Model):
    table_name = 'latest_bar'
    code = CharField(primary_key=True)
    datetime = DateTimeField()
    volume = FloatField()
    open_price = FloatField()
    high_price = FloatField()
    low_price = FloatField()
    close_price = FloatField()


    def to_dict(self):
        return self.__data__

    @staticmethod
    def from_data(data: LatestBar):
        db_data = LatestBarModel()
        db_data.code = data.code
        db_data.datetime = data.datetime
        db_data.volume = data.volume
        db_data.open_price = data.open_price
        db_data.high_price = data.high_price
        db_data.low_price = data.low_price
        db_data.close_price = data.close_price
        return db_data

    def to_data(self):
        data = LatestBar(
            code=self.code,
            datetime= self.datetime
        )
        data.volume = self.volume
        data.open_price = self.open_price
        data.high_price = self.high_price
        data.low_price = self.low_price
        data.close_price = self.close_price
        return data

class LatestBarDB:

    def __init__(self,db:Database):
        class LatestBarModelWrapper(LatestBarModel):
            class Meta:
                database = db
                table_name = LatestBarModel.table_name
        self.db = db
        self.latestBarModel = LatestBarModelWrapper
        if db.is_closed():
            db.connect()
        db.create_tables([LatestBarModelWrapper])
        self.__cach_latest_bar_map:{} = None

    def __loadCache(self):
        if self.__cach_latest_bar_map is None:
            s = (
                self.latestBarModel.select()
            )
            datas = [db_bar.to_data() for db_bar in s]
            lastedMap = {}
            for data in datas:
                lastedMap[data.code] = data
            self.__cach_latest_bar_map = lastedMap
        return self.__cach_latest_bar_map

    def load(self, codeList: [])->Sequence["LatestBar"]:
        latest_bar_map = self.__loadCache()
        ret = {}
        for code in codeList:
            bar = latest_bar_map.get(code)
            ret[code] = bar
        return ret

    def update(self, codeList: [], start=None, end=None):
        if start == None or end == None:
            end = datetime.now()
            start = utils.to_start_date(end)
        update_time = end
        assert not update_time is None
        todayBarsMap = jqSdk.fethcNowDailyBars(codeList,start,end)
        old_latest_bar_map = self.__loadCache()
        to_update_latest_bar = []
        for code,bar in  todayBarsMap.items():
            if bar is None:
                continue
            old_latestBar = old_latest_bar_map.get(code)
            if not old_latestBar is None:
                if old_latestBar.datetime >= bar.datetime:
                    ##非最新的数据，跳过
                    continue
            lastest_bar = LatestBar(code=bar.symbol,datetime=update_time)
            lastest_bar.volume = bar.volume
            lastest_bar.high_price = bar.high_price
            lastest_bar.low_price = bar.low_price
            lastest_bar.open_price = bar.open_price
            lastest_bar.close_price = bar.close_price
            to_update_latest_bar.append(lastest_bar)
        update_count = len(to_update_latest_bar)
        print(f"[LatestBarDB]: update count = {update_count}")
        if update_count > 0:
            self.__save(to_update_latest_bar)
            for latest_bar in to_update_latest_bar:
                self.__cach_latest_bar_map[latest_bar.code] = lastest_bar

    def __save(self, datas: List["LatestBar"]):
        ds = [self.latestBarModel.from_data(i) for i in datas]
        dicts = [i.to_dict() for i in ds]
        with self.db.atomic():
            for c in chunked(dicts, 50):
                self.latestBarModel.insert_many(c).on_conflict_replace().execute()


if __name__ == "__main__":

    db_file = SqliteDatabase("latest_bar2.db")
    db = LatestBarDB(db_file);
    now = datetime.now()

    print(f"size = {len(db.load(ZZ500DataSource.SZ500_JQ_CODE_LIST))}")
    #db.update(ZZ500DataSource.SZ500_JQ_CODE_LIST)

    # time = datetime.now() - timedelta(days=5)
    #
    # for i in range(0,5):
    #     start = utils.to_start_date(time)
    #     end = utils.to_end_date(time)
    #     db.update(ZZ500DataSource.SZ500_JQ_CODE_LIST,start=start,end=end)
    #     time = time + timedelta(days=1)



