from datetime import datetime, timedelta
from earnmi.chart.Chart import Chart
from earnmi.data.HistoryBarPool import HistoryBarPool
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from earnmi.data import import_data_from_jqdata


code = "300004"
startDate = datetime(2019,4,1)
endDate = datetime(2020,3,25)


exchange = Exchange.SZSE
if code.startswith("6"):
    exchange = Exchange.SSE

bars = database_manager.load_bar_data(code,exchange,Interval.DAILY,startDate,endDate)

historyData = HistoryBarPool(code,120)
historyData.initPool(startDate,endDate)
historyData.setToday(endDate)
bars = historyData.getData()

print(f"bar.size = ${bars.__len__()}")


if(bars.__len__() < 1):
    #从网络加载
    print(f"从网络获取数据：{code}")
    import_data_from_jqdata.save_bar_data_from_jqdata(code,Interval.DAILY,startDate,endDate)
    bars = database_manager.load_bar_data(code,exchange,Interval.DAILY,startDate,endDate)
else:
    print(f"从缓存获取数据:{code}")

chart = Chart()
chart.setBarData(bars)
chart.open_rsi = True
chart.show()