from datetime import datetime

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Factory import Factory
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.model.CollectData import CollectHandler, CollectData
from earnmi.model.bar import BarData
from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.constant import Interval

''''
构建一个新的bar，周期为perioid，volumn属性为ad_diff
'''
def to_nbar_list(barList:['BarData'] = None,period = 5):
    assert  period > 2
    low,high,open,close,volume = BarUtils.to_np_array(barList)
    ad_diff_list = Factory.ad_diff(close,high,low,volume);
    n_bar_list = []
    symbol = barList[0].symbol
    size = len(barList)
    for i in range(1,size,period):
        print(f"start = {i},end = {i+period}")
        end_index = i + period
        if end_index > size:
            break
        start_index = i
        open = barList[start_index - 1].close_price
        close = barList[end_index - 1].close_price
        high = max(open,barList[start_index].high_price)
        low = min(open,barList[start_index].low_price)
        for j in range(start_index+1,end_index):
            high = max(high,barList[j].high_price)
            low = min(low,barList[j].low_price)
        bar = BarData(symbol=symbol,datetime=barList[start_index].datetime)
        bar.open_price = open
        bar.close_price = close
        bar.high_price = high
        bar.low_price = low
        bar.volume = ad_diff_list[end_index-1] - ad_diff_list[start_index]
        if bar.volume < 1:
            bar.volume = 1
        n_bar_list.append(bar)
    return n_bar_list


drvier1 = StockIndexDriver()
drvier2 = SW2Driver()
app = App()
start = datetime(year=2020,month=1,day=1)
end = datetime(year=2021,month=3,day=20)


bar_source = app.getBarManager().createBarSoruce(drvier2,start,end)
chart = Chart()
for symbol, bars in bar_source.itemsSequence():

    class Item(IndicatorItem):

        def init(self):
            self.names = ['ad_diff', 'ad_diff2']  ##指标名称
            self.colors = ['b', 'g', 'r', 'black']  ##指标颜色

        def getValues(self, indicator: Indicator, bar: BarData, signal: Signal) -> Map:
            values = {}
            values['ad_diff'] = bar.ad_diff
            values['ad_diff2'] = bar.ad_diff2
            return values

    low, high, open, close, volume = BarUtils.to_np_array(bars)
    ad_diff2 = Factory.ad_diff2(close, high, low, volume);
    ad_diff = Factory.ad_diff(close, high, low, volume);
    for i in range(len(bars)):
        bars[i].ad_diff2 = ad_diff2[i]
        bars[i].ad_diff = ad_diff[i]

    #chart.show(bars,Item())

    print(f"{symbol}: size = {len(bars)}")
    n_bar_list = to_nbar_list(bars,5)

    chart.show(n_bar_list)


