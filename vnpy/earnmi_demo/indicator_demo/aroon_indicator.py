from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl
from earnmi_demo.indicator_demo.IndicatorItemHelper import IndicatorItemHelper
from vnpy.trader.object import BarData


class AroonItem(IndicatorItemHelper):

    deal_list = []

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
                if  not self.hasBuy():
                    buy_tag = False
                    costs = self.getCostList()
                    if len(costs) >= 2:
                        if costs[-1] > 0.00 and costs[-2] > 0.00:
                            buy_tag = True
                    signal.buy = buy_tag
                    self.buy(bar.close_price)
                    # print(f"{bar.datetime}： 买: price:{bar.close_price * 1.01}")
            else:
                if( self.hasBuy()):
                    signal.sell = True
                    self.sell(bar.close_price)
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

sw = SWImpl()
lists = sw.getSW2List()
bars = sw.getSW2Daily(lists[3],start,end)
print(f"bar.size = {bars.__len__()}")


chart = Chart()
item = AroonItem();
chart.show(bars, item)

##cost = 0
costList = item.getCostList()
ok = 0
size = len(costList)
for c in item.getCostList():
    if c > 0.0:
        ok = ok + 1

print(f"size ={size},ok = {ok}")


