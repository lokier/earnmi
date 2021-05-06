import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

import mplfinance as mpf
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np

from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.constant import Exchange, Interval
from werkzeug.routing import Map

from earnmi.chart.Indicator import Indicator
import abc

from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData

@dataclass
class Signal:
    buy = False  # 买入信号
    sell = False  #卖出信号
    redTag = False  #红色标记

    hasBuy = False #是否已经买入

    def reset(self):
        self.buy = False
        self.sell = False

@dataclass
class HoldBar():
    code:str
    start_time:datetime
    end_time:datetime
    open_price: float = 0.0
    close_price: float = 0.0
    high_price:float = 0.0
    low_price:float = 0.0
    bars:[] = None
    _days:int = 0

    def __post_init__(self):
        """"""
        self.bars = []

    def getCostPct(self):
        start_price = self.open_price
        return (self.close_price- start_price) / start_price

    def getDays(self):
        return (self._days)

    def toBarData(self,new_open_price:float = None)->BarData:

        open_price = self.open_price
        close_price = self.close_price
        high_price = self.high_price
        low_price = self.low_price

        if not new_open_price is None:
            close_price = close_price * new_open_price / open_price
            high_price = high_price * new_open_price / open_price
            low_price = low_price * new_open_price / open_price
            open_price = new_open_price

        bar = BarData(
            symbol=self.code,
            exchange=Exchange.SSE,
            datetime=self.start_time,
            interval=Interval.WEEKLY,
            volume = self.getDays(),
            open_price= open_price,
            high_price = high_price,
            low_price= low_price,
            close_price= close_price,
            gateway_name='holdData'
        )
        return bar

class HoldBarMaker:

    _hold_bars:['HoldBar'] = None
    __current_hold_bar: HoldBar = None
    def __init__(self):
        self.reset()

    def getHoldBars(self) ->['HoldBar']:
        return self._hold_bars

    def reset(self):
        self.__current_hold_bar = None
        self._hold_bars = []

    def isHoldStarting(self) ->bool:
        return not self.__current_hold_bar is None

    def onHoldStart(self,bar:BarData) ->HoldBar:

        if( self.isHoldStarting()):
            raise RuntimeError("you must call onHoldEnd first()")

        holdBar = HoldBar(code=bar.symbol, start_time=bar.datetime, end_time=bar.datetime)
        """
             真正的盈利开始算是从第一天收盘价作为买入点,这里于
         """
        holdBar.open_price = (bar.open_price + bar.close_price) / 2;
        holdBar.high_price = bar.high_price;
        holdBar.close_price = bar.close_price;
        holdBar.low_price = min(bar.low_price,bar.open_price)

        self.__current_hold_bar = holdBar
        self.onHoldUpdate(bar)
        return holdBar

    def onHoldEnd(self):
        if (self.__current_hold_bar is None):
            raise RuntimeError("you must call onHoldStart first()")
        else:
            self._hold_bars.append(self.__current_hold_bar)

        self.__current_hold_bar  = None

    def onHoldUpdate(self,bar:BarData):
        holdBar = self.__current_hold_bar
        if holdBar is None:
            return
        holdBar.high_price = max(holdBar.high_price, bar.high_price)
        holdBar.low_price = min(holdBar.low_price, bar.low_price)
        holdBar.close_price = bar.close_price
        holdBar.end_time = bar.datetime
        holdBar._days = holdBar._days + 1
        holdBar.bars.append(bar)
        pass


class IndicatorItem(metaclass=abc.ABCMeta):

    def __init__(self,generateHoldbars:bool = True):
        if generateHoldbars:
            self._holdbarMaker = HoldBarMaker()
        else:
            self._holdbarMaker = None
        self.names = []
        self.colors = ['b', 'g', 'r', 'black']
        self.init()

    def init(self):
        pass

    """
        返回指标名称的在某个点的值。
        """
    @abc.abstractmethod
    def getValues(self, indicator: Indicator, bar: BarData, signal: Signal) -> Map:
        pass

    def getHoldBars(self)->['HoldBar']:
        if(self._holdbarMaker is None):
            return []
        return self._holdbarMaker._hold_bars


    def getNames(self)->List:
        return self.names


    def getColor(self, name: str):
        index = self.names.index(name)
        if index >= 0:
            return self.colors[index]
        return 'r'

    """
    是否在底部显示
    """
    def isLowerPanel(self) ->bool:
        return False


