from datetime import datetime, timedelta
from earnmi.chart.Chart import Chart, BollItem
from earnmi.data.MarketImpl import MarketImpl
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from earnmi.data import import_data_from_jqdata


code = "600155"
#code = '000300'
#801161.XSHG
market = MarketImpl()
market.addNotice(code)
market.setToday(datetime.now())


bars = market.getHistory().getKbars(code,80)

print(f"bar.size = {bars.__len__()}")


chart = Chart()
chart.open_obv = True
chart.show(bars,BollItem())
#chart.showCompare(bars,"000300")