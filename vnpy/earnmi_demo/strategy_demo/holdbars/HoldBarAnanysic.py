from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, Signal, IndicatorItem, HoldBar
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl
from earnmi.uitl.utils import utils
from earnmi_demo.strategy_demo.holdbars.HoldBarUtils import HoldBarData, HoldBarUtils
from vnpy.trader.object import BarData

class arron(IndicatorItem):
    def getNames(self) -> List:
        return ["arron_up_25","arron_down_25"]
    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        count = 15
        if indicator.count >= count:
            aroon_down,aroon_up = indicator.aroon(count,True)
            values["arron_up_25"] = aroon_up[-1]
            values["arron_down_25"] = aroon_down[-1]
            need_hold = aroon_up[-1] > 50  and  aroon_up[-1] > aroon_down[-1]
            if need_hold:
                if  not signal.hasBuy:
                    signal.buy = True
                    # print(f"{bar.datetime}： 买: price:{bar.close_price * 1.01}")
            else:
                if( signal.hasBuy):
                    signal.sell = True
                    #print(f"{bar.datetime}： 卖: price:{bar.close_price * 0.99}")

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


class macd(IndicatorItem):
    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        count = 30
        if indicator.count >= count:
            dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True);
            ##金叉出现
            if (macd_bar[-1] >= 0 and macd_bar[-2] <= 0):
                if not signal.hasBuy:
                    signal.buy = True

                ##死叉出现
            if (macd_bar[-1] <= 0 and macd_bar[-2] >= 0):
                if signal.hasBuy:
                    signal.sell = True
        return values

class kdj(IndicatorItem):

    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        count = 30
        if indicator.count >= count:
            k, d, j = indicator.kdj(fast_period=9, slow_period=3, array=True)
            ##金叉出现
            if (k[-1] >= d[-1] and k[-2] <= d[-2]):
                if not signal.hasBuy:
                    signal.buy = True
            ##死叉出现
            if (k[-1] <= d[-1] and k[-2] >= d[-2]):
                if signal.hasBuy:
                    signal.sell = True

        return values




start = datetime(2014, 5, 1)
end = datetime(2020, 8, 17)
# code = "600196"
#
#
# market = MarketImpl()
# market.addNotice(code)
# market.setToday(end)
#
#
# bars = market.getHistory().getKbarFrom(code,start)
import numpy as np
"""
  计算HoldBar的指标
"""



def computeHoldBarIndictor(indictor:IndicatorItem)->HoldBarData:
    sw = SWImpl()
    lists = sw.getSW2List()
    chart = Chart()
    total_cost_pcts = []#收益
    avg_eran_cost_pcts = []#每个盈利holdbard的平均盈利

    total_days = []
    total_eran_days = []
    total_holdbars = []
    total_holdbars_earn = []
    max_cost_pcts =[]   #最大收益
    min_cost_pcts = []

    for code in lists:

        if len(sw.getSW2Stocks(code)) < 10:
            continue

        bars = sw.getSW2Daily(code, start, end)
        #print(f"bar.size = {bars.__len__()}")
        chart.run(bars, indictor)
        holdbarList = indictor.getHoldBars()
        data = HoldBarUtils.computeHoldBarIndictor(holdbarList);

        total_cost_pcts.append(data.total_cost_pct)
        max_cost_pcts.append(data.max_cost_pct)
        min_cost_pcts.append(data.min_cost_pct)
        total_days.append(data.total_day)
        total_holdbars.append(data.total_holdbar)
        total_holdbars_earn.append(data.total_holdbar_earn)
        avg_eran_cost_pcts.append(data.avg_eran_cost_pct)
        total_eran_days.append(data.total_earn_day)


    ret = HoldBarData()

    total_cost_pcts = np.array(total_cost_pcts)
    total_days = np.array(total_days)
    max_cost_pcts = np.array(max_cost_pcts)
    min_cost_pcts = np.array(min_cost_pcts)
    total_holdbars = np.array(total_holdbars)
    total_holdbars_earn = np.array(total_holdbars_earn)
    avg_eran_cost_pcts = np.array(avg_eran_cost_pcts)
    total_eran_days = np.array(total_eran_days)



    ret.total_min_cost_pct = total_cost_pcts.min()
    ret.total_max_cost_pct = total_cost_pcts.max()
    ret.total_cost_pct = total_cost_pcts.mean()
    ret.total_cost_pct_std = np.std(total_cost_pcts)
    ret.total_day = total_days.mean()
    ret.max_cost_pct = max_cost_pcts.mean()
    ret.min_cost_pct = min_cost_pcts.mean()
    ret.total_holdbar = total_holdbars.mean()
    ret.total_holdbar_earn = total_holdbars_earn.mean()
    ret.avg_eran_cost_pct = avg_eran_cost_pcts.mean()
    ret.total_earn_day = total_eran_days.mean()

    return ret


class Custom(IndicatorItem):
    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        count = 30
        fast_rsi = indicator.rsi(n=3, array=True)
        slow_rsi = indicator.rsi(n=9, array=True)
        ##金叉出现
        if (fast_rsi[-1] >= slow_rsi[-1] and fast_rsi[-2] <= slow_rsi[-2]):
            if not signal.hasBuy:
                signal.buy = True
        ##死叉出现
        if (fast_rsi[-1] <= slow_rsi[-1] and fast_rsi[-2] >= slow_rsi[-2]):
            if signal.hasBuy:
                signal.sell = True
        return values

if __name__ == "__main__":
    item = macd()
    data =  computeHoldBarIndictor(item)
    print("total_pct=%.2f%%(max=%.2f%%,min=%.2f%%),"
           "std=%.2f,"
          "holdbars=%.2f,"
          "holdbars_earn=%.2f,"
          "avg_eran_pct=%.2f%%,"
          'total_earn_day=%.2f,'
          "max_pct=%.2f%%,"
          "min_pct=%.2f%%,"
          "day=%.2f"
          %
          (data.total_cost_pct * 100,data.total_max_cost_pct*100,data.total_min_cost_pct*100,
           data.total_cost_pct_std,data.total_holdbar,data.total_holdbar_earn,
           data.avg_eran_cost_pct*100,data.total_earn_day,
           data.max_cost_pct*100,data.min_cost_pct*100 ,data.total_day)
          )