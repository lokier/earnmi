from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, Signal, IndicatorItem
from earnmi.chart.Factory import Factory
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData
import numpy as np

class AroonItem(IndicatorItem):


    def getNames(self) -> List:
        return ["arron_up_25","arron_down_25"]

    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        count = 34
        if indicator.count >= count:
            aroon_down,aroon_up = indicator.aroon(count,False)
            #aroon_down, aroon_up = Factory.obv_wave(33, indicator.close, indicator.high, indicator.low,indicator.volume)
            values["arron_up_25"] = aroon_up
            values["arron_down_25"] = aroon_down
            need_hold = aroon_up > 50  and  aroon_up > aroon_down
            #need_hold = aroon_up > 16.67
            if need_hold:
                if  not signal.hasBuy:
                    signal.buy = True
                    # print(f"{bar.datetime}： 买: price:{bar.close_price * 1.01}")
            else:
                if( signal.hasBuy):
                    signal.sell = True
                    #print(f"{bar.datetime}： 卖: price:{bar.close_price * 0.99}")

        else:
            values["arron_up_25"] = 10
            values["arron_down_25"] = 10


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

day_encoder = FloatEncoder([1,3,5,8,12,15])
pct_encoder = FloatEncoder([-8,-3,-1,1,3,5,8,15,22])

day_list = []
pct_list = []
for code in lists:
    bars = sw.getSW2Daily(code, start, end)
    item = AroonItem();
    chart.run(bars, item)

    print(f"code:{code},bar.size = {len(bars)},holdbars = {len(item.getHoldBars())}")

    barList = []
    close_price = None
    for holdBar in item.getHoldBars():
        a_hold_bar:BarData = holdBar.toBarData()
        barList.append(holdBar.toBarData())
        day_list.append(holdBar._days)
        pct_list.append(100 *(a_hold_bar.close_price -a_hold_bar.open_price) / a_hold_bar.open_price)
    chart.show(barList, savefig=f'imgs\\{code}.png')

day_list = np.array(day_list)
pct_list = np.array(pct_list)
print(f"     天数:{day_list.mean()},值分布:{FloatRange.toStr(day_encoder.computeValueDisbustion(day_list), day_encoder)}" )
print(f"     pct:{pct_list.mean()},值分布:{FloatRange.toStr(pct_encoder.computeValueDisbustion(pct_list), pct_encoder)}")




#trades = pd.DataFrame(data, index=index, columns=columns)



