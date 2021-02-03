from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import cmp_to_key

import numpy as np
import talib

import time
import sched

from earnmi.chart.KPattern import KPattern

from earnmi.chart.Chart import Chart
from earnmi.chart.Indicator import Indicator
from earnmi.chart.KPattern2 import KPattern2
from earnmi.core.App import App
from earnmi.core.analysis.FloatRange import FloatParser, FloatDistribute
from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver

from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.constant import Interval

target_pattern_values = [206671, 265649, 213961, 265639, 265720, 206580, 324769, 81283, 265629, 29443, 206590, 206337, 199381, 265619, 259159, 265963, 265376,
442867, 14944, 265710, 258430, 265719, 280300, 206428, 265801, 265467, 81040, 36814, 21991, 251140, 265477, 88330, 88492, 95863, 265497, 265740, 265711,
265487, 88482, 199138, 199300, 265638, 88320, 206347, 88573, 22234, 206681, 258420, 279571, 265730, 273010, 266449, 205942, 265386, 265721, 272281, 265729, 265406,
273020, 192091, 265457, 273000, 251869, 88563, 258187, 103153, 221251, 258440, 73993, 264991, 258349, 265700, 265659, 272919, 272929]

app = App()
start = datetime(year=2018,month=1,day=6)
end = datetime(year=2021,month=1,day=6)
drvier2 = ZZ500StockDriver()
bar_source = app.getBarManager().createBarSoruce([drvier2],Interval.DAILY,start,end)
rate_list_map = defaultdict(list)
bars,symbol = bar_source.nextBars()
while not bars is None:
    print(f"symbol:{symbol}: size = {len(bars)}")
    pre_bar = None
    bar_list = []
    for bar in bars:
        if BarUtils.isOpen(bar):
            pattern_value = -1
            if not pre_bar is None:
                pattern_value = KPattern.encode_2k_by_algo1(bar_list)  ##前2个交易日的k线形态编码
                if not pattern_value is None and target_pattern_values.__contains__(pattern_value):
                    _rate = (bar.close_price - pre_bar.close_price )* 100  / pre_bar.close_price
                    rate_list = rate_list_map[pattern_value]
                    rate_list.append(_rate)
            pre_bar = bar
            bar_list.append(bar)
            # if pattern_value == 88320:
            #      chart = Chart()
            #      size = min(15,len(bar_list))
            #      chart.show(bar_list[-size:])
        else:
            pre_bar = None
            bar_list = []
    bars, symbol = bar_source.nextBars()
@dataclass
class Item():
    count:int
    pattern_value:int
    score:float
    avg_line:float
    # best_ragne:[]


item_list = []
for pattern_value,rate_list in rate_list_map.items():
    fParser = FloatParser(-10,10)  ##设置最大涨跌幅度
    score = fParser.calc_op_score(rate_list,1.6)
    item = Item(count =len(rate_list),
                pattern_value=pattern_value,
                score=score,
                avg_line = fParser.calc_avg_line(rate_list)
                # best_ragne=fParser.find_best_range(rate_list,1.6)
                )
    #print(f"{pattern_value}: size = {len(rate_list)},score:{score}")
    if item.count > 10:
        item_list.append(item)
def _compare_(a,b):
    return abs(a.avg_line) - abs(b.avg_line)
item_list = sorted(item_list,key=cmp_to_key(_compare_),reverse=False)
for item in item_list:
    print(f"{item}")

# score_parser = FloatParser(_score_list)
# score_parser.showBarChart()
#
# best_fParser.showBarChart()



