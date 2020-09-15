from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, Signal, IndicatorItem
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl
from earnmi.uitl.utils import utils
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

sw = SWImpl()
lists = sw.getSW2List()
chart = Chart()

for code in lists:
    bars = sw.getSW2Daily(code, start, end)
    print(f"bar.size = {bars.__len__()}")
    item = AroonItem();
    chart.run(bars, item)

    print(f"holdbars = {len(item.getHoldBars())}")

    barList = []
    for holdBar in item.getHoldBars():
        barList.append(holdBar.toBarData())

    chart.show(barList, savefig=f'imgs\\{code}.png')


#trades = pd.DataFrame(data, index=index, columns=columns)



