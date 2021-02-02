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
    indicator = Indicator()
    bar_list = []
    for bar in bars:
        if BarUtils.isOpen(bar):
            if not pre_bar is None:
                pattern_value = KPattern.encode_2k_by_algo1(bar_list)  ##前2个交易日的k线形态编码
                bar_list.append(bar)
                if pattern_value == 265749:
                    chart = Chart()
                    size = min(15,len(bar_list))
                    chart.show(bar_list[-size:])
                if not pattern_value is None:
                    _rate = (bar.close_price - pre_bar.close_price )* 100  / pre_bar.close_price
                    rate_list = rate_list_map[pattern_value]
                    rate_list.append(_rate)
            indicator.update_bar(bar)
            pre_bar = bar
    bars, symbol = bar_source.nextBars()
@dataclass
class Item():
    count:int
    pattern_value:int
    score:float

item_list = []
for pattern_value,rate_list in rate_list_map.items():
    fParser = FloatParser(-10,10)  ##设置最大涨跌幅度
    score = fParser.calc_op_score(rate_list,1.6)
    item = Item(count =len(rate_list),pattern_value=pattern_value,score=score)
    print(f"{pattern_value}: size = {len(rate_list)},score:{score}")
    if item.count > 10:
        item_list.append(item)
def _compare_(a,b):
    return a.score - b.score
item_list = sorted(item_list,key=cmp_to_key(_compare_),reverse=False)
for item in item_list:
    print(f"{item}")

# score_parser = FloatParser(_score_list)
# score_parser.showBarChart()
#
# best_fParser.showBarChart()



