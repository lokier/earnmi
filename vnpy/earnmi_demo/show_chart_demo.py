from datetime import datetime, timedelta
from typing import List

from ibapi.common import BarData
from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, BollItem, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from earnmi.data.SWImpl import SWImpl
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from earnmi.data import import_data_from_jqdata


"""
 RSI指标
"""
class IndicatorLine(IndicatorItem):

    def getNames(self) -> List:
        return ["k","d"]


    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        if indicator.count >= 15:
            k, d,j = indicator.kdj(fast_period=9,slow_period=3,array=True)
            values["k"] = k[-1]
            values["d"] = d[-1]
            ##金叉出现
            if (k[-1] >= d[-1] and k[-2] <= d[-2]):
                if not signal.hasBuy:
                    signal.buy = True
            ##死叉出现
            if (k[-1] <= d[-1] and k[-2] >= d[-2]):
                if signal.hasBuy:
                    signal.sell = True

        else:
            values["k"] = 50
            values["d"] = 50
        return values

    def getColor(self, name: str):
        if name == "k":
            return 'r'
        return 'y'

    def isLowerPanel(self) ->bool:
        return True

code = "600196"

start = datetime(2020, 5, 1)
end = datetime.now();
#end = datetime(2020, 8, 17)

#code = '000300'
#801161.XSHG
#market = MarketImpl()
#market.addNotice(code)
#market.setToday(datetime.now())
#bars = market.getHistory().getKbarFrom(code,start)

sw = SWImpl()
codeList = sw.getSW2List()
code = codeList[1]
start = datetime(2020, 5, 1)
bars = sw.getSW2Daily(code,start,end)



print(f"bar.size = {bars.__len__()}")


chart = Chart()

chart.show(bars,IndicatorLine())
#chart.showCompare(bars,"000300")