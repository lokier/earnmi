from datetime import datetime, timedelta
from earnmi.chart.Chart import Chart, BollItem
from earnmi.data.MarketImpl import MarketImpl
from earnmi.data.SWImpl import SWImpl
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from earnmi.data import import_data_from_jqdata


code = "600196"

start = datetime(2020, 5, 1)
end = datetime.now();
#end = datetime(2020, 8, 17)

#code = '000300'
#801161.XSHG
#market = MarketImpl()
#market.addNotice(code)
#market.setToday(datetime.now())
#bars = market.getHistory().getKbarFrom(code,start)

sw = SWImpl()
codeList = sw.getSW2List()
code = codeList[1]
start = datetime(2014, 5, 1)
bars = sw.getSW2Daily(code,start,end)



print(f"bar.size = {bars.__len__()}")


chart = Chart()
chart.show(bars,BollItem())
#chart.showCompare(bars,"000300")