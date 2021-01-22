from dataclasses import dataclass
from datetime import datetime,timedelta
from typing import List, Sequence

from peewee import Model, AutoField, CharField, DateTimeField, FloatField, Database, SqliteDatabase, chunked
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Exchange, Interval
import requests

import numpy as np
import re

@dataclass
class BarData:
    """
    Candlestick bar data of a certain trading period.
    """
    symbol: str
    datetime: datetime
    interval: Interval = None
    volume: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0
    _driver: str = ""  ##Bar驱动器名称，具体查看BarDriver.getName()




"""
最新的bar
"""
@dataclass
class LatestBar(object):

    code: str
    datetime: datetime
    name:str = None
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
                _driver="SSE",
                datetime=self.datetime,
                interval=Interval.WEEKLY,
                volume=self.volume,
                open_price=self.open_price,
                high_price=self.high_price,
                low_price=self.low_price,
                close_price=self.close_price,
            )

class LatestBarModel(Model):
    table_name = 'latest_bar'
    code = CharField(primary_key=True)
    name = CharField()
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
        db_data.name = data.name
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
        data.name = self.name
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


    def loadLatestBar(self,code:str)->LatestBar:
        latest_bar_map = self.__loadCache()
        bar = latest_bar_map.get(code)
        return bar

    def update(self, codeList: [], start=None, end=None):
        if start == None or end == None:
            end = datetime.now()
            start = utils.to_start_date(end)
        update_time = end
        assert not update_time is None
        latest_bar_list = self.fetchLatestBarFromSina(codeList)

        old_latest_bar_map = self.__loadCache()
        to_update_latest_bar = []
        for latest_bar in  latest_bar_list:
            old_latestBar = old_latest_bar_map.get(latest_bar.code)
            if not old_latestBar is None:
                if old_latestBar.datetime >= latest_bar.datetime:
                    ##非最新的数据，跳过
                    continue
            to_update_latest_bar.append(latest_bar)

        update_count = len(to_update_latest_bar)
        print(f"[LatestBarDB]: update count = {update_count}")
        if update_count > 0:
            self.__save(to_update_latest_bar)
            for latest_bar in to_update_latest_bar:
                self.__cach_latest_bar_map[latest_bar.code] = latest_bar

    def __save(self, datas: List["LatestBar"]):
        ds = [self.latestBarModel.from_data(i) for i in datas]
        dicts = [i.to_dict() for i in ds]
        with self.db.atomic():
            for c in chunked(dicts, 50):
                self.latestBarModel.insert_many(c).on_conflict_replace().execute()


    def toSinCode(self,code: str):
        offset = code.index(".")
        if offset > 0:
            code = code[:offset]
        assert code.isdigit()
        if code.startswith("6"):
            return f"sh{code}"
        else:
            return f"sz{code}"

    def fetchLatestBarFromSina(self, codeList):
        batch_size = 100
        size = len(codeList)
        bar_list = []
        for i in range(0,size,batch_size):
            sub_code_list = codeList[i:i+batch_size]
            sub_bar_list = self._fetchLatestBarFromSinaByBatch(sub_code_list)
            bar_list.extend(sub_bar_list)
        return bar_list


    def _fetchLatestBarFromSinaByBatch(self,codeList):
        codeSize = len(codeList)
        assert codeSize <=100
        sinaCodeList = np.array(codeList)
        for i in range(0, codeSize):
            sinaCodeList[i] = self.toSinCode(codeList[i])

        urlParams = ','.join(sinaCodeList)
        url = f"http://hq.sinajs.cn/list={urlParams}"
        res = requests.get(url=url)
        text = res.text
        matchObj = re.findall('var hq_str_.*?="([\s\S]+?)";', text, re.M | re.I)

        latestBarList = []
        if matchObj:
            for index, item in enumerate(matchObj):
                tokens = item.split(",")
                if len(tokens) < 32:
                    continue
                dt = datetime.strptime(f"{tokens[30]} {tokens[31]}", "%Y-%m-%d %H:%M:%S")
                bar = LatestBar(
                    code=codeList[index],
                    datetime=dt
                )
                bar.name = tokens[0]
                bar.open_price = float(tokens[1])
                bar.close_price = float(tokens[3])
                bar.high_price = float(tokens[4])
                bar.low_price = float(tokens[5])
                bar.volume = float(tokens[8])
                latestBarList.append(bar)
        return latestBarList


if __name__ == "__main__":

    db_file = SqliteDatabase("latest_bar2.db")
    db = LatestBarDB(db_file);
    now = datetime.now()

    print(f"size = {len(db.load(ZZ500DataSource.SZ500_JQ_CODE_LIST))}")
    db.update(ZZ500DataSource.SZ500_JQ_CODE_LIST)

    # time = datetime.now() - timedelta(days=5)
    #
    # for i in range(0,5):
    #     start = utils.to_start_date(time)
    #     end = utils.to_end_date(time)
    #     db.update(ZZ500DataSource.SZ500_JQ_CODE_LIST,start=start,end=end)
    #     time = time + timedelta(days=1)



