from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, BollItem, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from vnpy.trader.object import BarData


class AroonItem(IndicatorItem):

    has_bug = False

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
                if self.has_bug == False:
                    signal.buy = True
                    self.has_bug = True
                    print(f"{bar.datetime}： 买: price:{bar.close_price * 1.01}")
            else:
                if( self.has_bug == True):
                    signal.sell = True
                    self.has_bug = False
                    print(f"{bar.datetime}： 卖: price:{bar.close_price * 0.99}")

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

code = "600196"
start = datetime(2018, 5, 1)
end = datetime(2020, 8, 17)

market = MarketImpl()
market.addNotice(code)
market.setToday(end)


bars = market.getHistory().getKbarFrom(code,start)

print(f"bar.size = {bars.__len__()}")


chart = Chart()
chart.show(bars, AroonItem())
