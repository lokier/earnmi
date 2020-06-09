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

from vnpy.trader.utility import ArrayManager

symbol = "600009";
bars = database_manager.load_bar_data(symbol,Exchange.SSE,Interval.DAILY,datetime(2019,4,1),datetime(2020,3,25))
bars.__reversed__()
data = []
index=[]
am = ArrayManager()
boll_window = 18
boll_dev = 3.4

# for bar in bars:
#     am.update_bar(bar)
#     if am.count >= boll_window:
#         up,down = am.boll(boll_window,boll_dev)
#     else:
#         up,down = [bar.close_price,bar.close_price]
#     index.append(bar.datetime)
#     data.append([bar.open_price,bar.high_price,bar.low_price,bar.close_price,bar.volume,up,down])
#
#
#
#
# data = pd.DataFrame(data,index=index,columns=['Open','High','Low','Close',"Volume","Boll_Up","Boll_Down"])
#
# #print(data)
# apds = [ mpf.make_addplot(data['Boll_Up'],linestyle='dashdot'),
#          mpf.make_addplot(data['Boll_Down'], linestyle='dashdot'),
#        ]
#
#
# mpf.plot(data, type='candle', volume=True, mav=(5), figscale=0.9, style='yahoo',addplot=apds)

char = Chart()
char.setBarData(bars)
char.open_boll = True
#char.openBoll(False)
char.show()




