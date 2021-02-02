from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import cmp_to_key
from typing import Callable, Sequence

import numpy as np
import talib

import time
import sched

from earnmi.chart.KPattern import KPattern, anaylsisPatternCoverity

from earnmi.chart.Chart import Chart
from earnmi.chart.Indicator import Indicator
from earnmi.chart.KPattern2 import KPattern2
from earnmi.core.App import App
from earnmi.core.analysis.FloatRange import FloatParser, FloatDistribute
from earnmi.data.BarSoruce import BarSource
from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver
from earnmi.model.bar import BarData

from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.constant import Interval



app = App()
start = datetime(year=2018,month=1,day=6)
end = datetime(year=2021,month=1,day=6)
drvier2 = ZZ500StockDriver()
bar_source = app.getBarManager().createBarSoruce([drvier2], Interval.DAILY, start, end)

def calc_pattern_value(bars:Sequence['BarData'])->int:
    return KPattern.encode_2k_by_algo1(bars)

anaylsisPatternCoverity(bar_source,calc_pattern_value,min_coverity_rate=0.001)