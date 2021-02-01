from dataclasses import dataclass
from datetime import datetime

import numpy as np
import talib

import time
import sched

from earnmi.core.App import App
from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.model.bar import LatestBar
from earnmi.model.op import OpOrder
from earnmi.uitl.jqSdk import jqSdk
from vnpy.trader.constant import Interval

app = App()
start = datetime(year=2018,month=1,day=6)
end = datetime(year=2021,month=1,day=6)
drvier2 = ZZ500StockDriver()
bar_source = app.getBarManager().createBarSoruce([drvier2],Interval.DAILY,start,end)
bars,symbol = bar_source.nextBars()
while not bars is None:
    print(f"{symbol}: size = {len(bars)}")
    bars, symbol = bar_source.nextBars()

