from dataclasses import dataclass
from datetime import datetime
from functools import cmp_to_key

from earnmi.chart.Chart import HoldBar
from earnmi.chart.Factory import Factory
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange
from earnmi.chart.Indicator import Indicator
from earnmi.model.BarDataSource import ZZ500DataSource, BarDataSource
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
        self.runing_strategy = None

    def startSession(self):
        pass

    def endSession(self):
        self.holdingBarMap.clear()
    """
    是否持有。
    """
    def measure(self, name: str, bar: BarData, isHold: bool,putIntoWhileNotHold:bool = True):
        """
        putIntoWhileNotHold：不包含的那一天，是否放在holdbar里面。
        """
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
                if putIntoWhileNotHold:
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
        holdBar.open_price = self.runing_strategy.getHoldBarOpenPrice(bar)
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
        pct_encoder = FloatEncoder([ -1, 0.5, 1.5,3, 5, 8, 15, 22])
        @dataclass
        class DataItem:
            name:str
            holdbarSize:int
            coverity:float
            pct:float
            day_list:[] =None
            pct_list:[] = None  ##涨幅
            pct_sell_list:[] = None  ##卖方价

        dataItemList = []
        for name,holdbarList in self.holdBarMapList.items():
            barList = []
            day_list = []
            pct_list = []
            pct_sell_list = []
            myBarOccurDay = {}
            for holdBar in holdbarList:
                a_hold_bar: BarData = holdBar.toBarData()
                barList.append(holdBar.toBarData())
                day_list.append(holdBar._days)
                pct_list.append(100 * (a_hold_bar.close_price - a_hold_bar.open_price) / a_hold_bar.open_price)
                pct_sell_list.append(100 * ((a_hold_bar.close_price + a_hold_bar.high_price)/2 - a_hold_bar.open_price) / a_hold_bar.open_price)

                for bar in holdBar.bars:
                    myBarOccurDay[self.__datetimeKey(bar.datetime)] = True
            holdBarSize = len(holdbarList)
            day_list = np.array(day_list)
            pct_list = np.array(pct_list)
            pct_sell_list = np.array(pct_sell_list)
            coverity = len(myBarOccurDay) / len(self.barOccurDay)
            dataItem= DataItem(holdbarSize=holdBarSize,name=name,coverity=coverity,pct=pct_list.mean())
            dataItem.pct_list = pct_list
            dataItem.day_list = day_list
            dataItem.pct_sell_list = pct_sell_list
            dataItemList.append(dataItem)
        ##findBese
        def _item_cmp(o1,o2):
            return o1.pct - o2.pct
        dataItemList = sorted(dataItemList,key=cmp_to_key(_item_cmp),reverse=True)

        ####输入markdown类的日志
        print(f"输出markdown格式内容:");
        print(f"名称| holdbar总数 | 持有天数 | pct |pct_sell| 覆盖率")
        print(f":--|:--:|:--|:--|:--|:--:")


        for dataItem in dataItemList:
            name = dataItem.name
            holdBarSize = dataItem.holdbarSize
            coverity = dataItem.coverity
            day_list = dataItem.day_list
            pct_list = dataItem.pct_list
            pct_sell_list = dataItem.pct_sell_list
            #print(f"因子【{name}】评测结果: holdbar总数:{holdBarSize},持有天数:%.2f,pct:%.2f,覆盖率:%.2f%%" % (day_list.mean(),pct_list.mean(),coverity * 100))
            #print( f"     天数:{day_list.mean()},值分布:{FloatRange.toStr(day_encoder.computeValueDisbustion(day_list), day_encoder)}")

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
                #print( f"           天数[{_min},{_max})的pct均值为：{_pct_list.mean()}")
            #print( f"     pct:{pct_list.mean()},值分布:{FloatRange.toStr(pct_encoder.computeValueDisbustion(pct_list), pct_encoder)}")
            #print( f"     pct_sell:{pct_sell_list.mean()},值分布:{FloatRange.toStr(pct_encoder.computeValueDisbustion(pct_sell_list), pct_encoder)}")
            day_cell_desc = self.to_markdown_Disbustion(day_list,day_encoder)
            pct_cell_desc = self.to_markdown_Disbustion(pct_list,pct_encoder)
            pct_sell_cell_desc = self.to_markdown_Disbustion(pct_sell_list,pct_encoder)
            print(f"{name}| {holdBarSize} | {day_cell_desc} | {pct_cell_desc} |{pct_sell_cell_desc}| {f'%.2f%%' % (coverity * 100)}")

    def to_markdown_Disbustion(self,pct_list, pct_encoder):

        desc = "%.2f" % pct_list.mean()
        ragneList = pct_encoder.computeValueDisbustion(pct_list)
        other_probal = None
        for i in range(0, len(ragneList)):
            r: FloatRange = ragneList[i]
            if r.probal < 0.01:
                ##小于1%，归为other
                if other_probal is None:
                    other_probal = r.probal
                else:
                    other_probal += r.probal
                continue
            _min, _max = pct_encoder.parseEncode(r.encode)
            if _min is None:
                _min = "min"
            else:
                _min = f"%.1f" % _min
            if _max is None:
                _max = "max"
            else:
                _max = f"%.2f" % _max
            desc += f" <br>[{_min}:{_max})=%.2f%%," % (100 * r.probal)

        if not other_probal is None:
            desc += f" <br>其它=%.2f%%," % (100 * other_probal)

        return desc


    def run(self, souces:BarDataSource, startegy):
        bars, code = souces.nextBars()
        self.runing_strategy = startegy
        while not bars is None:
            print(f"new session=>code:{code},bar.size = {len(bars)}")
            measure.startSession()
            code = bars[-1].symbol
            startegy.onMeasureStart(code)
            for bar in bars:
                if not BarUtils.isOpen(bar):
                    continue
                startegy.onMeasureBar(measure, bar)
            startegy.onMeasureEnd(code)
            measure.endSession()
            bars, code = souces.nextBars()
        ##打印因子策略结果
        self.runing_strategy = None

