import string
from datetime import datetime, timedelta
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta
from earnmi.chart.Chart import Chart
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from vnpy.trader.object import BarData

import jqdatasdk as jq
import numpy as np

symbol = "600009";
bars = database_manager.load_bar_data(symbol,Exchange.SSE,Interval.DAILY,datetime(2018,4,1),datetime(2020,3,25))
data = []
index=[]
for bar in bars:
    index.append(bar.datetime)
    data.append([bar.open_price,bar.high_price,bar.low_price,bar.close_price,bar.volume])

data = pd.DataFrame(data,index=index,columns=['Open','High','Low','Close',"Volume"])
#print(data)

chart = Chart()

chart.setBarData(bars)
chart.show()




