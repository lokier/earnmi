from datetime import datetime, timedelta
from earnmi.chart.Chart import Chart
from earnmi.data.HistoryBarPool import HistoryBarPool
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from earnmi.data import import_data_from_jqdata

def assertEqual(d1, d2):
    if( not d1.__eq__(d2)):
        raise AssertionError(f"asset fail!,d1={d1},d2={d2}")

def assertLittle(d1, d2):
    if (not d1.__le__(d2)):
        raise AssertionError(f"asset fail!,d1={d1},d2={d2}")

code = "300004"
startDate = datetime(2019,4,1)
endDate = datetime(2020,5,1)
today = datetime(2020,3,24)
keepN = 88

historyData = HistoryBarPool(code,keepN)
historyData.initPool(startDate,endDate)

exchange = Exchange.SZSE
if code.startswith("6"):
    exchange = Exchange.SSE




for  i in range(0,20):
    changed = historyData.setToday(today)
    if(not changed):
         continue

    #返回今天以前的历史数据
    bars1 = historyData.getData()
    bars2 = database_manager.load_bar_data(code,exchange,Interval.DAILY,bars1[0].datetime,bars1[-1].datetime)
    assertEqual(bars1.__len__(), bars2.__len__())
    assertEqual(bars1[0].datetime, bars2[0].datetime)
    assertEqual(bars1[-1].datetime, bars2[-1].datetime)
    assertLittle(bars1[-1].datetime, today)
    assertEqual(bars1.__len__(), keepN)

    today = today + timedelta(days=1)

    print(f"bars.length = {bars1.__len__()}")
    print(f"bars.length = {bars2.__len__()}")