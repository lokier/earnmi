from dataclasses import dataclass
from datetime import datetime

from earnmi.chart.Chart import HoldBar
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange
from earnmi.chart.Indicator import Indicator
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.object import BarData
import numpy as np

"""
度量各指标因子：
    根据指标的计算一段HoldBar, 通过计算holdbar的
    平均持有天数、
    平均pct，
    发生率来评价系统的好坏。
"""
class IndicatorMeasure:
    def __init__(self):
        self.barOccurDay={} ##交易日
        self.holdBarMapList = {}
        self.holdingBarMap = {}

    def newSession(self):
        for name,holdbar in self.holdingBarMap.items():
            if not holdbar is None:
                self.__put_holdBar(name,holdbar)
        self.holdingBarMap.clear()
    """
    是否持有。
    """
    def measure(self, name: str, bar: BarData, isHold: bool):
        holdingBar:HoldBar = self.holdingBarMap.get(name)
        if isHold:
            if holdingBar is None:
                #开始持有。
                holdingBar = self.__crateHoldBars(bar)
                self.holdingBarMap[name] = holdingBar
            self.__onHoldUpdate(holdingBar,bar)
        else:
            if not holdingBar is None:
                ##结束持有
                self.__onHoldUpdate(holdingBar, bar)
                self.__put_holdBar(name,holdingBar)
                self.holdingBarMap[name] = None
        ###当天记作为交易日。
        self.barOccurDay[self.__datetimeKey(bar.datetime)] = True
        pass
    def __put_holdBar(self,name,holdbar):
        holdbarList = self.holdBarMapList.get(name)
        if holdbarList is None:
            holdbarList = []
            self.holdBarMapList[name] = holdbarList
        holdbarList.append(holdbar)

    def __datetimeKey(self,dt:datetime):
        return dt.year * 13 * 33 + dt.month * 33 + dt.day

    def getHoldBarList(self,name) ->[]:
        return self.holdBarMapList.get(name)

    def __crateHoldBars(self,bar:BarData):
        holdBar = HoldBar(code=bar.symbol, start_time=bar.datetime, end_time=bar.datetime)
        """
             真正的盈利开始算是从第一天收盘价作为买入点,这里于
         """
        holdBar.open_price = (bar.open_price + bar.close_price) / 2
        return holdBar

    def __onHoldUpdate(self,holdBar:HoldBar,bar:BarData):
        holdBar.high_price = max(holdBar.high_price, bar.high_price)
        holdBar.low_price = min(holdBar.low_price, bar.low_price)
        holdBar.close_price = bar.close_price
        holdBar.end_time = bar.datetime
        holdBar._days = holdBar._days + 1
        holdBar.bars.append(bar)
        pass

    def printAll(self):

        day_encoder = FloatEncoder([1, 3, 5, 8, 12, 15])
        pct_encoder = FloatEncoder([-8, -3, -1, 1, 3, 5, 8, 15, 22])
        for name,holdbarList in self.holdBarMapList.items():
            barList = []
            day_list = []
            pct_list = []
            myBarOccurDay = {}
            for holdBar in holdbarList:
                a_hold_bar: BarData = holdBar.toBarData()
                barList.append(holdBar.toBarData())
                day_list.append(holdBar._days)
                pct_list.append(100 * (a_hold_bar.close_price - a_hold_bar.open_price) / a_hold_bar.open_price)
                for bar in holdBar.bars:
                    myBarOccurDay[self.__datetimeKey(bar.datetime)] = True
            holdBarSize = len(holdbarList)
            day_list = np.array(day_list)
            pct_list = np.array(pct_list)

            coverity = len(myBarOccurDay) / len(self.barOccurDay)
            print(f"因子【{name}】评测结果: holdbar总数:{holdBarSize},持有天数:%.2f,pct:%.2f,覆盖率:%.2f%%" % (day_list.mean(),pct_list.mean(),coverity * 100))
            print( f"     天数:{day_list.mean()},值分布:{FloatRange.toStr(day_encoder.computeValueDisbustion(day_list), day_encoder)}")
            print( f"     pct:{pct_list.mean()},值分布:{FloatRange.toStr(pct_encoder.computeValueDisbustion(pct_list), pct_encoder)}")

            # if len(barList) > 1:
            #     chart.show(barList, savefig=f'imgs\\{code}.png')

if __name__ == "__main__":
    start = datetime(2015, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    measure = IndicatorMeasure()
    bars, code = souces.nextBars()
    while not bars is None:
        print(f"new session=>code:{code},bar.size = {len(bars)}")
        indicator = Indicator(34)
        latesBars = []
        for bar in bars:
            if not BarUtils.isOpen(bar):
                continue
            indicator.update_bar(bar)
            latesBars.append(bar)
            if indicator.count < 34:
                continue
            m_di = indicator.minus_di(14)
            p_di = indicator.plus_di(14)
            buy_proid = p_di - m_di > 30 and p_di - m_di < 40
            hold_peroid = buy_proid or p_di - m_di > 30 and p_di < 75
            measure.measure("di指标因子_p14",bar,hold_peroid)
        measure.newSession()
        bars, code = souces.nextBars()
    ##打印因子策略结果
    measure.printAll()