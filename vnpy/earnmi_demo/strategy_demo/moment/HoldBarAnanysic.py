from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, Signal, IndicatorItem
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl
from vnpy.trader.object import BarData

class AroonItem(IndicatorItem):


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
@dataclass
class HoldBarIndictor:
    total_cost_pct:float = 0.0 ##总共收益
    total_cost_pct_std:float = 0.0 ##标准差
    total_day:int = 0 ##总天数
    total_eran_day:int = 0

    max_cost_pct:float =0.0 ##当中最大收益
    min_cost_pct:float =0.0 ##当中最小收益


def computeHoldBarIndictor(indictor:IndicatorItem)->HoldBarIndictor:
    sw = SWImpl()
    lists = sw.getSW2List()
    chart = Chart()
    total_cost_pcts = []#收益
    total_days = []
    total_earn_days = []
    max_cost_pcts =[]   #最大收益
    min_cost_pcts = []

    for code in lists:
        bars = sw.getSW2Daily(code, start, end)
        #print(f"bar.size = {bars.__len__()}")
        chart.run(bars, indictor)
        holdbarList = indictor.getHoldBars()

        barList = []
        close_price = None
        max_cost_pct = 0.0
        min_cost_pct = 0.0
        total_day = 0
        total_earn_day = 0
        for holdBar in holdbarList:
            bar:BarData = None
            if close_price is None:
                bar = holdBar.toBarData()
            else:
                bar = holdBar.toBarData(new_open_price=close_price)
            barList.append(bar)
            close_price = bar.close_price
            total_day = total_day + holdBar.getDays()
            pct = holdBar.getCostPct()

            if pct > 0.00001:
                total_earn_day = total_earn_day + holdBar.getDays()

            if pct > max_cost_pct:
                max_cost_pct = pct
            if pct < min_cost_pct:
                min_cost_pct = pct

        total_cost_pct = (holdbarList[-1].close_price - holdbarList[0].open_price) / holdbarList[0].open_price
        total_cost_pcts.append(total_cost_pct)
        max_cost_pcts.append(max_cost_pct)
        min_cost_pcts.append(min_cost_pct)
        total_days.append(total_day)
        total_earn_days.append(total_earn_day)


    ret = HoldBarIndictor()

    total_cost_pcts = np.array(total_cost_pcts)
    total_days = np.array(total_days)
    max_cost_pcts = np.array(max_cost_pcts)
    min_cost_pcts = np.array(min_cost_pcts)
    total_earn_days = np.array(total_earn_days)

    ret.total_cost_pct = total_cost_pcts.mean()
    ret.total_cost_pct_std = np.std(total_cost_pcts)
    ret.total_day = total_days.mean()
    ret.max_cost_pct = max_cost_pcts.mean()
    ret.min_cost_pct = min_cost_pcts.mean()
    ret.total_eran_day = total_earn_days.mean()

    return ret



if __name__ == "__main__":
    item = AroonItem()
    data =  computeHoldBarIndictor(item)
    print(f"total_pct={data.total_cost_pct},day={data.total_eran_day}/{data.total_day},std = {data.total_cost_pct_std},max_pct={data.max_cost_pct},min_pct={data.min_cost_pct}")