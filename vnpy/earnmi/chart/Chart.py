import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

import mplfinance as mpf
import pandas as pd
import numpy as np
from werkzeug.routing import Map

from earnmi.chart.Indicator import Indicator
import abc

from vnpy.trader.object import BarData

@dataclass
class Signal:
    buy = False  # 买入信号
    sell = False  #卖出信号

    def reset(self):
        self.buy = False
        self.sell = False

class IndicatorItem(metaclass=abc.ABCMeta):

    """
    返回指标名称.
    """
    @abc.abstractmethod
    def getNames(self)->List:
        pass

    """
    返回指标名称的在某个点的值。
    """
    @abc.abstractmethod
    def getValues(self,indicator:Indicator,bar:BarData,signal:Signal)->Map:
        pass

    def getColor(self,name:str):
        return 'b'

    """
    是否在底部显示
    """
    def isLowerPanel(self) ->bool:
        return False


class Chart:
    window_size = 15
    open_obv = False  ##是否显示obv指标

    """
    设置数据
    """
    def setBarData(self,bars:list) :
       self.barDatas = bars

    """
    显示图表
    """
    def show(self,item:IndicatorItem=None):
        bars = self.barDatas;
        if(bars[0].datetime > bars[-1].datetime):
            bars = bars.__reversed__()
        data = []
        index = []
        indicator = Indicator(self.window_size * 2)
        ### 初始化columns
        columns = ['Open', 'High', 'Low', 'Close', "Volume"]
        if(self.open_obv):
            columns.append("obv")
        if  not item  is None:
            item_names = item.getNames()
            item_size = len(item_names)
            for i in range(item_size):
                columns.append(item_names[i])
            columns.append("signal_buy")
            columns.append("signal_sell")

        item_signal_buy_open = False
        item_signal_sell_open = False
        item_signal = Signal()

        for bar in bars:
            index.append(bar.datetime)
            list = [bar.open_price, bar.high_price, bar.low_price, bar.close_price, bar.volume]
            indicator.update_bar(bar)
            if self.open_obv:
                if indicator.count >= self.window_size:
                    obv = indicator.obv(self.window_size)
                    list.append(obv)
                else:
                    list.append(bar.volume)

            if not item is None:
                item_names = item.getNames()
                item_size = len(item_names)
                item_signal.reset()
                item_value = item.getValues(indicator,bar,item_signal);
                for i in range(item_size):
                    list.append(item_value[item_names[i]])
                if  item_signal.buy:
                    list.append(bar.low_price * 0.99)
                    item_signal_buy_open = True
                else:
                    list.append(np.nan)
                if item_signal.sell:
                    list.append(bar.high_price * 1.01)
                    item_signal_sell_open = True
                else:
                    list.append(np.nan)
            data.append(list)

        trades = pd.DataFrame(data, index=index, columns=columns)
        apds = []
        if self.open_obv:
            apds.append(mpf.make_addplot(trades['obv'], panel='lower',color='g',secondary_y=True))

        if not item is None:
            item_names = item.getNames()
            item_size = len(item_names)
            for i in range(item_size):
                name = item_names[i]
                if item.isLowerPanel():
                    apds.append(mpf.make_addplot(trades[name],  panel='lower',color=item.getColor(name), secondary_y=True))
                else:
                    apds.append(mpf.make_addplot(trades[name],  color=item.getColor(name), secondary_y=True))

            if  item_signal_buy_open:
                apds.append(mpf.make_addplot(trades['signal_buy'], scatter=True,markersize=100,color='r',marker='^'))
            if  item_signal_sell_open:
                apds.append(mpf.make_addplot(trades['signal_sell'], scatter=True,markersize=100,color='g',marker='v'))

        mpf.plot(trades, type='candle', volume=True, mav=(5), figscale=1.3,addplot=apds)

"""
 KDJ指标
"""
class KDJItem(IndicatorItem):

    def getNames(self) -> List:
        return ["k","d","j"]

    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        if indicator.count >= 15:
            k, d, j = indicator.kdj(array=False)
            values["k"] = k
            values["d"] = d
            values["j"] = j
        else:
            values["k"] = 50
            values["d"] = 50
            values["j"] = 50
        return values

    def getColor(self, name: str):
        if name == "k":
            return 'r'
        if name == "d":
            return 'g'
        return 'b'

    def isLowerPanel(self):
        return True

"""
 RSI指标
"""
class BollItem(IndicatorItem):

    def getNames(self) -> List:
        return ["boll_up","boll_down"]


    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        if indicator.count >= 15:
            up, down = indicator.boll(15, 3.4)
            values["boll_up"] = up
            values["boll_down"] = down

        else:
            values["boll_up"] = bar.close_price
            values["boll_down"] = bar.close_price
        return values

    def getColor(self, name: str):
        if name == "boll_up":
            return 'r'
        return 'y'




"""
 RSI指标
"""
class RSIItem(IndicatorItem):

    def getNames(self) -> List:
        return ["RSI6","RSI12"]

    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        windonwSize = 6;
        if indicator.count >= windonwSize:
            rsi = indicator.rsi(windonwSize)
            values["RSI6"] = rsi
        else:
            values["RSI6"] = 50

        windonwSize = 12;
        if indicator.count >= windonwSize:
            rsi = indicator.rsi(windonwSize)
            values["RSI12"] = rsi
        else:
            values["RSI12"] = 50

        return values

    def getColor(self, name: str):
        if name == "RSI6":
            return 'r'
        return 'y'

"""
 RSI指标
"""
class AroonItem(IndicatorItem):

    has_bug = False

    def getNames(self) -> List:
        return ["arron_up_25","arron_down_25"]

    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        if indicator.count >= 25:
            aroon_up, aroon_down = indicator.aroon(25,True)
            values["arron_up_25"] = aroon_up[-1]
            values["arron_down_25"] = aroon_down[-1]

            need_hold = aroon_up[-1] > 50  and  aroon_up[-1] > aroon_down[-1]
            if need_hold:
                if self.has_bug == False:
                    signal.buy = True
                    self.has_bug = True
            else:
                if( self.has_bug == True):
                    signal.sell = True
                    self.has_bug = False

        else:
            values["arron_up_25"] = 50
            values["arron_down_25"] = 50


        return values

    def getColor(self, name: str):
        if name == "arron_up_25":
            return 'r'
        return 'y'

    def isLowerPanel(self):
        return True


if __name__ == "__main__":
    from earnmi.data.MarketImpl import MarketImpl

    code = "600155"
    # 801161.XSHG
    market = MarketImpl()
    market.addNotice(code)
    market.setToday(datetime.now())

    bars = market.getHistory().getKbars(code, 360)

    print(f"bar.size = {bars.__len__()}")

    chart = Chart()
    chart.setBarData(bars)
    #chart.open_kdj = True
    chart.show(KDJItem())