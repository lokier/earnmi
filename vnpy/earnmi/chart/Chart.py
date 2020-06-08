import string
from datetime import datetime, timedelta
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta
import jqdatasdk as jq
import numpy as np
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from vnpy.trader.object import BarData

class Chart:



    """
    设置数据
    """
    def setBarData(self,bars:list) :
       data = []
       index = []
       for bar in bars:
           index.append(bar.datetime)
           data.append([bar.open_price, bar.high_price, bar.low_price, bar.close_price, bar.volume])
       trades = pd.DataFrame(data, index=index, columns=['Open', 'High', 'Low', 'Close', "Volume"])
       self.data = trades


    """
    显示图表
    """
    def show(self):
        mpf.plot(self.data, type='candle', volume=True, mav=(5), figscale=0.9, style='yahoo')
        pass

