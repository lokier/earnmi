from datetime import datetime, timedelta
from earnmi.chart.Chart import Chart
from earnmi.data.HistoryBarPool import HistoryBarPool
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from earnmi.data import import_data_from_jqdata


code = "300004"
startDate = datetime(2019,4,1)
endDate = datetime(2020,3,25)

historyData = HistoryBarPool(code,121)
historyData.initPool(startDate,endDate)
historyData.setToday(endDate)
bars = historyData.getData()

print(f"bar.size = {bars.__len__()}")


chart = Chart()
chart.setBarData(bars)
chart.open_rsi = True
chart.show()