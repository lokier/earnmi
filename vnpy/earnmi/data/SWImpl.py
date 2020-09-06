from builtins import list
from datetime import datetime, timedelta
from typing import Sequence
from vnpy.trader.constant import Exchange, Interval

from peewee import SqliteDatabase
from earnmi.uitl.utils import utils
from earnmi.data.SW import SW
from vnpy.trader.database.database_sql import init_by_sql_databease, SqlManager
from vnpy.trader.object import BarData
from vnpy.trader.utility import get_file_path

"""
  实现2014年到现在的数据。
"""
class SWImpl(SW):


    def __init__(self):
        database = f"sw_2_daily_bar.db"
        path = str(get_file_path(database))
        db = SqliteDatabase(path)
        self.__database_manager = init_by_sql_databease(db)

    def getSqlManager(self)->SqlManager:
        return self.__database_manager

    """
       返回申万二级行业数据
       """
    def getSW2List(self) -> list:
        return self.__sw_code_list

    """
        返回某个行业数据的日k线图
        """

    def getSW2Daily(self, code: str, start: datetime, end: datetime) -> Sequence["BarData"]:
        pass

    """
          返回某个行业数据的分时图
       """

    def getSW2Mintuely(self, code: str, date: datetime) -> Sequence["BarData"]:
        pass

    __sw_code_list = ["801011",
                      "801012",
                      "801013",
                      "801014",
                      "801015",
                      "801016",
                      "801017",
                      "801018",
                      "801021",
                      "801022",
                      "801023",
                      "801024",
                      "801031",
                      "801032",
                      "801033",
                      "801034",
                      "801035",
                      "801036",
                      "801037",
                      "801041",
                      "801042",
                      "801051",
                      "801052",
                      "801053",
                      "801054",
                      "801055",
                      "801061",
                      "801062",
                      "801071",
                      "801072",
                      "801073",
                      "801074",
                      "801075",
                      "801076",
                      "801081",
                      "801082",
                      "801083",
                      "801084",
                      "801085",
                      "801091",
                      "801092",
                      "801093",
                      "801094",
                      "801101",
                      "801102",
                      "801111",
                      "801112",
                      "801121",
                      "801122",
                      "801123",
                      "801124",
                      "801131",
                      "801132",
                      "801141",
                      "801142",
                      "801143",
                      "801144",
                      "801151",
                      "801152",
                      "801153",
                      "801154",
                      "801155",
                      "801156",
                      "801161",
                      "801162",
                      "801163",
                      "801164",
                      "801171",
                      "801172",
                      "801173",
                      "801174",
                      "801175",
                      "801176",
                      "801177",
                      "801178",
                      "801181",
                      "801182",
                      "801191",
                      "801192",
                      "801193",
                      "801194",
                      "801201",
                      "801202",
                      "801203",
                      "801204",
                      "801205",
                      "801211",
                      "801212",
                      "801213",
                      "801214",
                      "801215",
                      "801221",
                      "801222",
                      "801223",
                      "801224",
                      "801231",
                      "801711",
                      "801712",
                      "801713",
                      "801721",
                      "801722",
                      "801723",
                      "801724",
                      "801725",
                      "801731",
                      "801732",
                      "801733",
                      "801734",
                      "801741",
                      "801742",
                      "801743",
                      "801744",
                      "801751",
                      "801752",
                      "801761",
                      "801881"
                      ]


if __name__ == "__main__":
    import json


    def fetchDataForm(code:str,start:datetime,count:int)-> Sequence["BarData"]:
        import requests
        # 字符串格式
        dt = start.strftime('%Y%m%d')
        url = f"http://106.15.58.126/sw_k.action?username=raodongming&password=58edde63081e2ce001cf5800f68df36f&id={code}&num={count}&datetime={dt}&period=d"
        res = requests.get(url=url)
        text = res.text
        print(url)
        if text is None:
            return None

        lines = text.splitlines(False)

        if len(lines) < 2:
            return []

        bars = []
        for i in range(1, len(lines)):

            tokens = lines[i].split(",")
            if (tokens is None or len(tokens) < 3):
                continue
            print(f"{tokens}")
            dt = datetime.strptime(tokens[0], "%Y%m%d"),
            volume = float(tokens[5])
            open_price = float(tokens[1])
            high_price = float(tokens[2])
            low_price = float(tokens[3])
            close_price = float(tokens[4])

            bar = BarData(
                symbol=code,
                exchange=Exchange.SZSE,
                datetime=dt,
                interval=Interval.DAILY,
                volume=volume,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                # open_interest=1f,
                gateway_name="DB"
            )
            bars.append(bar)
        return bars

    def updateDataFrom2014(db:SqlManager,code:str,start:datetime):
        #清空数据
        db.clean(code)

        now = datetime.now()
        print(f"start updateDataFrom2014: code = {code}, form = {start}")
        count = 0
        while True:
            bars = fetchDataForm(code,start,1800);
            if len(bars) == 0:
                break;
            print(f"  fetchDataForm: {start},count = {len(bars)},end = {end}")
            end =  bars[-1].datetime;
            db.save_bar_data(bars)
            start = end + timedelta(days=1)
            count += len(bars)
            if start > now:
                break;
        print(f"finished updateDataFrom2014: code = {code}, form = {start},count ={count}")


    sw = SWImpl()
    db = sw.getSqlManager();
    list = sw.getSW2List();
    start_day = datetime.strptime("2016-5-09", "%Y-%m-%d")
    code = list[0]
    ##yyyyMMdd
    print(f"code:{code},{start_day.strftime('%Y%m%d%H%m')}")

    bars = fetchDataForm(list[0],start_day,5)
    print(f"bars.size={len(bars)}")
    print(f"{bars}")
    #def update(db:SqlManager,);