class MeasureStartegy:


    def onMeasureStart(self,code:str):
        self.indicator = Indicator(42)

    def onMeasureBar(self,measure:IndicatorMeasure,bar:BarData):
        pass
    """
       真正的盈利开始算是从第一天收盘价作为买入点,这里于
    """
    def getHoldBarOpenPrice(self, bar: BarData):
        pass

    def onMeasureEnd(self,code:str):
        pass




if __name__ == "__main__":


    class SampleMeasureStartegy(MeasureStartegy):
        def onMeasureStart(self, code: str):
            self.indicator = Indicator(42)

        def onMeasureBar(self, measure: IndicatorMeasure, bar: BarData):
            indicator = self.indicator
            indicator.update_bar(bar)
            if not indicator.inited:
                return

            paramsMap = {
                'day': [1,2,3],            }
            paramList = utils.expandParamsMap(paramsMap)
            for param in paramList:
                day = param['day']
                k, d, j = indicator.kdj(fast_period=9, slow_period=3, array=True)
                dif, dea, macd = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True)
                holdDay = 0
                for i in range(-1, -8, -1):
                    isHold = k[i] >= d[i] and dif[i] > 0 and dif[i] > dea[i]
                    if not isHold:
                        break
                    holdDay += 1
                hold = holdDay >= day
                measure.measure(f"kdj/mackd双金叉指标<br>day={day}", bar, hold, putIntoWhileNotHold=False)

        def getHoldBarOpenPrice(self, bar: BarData):
            # 第一天的收盘价作为holdbar的开始价格。
            return  bar.close_price



    start = datetime(2017, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    measure = IndicatorMeasure()
    startegy = SampleMeasureStartegy()
    measure.run(souces,startegy)

    measure.printBest()
    """
    因子【di指标因子:{'period': 14, 'min_dist': 15, 'x': 2, 'duration': 4}】评测结果: holdbar总数:5203,持有天数:2.09,pct:1.74,覆盖率:97.68%
     天数:2.0876417451470304,值分布:[[min:1.00)=0.00%,[1.00:3.00)=72.29%,[3.00:5.00)=21.56%,[5.00:8.00)=6.13%,[8.00:12.00)=0.02%,[12.00:15.00)=0.00%,[15.00:max)=0.00%,]
           天数[1,3)的pct均值为：0.3766889008876466
           天数[3,5)的pct均值为：4.460444868507723
           天数[5,8)的pct均值为：8.187512883858655
           天数[8,12)的pct均值为：7.994340290060141
     pct:1.737681539293691,值分布:[[min:-1.00)=14.18%,[-1.00:0.50)=35.27%,[0.50:1.50)=15.39%,[1.50:3.00)=13.32%,[3.00:5.00)=9.01%,[5.00:8.00)=6.07%,[8.00:15.00)=4.98%,[15.00:22.00)=1.04%,[22.00:max)=0.73%,]
     pct_sell:2.9412162923268568,值分布:[[min:-1.00)=0.62%,[-1.00:0.50)=21.35%,[0.50:1.50)=26.89%,[1.50:3.00)=21.01%,[3.00:5.00)=13.05%,[5.00:8.00)=8.38%,[8.00:15.00)=6.52%,[15.00:22.00)=1.36%,[22.00:max)=0.83%,]

    """