from dataclasses import dataclass
from datetime import datetime

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.data.tranfrom.BarV2TransformHandle import BarV2TransformHandle
from earnmi.model.bar import BarData
from vnpy.trader.constant import Interval

app = App()

drvier = SW2Driver()
transfromHandle = BarV2TransformHandle(driver=drvier)

barTransform = app.getBarManager().createBarTransform(transfromHandle)

#barTransform.transfrom()

sources = barTransform.createBarSource()

for symbol,bars in sources.itemsSequence():
    print(f"symbol:{symbol}, len = {len(bars)}")


# symbol = '801744'
# bars = sources.get_bars(symbol,interval=Interval.DAILY)
# print(f"symbol:{symbol}, len = {len(bars)}")
#
# for bar in bars:
#     print(f"extra:{bar.extra.__dict__}")

# for symbol,bars in sources.itemsSequence():
#     print(f"symbol:{symbol}, len = {len(bars)}")