class Chart:

    def __init__(self):
        pass
        #self.holdBar:HoldBar = None

    def run(self,bars:list,item:IndicatorItem=None):
        try:
            if (bars[0].datetime > bars[-1].datetime):
                bars = bars.__reversed__()
        except AttributeError:
            print(f"sfsdfdsf")
        data = []
        index = []
        indicator = Indicator()
        ### 初始化columns
        columns = ['Open', 'High', 'Low', 'Close', "Volume"]

        holdbarMaker:HoldBarMaker = None
        if not item is None:
            holdbarMaker = item._holdbarMaker
            if not holdbarMaker is None:
                holdbarMaker.reset()
            item_names = item.getNames()
            item_size = len(item_names)
            for i in range(item_size):
                columns.append(item_names[i])
            columns.append("signal_buy")
            columns.append("signal_sell")
            columns.append("signal_redTag")

        item_signal_buy_open = False
        item_signal_sell_open = False
        item_signal_redTag_open = False

        item_signal = Signal()
        ##current_hold_bar: HoldBar = None
        has_buy = False;
        for bar in bars:
            if not BarUtils.isOpen(bar):
                ##没开盘
                if len(list)> 0:
                    index.append(bar.datetime)
                    list = data[-1]
            else:
                index.append(bar.datetime)
                list = [bar.open_price, bar.high_price, bar.low_price, bar.close_price, bar.volume]
                indicator.update_bar(bar)
                if not item is None:
                    item_names = item.getNames()
                    item_size = len(item_names)
                    item_signal.reset()
                    item_signal.hasBuy = has_buy
                    item_value = item.getValues(indicator, bar, item_signal);
                    for i in range(item_size):
                        list.append(item_value[item_names[i]])
                    if item_signal.buy:
                        list.append(bar.low_price * 0.99)
                        item_signal_buy_open = True
                        has_buy = True
                        ##生成一个新的holdbar。
                        if not holdbarMaker is None:
                            holdbarMaker.onHoldStart(bar)

                    else:
                        ##更新holdBar
                        if not holdbarMaker is None:
                            holdbarMaker.onHoldUpdate(bar)

                        list.append(np.nan)

                    if item_signal.sell:
                        list.append(bar.high_price * 1.01)
                        item_signal_sell_open = True
                        has_buy = False
                        ##结束目前的HoldBar
                        if not holdbarMaker is None:
                            holdbarMaker.onHoldEnd()
                    else:
                        list.append(np.nan)

                    if item_signal.redTag:
                        item_signal_redTag_open = True
                        list.append(bar.low_price * 0.99)
                    else:
                        list.append(np.nan)
            data.append(list)

        trades = pd.DataFrame(data, index=index, columns=columns)
        return trades,item_signal_buy_open,item_signal_sell_open,item_signal_redTag_open


    """
    显示图表
    """
    def show(self,bars:list,item:IndicatorItem=None,savefig:str=None):

        trades,item_signal_buy_open,item_signal_sell_open,item_signal_redTag_open = self.run(bars,item);
        apds = []

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
                apds.append(mpf.make_addplot(trades['signal_buy'], scatter=True,markersize=100,color='b',marker='^'))
            if  item_signal_sell_open:
                apds.append(mpf.make_addplot(trades['signal_sell'], scatter=True,markersize=100,color='g',marker='v'))
            if item_signal_redTag_open:
                apds.append(mpf.make_addplot(trades['signal_redTag'], scatter=True,markersize=100,color='r',marker='-'))


        if savefig is None:
            mpf.plot(trades, type='candle', volume=True, mav=(5), figscale=1.3,addplot=apds)
        else:
            mpf.plot(trades, type='candle', mav=(5), figscale=1.3,addplot=apds,savefig =savefig)
            plt.close()



    """
    比较走势
    code: 指数代码
    """
    def showCompare(self,bars:[],code:str):
        from earnmi.data.MarketImpl import Market2Impl
        market = Market2Impl()
        market.addNotice(code)
        today:datetime = bars[-1].datetime
        market.setToday(today + timedelta(days=1))
        start :datetime = bars[0].datetime;
        baseBars = market.getHistory().getKbarFrom(code,datetime(start.year,start.month,start.day))

        #baseBar = mainBar
        ### 初始化columns
        columns = ['Open', 'High', 'Low', 'Close', "Volume","Close2"]
        data = []
        index = []
        bars1 = baseBars;
        bars2 = bars
        size1 = len(bars1)
        size2 = len(bars2)
        rate =  bars1[0].close_price / bars2[0].close_price
        bar_pre_2 = bars2[0]
        i2 = 0
        for i1 in range(size1):
           bar1 = bars1[i1]
           index.append(bar1.datetime)
           list = [bar1.open_price, bar1.high_price, bar1.low_price, bar1.close_price, bar1.volume]

           if i2 < size2:
               bar2 = bars2[i2]
               if utils.is_same_day(bar1.datetime,bar2.datetime):
                   list.append(bar2.close_price * rate)
                   bar_pre_2 = bar2
                   i2 = i2 + 1
               else:
                   ##bar2缺少今天数据。
                   list.append(bar_pre_2.close_price * rate)
               ##保证i2要大于大
               while(i2 < size2):
                   bar2 = bars2[i2]
                   days = (bar2.datetime - bar1.datetime).days
                   if days > 0 :
                       break
                   i2 =i2+1
           else:
               list.append(bar_pre_2.close_price* rate)
           data.append(list)

        trades = pd.DataFrame(data, index=index, columns=columns)
        apds = []
        apds.append(mpf.make_addplot(trades['Close'], color='gray'))
        apds.append(mpf.make_addplot(trades['Close2'], color='r'))
        mpf.plot(trades, type='line',  figscale=1.3, addplot=apds)
        pass


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
            aroon_down,aroon_up = indicator.aroon(25,True)
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
    from earnmi.data.MarketImpl import Market2Impl

    code = "600155"
    # 801161.XSHG
    market = Market2Impl()
    market.addNotice(code)
    market.setToday(datetime.now())

    bars = market.getHistory().getKbars(code, 360)

    print(f"bar.size = {bars.__len__()}")

    chart = Chart()
    #chart.open_kdj = True
    #chart.show(bars,KDJItem())
    chart.showCompare(bars,"000300")