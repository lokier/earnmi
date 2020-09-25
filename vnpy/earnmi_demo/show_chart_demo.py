from datetime import datetime, timedelta
from typing import List

from ibapi.common import BarData
from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, BollItem, IndicatorItem, Signal, HoldBarMaker
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl


"""
 RSI指标
"""
class IndicatorLine(IndicatorItem):

    maker:HoldBarMaker = HoldBarMaker()

    def getNames(self) -> List:
        return ["a"]


    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        if indicator.count>1:
            obv = indicator.obv(array=False)
            values["a"] = obv
        else:
            values["a"] = 50
        return values

    def getColor(self, name: str):
        if name == "fast":
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


for code in codeList:
    print(f"name = {sw.getSw2Name(code)},len = {len(sw.getSW2Stocks(code))}")

print(f"bar.size = {bars.__len__()}")


chart = Chart()

chart.show(bars,IndicatorLine())
#chart.showCompare(bars,"000300")