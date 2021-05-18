from dataclasses import dataclass
from datetime import datetime

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarManager import BarManager
from earnmi.data.BarStorage import BarV2Storage
from earnmi.data.BarTransform import BarTransformHandle
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.data.tranfrom.BarV2TransformHandle import BarV2TransformHandle
from earnmi.model.bar import BarData, BarV2
from vnpy.trader.constant import Interval


class MA5Handle(BarTransformHandle):
    def __init__(self,driver:BarDriver):
        self.driver = driver
        self.target_symbol = driver.get_symbol_lists()[0]

    def get_name(self):
        return "ma5_transform"

    def get_symbol_lists(self):
        return [self.target_symbol]

    def onTransform(self,manager:BarManager,storage: BarV2Storage,driver_name:str):
        ##清理数据
        storage.clean(driver=driver_name)
        targetDriver = self.driver
        barSource = manager.createBarSoruce(targetDriver)
        bars = barSource.get_bars(self.target_symbol)
        indicator = Indicator();
        barV2_list = []
        for i in range(0,len(bars)):
            ma5 = 0
            indicator.update_bar(bars[i])
            if indicator.count > 5:
                ma5 = indicator.ema(5,array=False)
            barV2 = BarV2.copy(bars[i],driver_name = driver_name)
            barV2.extra.ma5 = ma5
            barV2_list.append(barV2)
        ###保存变换后的数据
        storage.save_bar_data(barV2_list)


app = App()
drvier = SW2Driver()
ma5Handle = MA5Handle(driver=drvier)
barTransform = app.getBarManager().createBarTransform(ma5Handle)
barTransform.transfrom()
sources = barTransform.createBarSource()
for symbol,bars in sources.itemsSequence():
    print(f"symbol:{symbol}, len = {len(bars)}")
    for bar in bars:
        print(f"datetime:{bar.datetime}: ma5 = {bar.extra.ma5}")

# symbol = '801744'
# bars = sources.get_bars(symbol,interval=Interval.DAILY)
# print(f"symbol:{symbol}, len = {len(bars)}")
#
# for bar in bars:
#     print(f"extra:{bar.extra.__dict__}")

# for symbol,bars in sources.itemsSequence():
#     print(f"symbol:{symbol}, len = {len(bars)}")






