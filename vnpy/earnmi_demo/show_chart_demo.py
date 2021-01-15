from datetime import datetime, timedelta
from typing import List

from ibapi.common import BarData
from statsmodels.multivariate.factor import Factor
from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, BollItem, IndicatorItem, Signal, HoldBarMaker
from earnmi.chart.Factory import Factory
from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import Market2Impl
from earnmi.data.SWImpl import SWImpl
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.BarUtils import BarUtils

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

"""
 RSI指标
"""
class kdj(IndicatorItem):

    maker:HoldBarMaker = HoldBarMaker()
    def __init__(self):
        super().__init__(False)

    def getNames(self) -> List:
        return [
            "osi1",
               # "osi2",
                #"osi3",
                #"osi4"
                ];
        #return ["osi3"];

    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        if indicator.count>35 and BarUtils.isOpen(bar):
            values["osi1"] = indicator.obv2();
            values["osi2"] =  indicator.ad2(15);
            values["osi3"]  = 0
            #values["osi1"] = 0
            values["osi3"] = Factory.pvb(indicator.close,indicator.high,indicator.low,indicator.volume,12);
            values["osi4"] =indicator.ad2(9);
        else:
            values["osi1"] = 0
            values["osi2"] = 0
            values["osi3"] = 0
            values["osi4"] =0
        return values

    def getColor(self, name: str):
        if name == "osi1":
            return 'r'
        elif name == 'osi2':
            return 'b'
        elif name == 'osi3':
            return 'black'
        return 'y'

    def isLowerPanel(self) ->bool:
        return True




code = "600196"

start = datetime(2018, 6, 8)
end =datetime(2018, 10, 1)
#end = datetime(2020, 8, 17)

code = '603377'
market = Market2Impl()
market.addNotice(code)
market.setToday(end)
bars = market.getHistory().getKbarFrom(code,start)





print(f"bar.size = {bars.__len__()}")


chart = Chart()

chart.show(bars,kdj(),savefig="dsjf1.jpg")
#chart.showCompare(bars,"000300")