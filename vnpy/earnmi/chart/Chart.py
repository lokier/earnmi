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
from vnpy.trader.utility import ArrayManager


class Chart:


    window_size = 15
    open_boll = False  ##是否显示布林指标


    """
    设置数据
    """
    def setBarData(self,bars:list) :
       self.barDatas = bars



    """
    显示图表
    """
    def show(self):
        bars = self.barDatas;
        if(bars[0].datetime > bars[-1].datetime):
            bars = bars.__reversed__()
        print(bars)
        data = []
        index = []
        am = ArrayManager(self.window_size * 2)

        ### 初始化columns
        columns = ['Open', 'High', 'Low', 'Close', "Volume"]

        enable_bool = self.open_boll
        if enable_bool:
            columns.append("boll_up")
            columns.append("boll_down")

        for bar in bars:
            index.append(bar.datetime)
            list = [bar.open_price, bar.high_price, bar.low_price, bar.close_price, bar.volume]
            am.update_bar(bar)

            #添加布林指标数据
            if enable_bool:
                if am.count >= self.window_size:
                    up, down = am.boll(self.window_size, 3.4)
                    list.append(up)
                    list.append(down)
                else:
                    list.append(bar.close_price)
                    list.append(bar.close_price)

            data.append(list)


        trades = pd.DataFrame(data, index=index, columns=columns)

        apds = []

        # 添加布林指标数据
        if enable_bool:
            apds.append(mpf.make_addplot(trades['boll_up'], linestyle='dashdot'))
            apds.append(mpf.make_addplot(trades['boll_down'], linestyle='dashdot'))


        mpf.plot(trades, type='candle', volume=True, mav=(5), figscale=0.9, style='yahoo',addplot=apds)


