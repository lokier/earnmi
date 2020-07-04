from datetime import datetime

import talib
import numpy

from earnmi.chart.Chart import Chart
from earnmi.data.import_data_from_jqdata import save_bar_data_from_jqdata
from vnpy.trader.database import database_manager
from vnpy.trader.object import BarData

from vnpy.trader.constant import Exchange, Interval

import pandas as pd
import numpy as np
code = "601318" #在datetime(2019, 2, 27, 9, 48)，到达 high_price=68.57

start_day = datetime(2019, 2, 28,1)
end_day = datetime(2019, 2, 28,23)

exchange = Exchange.SZSE
if (code.startswith("6")):
     exchange = Exchange.SSE

database_manager.delete_bar_data(code,exchange,Interval.MINUTE)
count = save_bar_data_from_jqdata(code, Interval.MINUTE, start_date=start_day, end_date=end_day)
db_data = database_manager.load_bar_data(code, exchange, Interval.MINUTE, start_day, end_day)


high_price_bar = db_data[0]

index = 0
for i in range(len(db_data)):
    print(f"{db_data[i].datetime}:open = {db_data[i].open_price},close={db_data[i].close_price}")
    if db_data[index].high_price < db_data[i].high_price:
        index = i

print(f"high: {db_data[index].datetime}:open = {db_data[index].open_price},close={db_data[index].close_price}")

chart = Chart()
chart.setBarData(db_data)
chart.open_rsi = True
chart.show()

#print(db_data[index])

