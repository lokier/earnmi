from datetime import datetime, timedelta
from typing import List

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, Signal, IndicatorItem
from earnmi.chart.Factory import Factory
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange2
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.BarUtils import BarUtils
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData
import numpy as np

class AroonItem(IndicatorItem):

    def __init__(self):
        super().__init__(True)
        self.hold_day = 0

    def getNames(self) -> List:
        return ["arron_up_25","arron_down_25"]

    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        count = 34
        if indicator.count >= count:
            m_di = indicator.minus_di(14)
            p_di = indicator.plus_di(14)
            aroon_down,aroon_up = indicator.aroon(24,False)
           # dif,dea, macd = indicator.macd(array=False)
            #aroon_down, aroon_up = Factory.obv_wave(33, indicator.close, indicator.high, indicator.low,indicator.volume)
            values["arron_up_25"] = aroon_up
            values["arron_down_25"] = aroon_down
            #need_hold = aroon_up > 50  and  aroon_up > aroon_down
           # need_hold = aroon_up > 16.67 and dea > 0 and p_di > m_di
            #need_hold = aroon_up > 16.67  and p_di > m_di
            #buy_proid = p_di  - m_di > 30 and p_di - m_di < 40
            hold =  p_di  - m_di > 30 and p_di < 75
            #need_hold =    and p_di < 75

            if hold and not signal.hasBuy:
                signal.buy = True
            elif not hold and signal.hasBuy:
                signal.sell = True


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

# sw = SWImpl()
# lists = sw.getSW2List()
chart = Chart()

day_encoder = FloatEncoder([1,3,5,8,12,15])
pct_encoder = FloatEncoder([-8,-3,-1,1,3,5,8,15,22])

day_list = []
pct_list = []
start = datetime(2015, 10, 1)
end = datetime(2020, 9, 30)
souces = ZZ500DataSource(start, end)
bars,code = souces.nextBars()
holdCount = 0
while not bars is None:
    ##bars = sw.getSW2Daily(code, start, end)
    bars = BarUtils.filterNoOpen(bars);
    item = AroonItem();
    chart.run(bars, item)
    print(f"code:{code},bar.size = {len(bars)},holdbars = {len(item.getHoldBars())}")
    barList = []
    close_price = None
    for holdBar in item.getHoldBars():
        holdCount+=1
        a_hold_bar:BarData = holdBar.toBarData()
        barList.append(holdBar.toBarData())
        day_list.append(holdBar._days)
        pct_list.append(100 *(a_hold_bar.close_price -a_hold_bar.open_price) / a_hold_bar.open_price)
    if len(barList) >1:
        chart.show(barList, savefig=f'imgs\\{code}.png')
    bars,code = souces.nextBars()

day_list = np.array(day_list)
pct_list = np.array(pct_list)
print(f"holdCount:{holdCount}")
print(f"     天数:{day_list.mean()},值分布:{FloatRange2.toStr(day_encoder.computeValueDisbustion(day_list), day_encoder)}")
print(f"     pct:{pct_list.mean()},值分布:{FloatRange2.toStr(pct_encoder.computeValueDisbustion(pct_list), pct_encoder)}")




#trades = pd.DataFrame(data, index=index, columns=columns)



