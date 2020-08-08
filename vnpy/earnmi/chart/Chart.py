import string
from datetime import datetime, timedelta
from typing import List

import mplfinance as mpf
import pandas as pd
from werkzeug.routing import Map

from earnmi.chart.Indicator import Indicator
import abc

from vnpy.trader.object import BarData


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
    def getValues(self,indicator:Indicator,bar:BarData)->Map:
        pass

    def getColor(self,name:str):
        return 'b'



class Chart:
    window_size = 15
    open_obv = False  ##是否显示obv指标
    open_kdj = False  ##是否显示rsiv指标

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
        if (self.open_kdj):
            columns.append("kdj_k")
            columns.append("kdj_d")
            columns.append("kdj_j")
        if  not item  is None:
            item_names = item.getNames()
            item_size = len(item_names)
            for i in range(item_size):
                columns.append(item_names[i])
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
            if not item is None:
                item_names = item.getNames()
                item_size = len(item_names)
                item_value = item.getValues(indicator,bar);
                for i in range(item_size):
                    list.append(item_value[item_names[i]])
            data.append(list)
        trades = pd.DataFrame(data, index=index, columns=columns)
        apds = []
        if self.open_obv:
            apds.append(mpf.make_addplot(trades['obv'], panel='lower',color='g',secondary_y=True))
        if self.open_kdj:
            apds.append(mpf.make_addplot(trades['kdj_k'], panel='lower',color='r',secondary_y=True))
            apds.append(mpf.make_addplot(trades['kdj_d'], panel='lower',color='g',secondary_y=True))
            apds.append(mpf.make_addplot(trades['kdj_j'], panel='lower',color='b',secondary_y=True))
        if not item is None:
            item_names = item.getNames()
            item_size = len(item_names)
            for i in range(item_size):
                name = item_names[i]
                apds.append(mpf.make_addplot(trades[name],  color=item.getColor(name), secondary_y=True))
        mpf.plot(trades, type='candle', volume=True, mav=(5), figscale=1.3, style='yahoo',addplot=apds)

"""
 RSI指标
"""
class BollItem(IndicatorItem):

    def getNames(self) -> List:
        return ["boll_up","boll_down"]

    def getValues(self, indicator: Indicator,bar:BarData) -> Map:
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

    def getValues(self, indicator: Indicator,bar:BarData) -> Map:
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

    def getNames(self) -> List:
        return ["arron_up_25","arron_down_25"]

    def getValues(self, indicator: Indicator,bar:BarData) -> Map:
        values = {}
        if indicator.count >= 25:
            aroon_up, aroon_down = indicator.aroon(25)
            values["arron_up_25"] = aroon_up
            values["arron_down_25"] = aroon_down
        else:
            values["arron_up_25"] = 50
            values["arron_down_25"] = 50


        return values

    def getColor(self, name: str):
        if name == "arron_up_25":
            return 'r'
        return 'y'


if __name__ == "__main__":
    from earnmi.data.MarketImpl import MarketImpl

    code = "600155"
    # 801161.XSHG
    market = MarketImpl()
    market.addNotice(code)
    market.setToday(datetime.now())

    bars = market.getHistory().getKbars(code, 80)

    print(f"bar.size = {bars.__len__()}")

    chart = Chart()
    chart.setBarData(bars)
    chart.open_kdj = True
    chart.show(AroonItem())