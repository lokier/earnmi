from dataclasses import dataclass
from datetime import datetime

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarManager import BarManager
from earnmi.data.BarStorage import BarV2Storage
from earnmi.data.BarTransform import BarTransformHandle, BarTransformStorage
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.data.tranfrom.BarV2TransformHandle import BarV2TransformHandle
from earnmi.data.tranfrom.RankTransformHandle import RankTransformHandle
from earnmi.model.bar import BarData, BarV2
from vnpy.trader.constant import Interval

app = App()
drvier = SW2Driver()
ma5Handle = RankTransformHandle(driver=drvier)
barTransform = app.getBarManager().createBarTransform(ma5Handle)
barTransform.transform()
sources = barTransform.createBarSource()
# for symbol,bars in sources.itemsSequence():
#     print(f"symbol:{symbol}, len = {len(bars)}")
#
#     bar = bars[0]
#     print(f"    datetime:{bar.datetime}: extra = {bar.extra.__dict__}")

# symbol = '801744'
# bars = sources.get_bars(symbol,interval=Interval.DAILY)
# print(f"symbol:{symbol}, len = {len(bars)}")
#
# for bar in bars:
#     print(f"extra:{bar.extra.__dict__}")

# for symbol,bars in sources.itemsSequence():
#     print(f"symbol:{symbol}, len = {len(bars)}")






