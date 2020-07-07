import string
from datetime import datetime, timedelta
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta
import jqdatasdk as jq
import numpy as np

from earnmi.chart.Indicator import Indicator
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from vnpy.trader.object import BarData
from vnpy.trader.utility import ArrayManager


class Chart:


    window_size = 15
    open_boll = False  ##是否显示布林指标
    open_obv = False  ##是否显示obv指标
    open_rsi = False  ##是否显示rsiv指标
    open_kdj = False  ##是否显示rsiv指标


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

        data = []
        index = []
        indicator = Indicator(self.window_size * 2)

        ### 初始化columns
        columns = ['Open', 'High', 'Low', 'Close', "Volume"]

        if self.open_boll:
            columns.append("boll_up")
            columns.append("boll_down")
        if(self.open_obv):
            columns.append("obv")
        if (self.open_rsi):
            columns.append("rsi")
        if (self.open_kdj):
            columns.append("kdj_k")
            columns.append("kdj_d")
            columns.append("kdj_j")

        for bar in bars:
            index.append(bar.datetime)
            list = [bar.open_price, bar.high_price, bar.low_price, bar.close_price, bar.volume]
            indicator.update_bar(bar)

            #添加布林指标数据
            if self.open_boll:
                if indicator.count >= self.window_size:
                    up, down = indicator.boll(self.window_size, 3.4)
                    list.append(up)
                    list.append(down)
                else:
                    list.append(bar.close_price)
                    list.append(bar.close_price)

            if self.open_obv:
                if indicator.count >= self.window_size:
                    obv = indicator.obv(self.window_size)
                    list.append(obv)
                else:
                    list.append(bar.volume)

            if self.open_rsi:
                if indicator.count >= self.window_size:
                    rsi = indicator.rsi(self.window_size)
                    list.append(rsi)
                else:
                    list.append(50)

            if self.open_kdj:
                if indicator.count >= self.window_size:
                    k,d,j = indicator.kdj(array=False)
                    list.append(k)
                    list.append(d)
                    list.append(j)
                else:
                    list.append(50)
                    list.append(50)
                    list.append(50)

            data.append(list)


        trades = pd.DataFrame(data, index=index, columns=columns)

        apds = []

        # 添加布林指标数据
        if self.open_boll:
            apds.append(mpf.make_addplot(trades['boll_up'], linestyle='dashdot'))
            apds.append(mpf.make_addplot(trades['boll_down'], linestyle='dashdot'))

        if self.open_obv:
            apds.append(mpf.make_addplot(trades['obv'], panel='lower',color='g',secondary_y=True))
        if self.open_rsi:
            apds.append(mpf.make_addplot(trades['rsi'], panel='lower',color='b',secondary_y=True))

        if self.open_kdj:
            apds.append(mpf.make_addplot(trades['kdj_k'], panel='lower',color='r',secondary_y=True))
            apds.append(mpf.make_addplot(trades['kdj_d'], panel='lower',color='g',secondary_y=True))
            apds.append(mpf.make_addplot(trades['kdj_j'], panel='lower',color='b',secondary_y=True))

        mpf.plot(trades, type='candle', volume=True, mav=(5), figscale=1.3, style='yahoo',addplot=apds)


