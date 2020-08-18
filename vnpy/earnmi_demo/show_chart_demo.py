from datetime import datetime, timedelta
from earnmi.chart.Chart import Chart, BollItem
from earnmi.data.MarketImpl import MarketImpl
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from earnmi.data import import_data_from_jqdata


code = "600196"

start = datetime(2020, 5, 1)
end = datetime.now();
#end = datetime(2020, 8, 17)

#code = '000300'
#801161.XSHG
market = MarketImpl()
market.addNotice(code)
market.setToday(datetime.now())


#bars = market.getHistory().getKbars(code,80)
bars = market.getHistory().getKbarFrom(code,start)

print(f"bar.size = {bars.__len__()}")


chart = Chart()
chart.show(bars,BollItem())
#chart.showCompare(bars,"000300")