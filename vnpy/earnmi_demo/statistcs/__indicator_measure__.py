from dataclasses import dataclass
from datetime import datetime
from functools import cmp_to_key

from earnmi.chart.Chart import HoldBar
from earnmi.chart.Factory import Factory
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange
from earnmi.chart.Indicator import Indicator
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.BarUtils import BarUtils
from earnmi.uitl.utils import utils
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

    def startSession(self):
        pass

    def endSession(self):
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

    def printBest(self):

        day_encoder = FloatEncoder([1, 3, 5, 8, 12, 15])
        pct_encoder = FloatEncoder([-8, -3, -1, 1, 3, 5, 8, 15, 22])
        @dataclass
        class DataItem:
            name:str
            holdbarSize:int
            coverity:float
            pct:float
            day_list:[] =None
            pct_list:[] = None

        dataItemList = []
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
            dataItem= DataItem(holdbarSize=holdBarSize,name=name,coverity=coverity,pct=pct_list.mean())
            dataItem.pct_list = pct_list
            dataItem.day_list = day_list
            dataItemList.append(dataItem)
        ##findBese
        def _item_cmp(o1,o2):
            return o1.pct - o2.pct
        dataItemList = sorted(dataItemList,key=cmp_to_key(_item_cmp),reverse=True)
        for dataItem in dataItemList:
            name = dataItem.name
            holdBarSize = dataItem.holdbarSize
            coverity = dataItem.coverity
            day_list = dataItem.day_list
            pct_list = dataItem.pct_list
            print(f"因子【{name}】评测结果: holdbar总数:{holdBarSize},持有天数:%.2f,pct:%.2f,覆盖率:%.2f%%" % (day_list.mean(),pct_list.mean(),coverity * 100))
            print( f"     天数:{day_list.mean()},值分布:{FloatRange.toStr(day_encoder.computeValueDisbustion(day_list), day_encoder)}")

            ##计算每天分布的对应pct值。
            day_pct_list= np.full(day_encoder.mask(),None)
            day_list_count = len(day_list)
            for __i in range(0,day_list_count):
                day = day_list[__i]
                if  day_pct_list[day_encoder.encode(day)]  is None:
                    day_pct_list[day_encoder.encode(day)] = []
                day_pct_list[day_encoder.encode(day)].append(pct_list[__i])
            for encode in range(0,day_encoder.mask()):
                if day_pct_list[encode] is None or len(day_pct_list[encode]) == 0:
                    continue
                _pct_list = np.array(day_pct_list[encode])
                _min,_max = day_encoder.parseEncode(encode)
                print( f"           天数[{_min},{_max})的pct均值为：{_pct_list.mean()}")

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
        measure.startSession()
        indicator = Indicator()
        latesBars = []
        for bar in bars:
            if not BarUtils.isOpen(bar):
                continue
            indicator.update_bar(bar)
            latesBars.append(bar)
            if not indicator.inited:
                continue

            paramsMap = {
                "period":[14],
                'min_dist': [30],
                #'max_dist': [ 70],
                #'min_p_id': [4,7,10,13,15,50],
            }

            paramList = utils.expandParamsMap(paramsMap)
            for param in paramList:
                period = param['period']
                min_dist = param['min_dist']
                #max_dist = param['max_dist']
                p_di = indicator.plus_di(period)
                m_di = indicator.minus_di(period)
                dist = p_di - m_di
                hold =  dist >= min_dist #and  p_di >= param['min_p_id']

                # ema30 = indicator.ema(30)
                # ema20 = indicator.ema(20)
                # ema10 = indicator.ema(10)

                measure.measure(f"di指标因子:{param}",bar,hold)

        measure.endSession()
        bars, code = souces.nextBars()
    ##打印因子策略结果
    measure.printBest()