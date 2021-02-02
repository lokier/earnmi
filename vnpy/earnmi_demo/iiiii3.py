from dataclasses import dataclass
from datetime import datetime
from functools import cmp_to_key

import numpy as np
import talib

import time
import sched

from earnmi.core.App import App
from earnmi.core.analysis.FloatRange import FloatParser, FloatDistribute
from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver

from earnmi.uitl.BarUtils import BarUtils
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval

app = App()
start = datetime(year=2020,month=1,day=6)
end = datetime(year=2021,month=1,day=6)
drvier2 = ZZ500StockDriver()
bar_source = app.getBarManager().createBarSoruce([drvier2],Interval.DAILY,start,end)
score_list = []
bars,symbol = bar_source.nextBars()
while not bars is None:
    rate_list = []  ##该个股的涨跌幅列表
    pre_bar = None
    for bar in bars:
        if BarUtils.isOpen(bar):
            if not pre_bar is None:
                _rate = (bar.close_price - pre_bar.close_price )* 100  / pre_bar.close_price
                rate_list.append(_rate)
            pre_bar = bar
    fParser = FloatParser(-10,10)  ##设置最大涨跌幅度
    score = fParser.calc_op_score(rate_list,1.6)
    print(f"{symbol}: size = {len(rate_list)},score:{score}")
    score_list.append(score)
    bars, symbol = bar_source.nextBars()
fDist = FloatDistribute(score_list)
fDist.showPipChart(limit_show_count=8)

# score_parser = FloatParser(_score_list)
# score_parser.showBarChart()
#
# best_fParser.showBarChart()



