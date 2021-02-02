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
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.model.bar import LatestBar
from earnmi.model.op import OpOrder
from earnmi.uitl.BarUtils import BarUtils
from earnmi.uitl.jqSdk import jqSdk
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval

app = App()
start = datetime(year=2020,month=1,day=6)
end = datetime(year=2021,month=1,day=6)
drvier2 = ZZ500StockDriver()
bar_source = app.getBarManager().createBarSoruce([drvier2],Interval.DAILY,start,end)
bars,symbol = bar_source.nextBars()

count = 0
best_fParser = None
best_symbol = None
best_result = None
best_score = 0

@dataclass
class ScoreItem:

    score:float  ##得分情况
    score_rate:float ##涨幅情况
    symbol:str

score_list = []

while not bars is None:

    rate_list = []
    pre_bar = None
    first_bar = None
    for bar in bars:
        if BarUtils.isOpen(bar):
            if not pre_bar is None:
                _rate = (bar.close_price - pre_bar.close_price )* 100  / pre_bar.close_price
                rate_list.append(_rate)
            if first_bar is None:
                first_bar = bar
            pre_bar = bar

    fParser = FloatParser(-10,10)
    score = fParser.calc_op_score(rate_list,1.6)
    print(f"{symbol}: size = {len(rate_list)},score:{score}")
    if symbol == '000685':
        print("debug here!")
        print(f"best_range:{fParser.find_best_range(rate_list,delta_value=1.6)}")
    #fParser.showLineChart(rate_list)
    score_item = ScoreItem(score = score,score_rate=(pre_bar.close_price - first_bar.close_price)*100 / first_bar.close_price,symbol=symbol)
    score_list.append(score_item)
    if score > best_score:
        best_score = score
        best_fParser = fParser
        best_symbol = symbol
    # result = fParser.find_best_range(1.5)
    # print(f"{symbol}:{result}")
    # if best_result is None or abs(best_result[0][0] - 0) < abs(result[0][0] - 0):
    #     best_result = result
    #     best_fParser = fParser
    #     best_symbol = symbol

    #count +=1
    if count ==1:
        break
    bars, symbol = bar_source.nextBars()

print(f"BEST:{best_symbol}:{best_score}")  #002709


def _comp_(a,b):
    return a.score - b.score

score_list = sorted(score_list,key=cmp_to_key(_comp_))

_score_list = [ item.score for item in score_list]
_score_rate_list = [ item.score_rate for item in score_list]


fDist = FloatDistribute(_score_list)

r_list = [[item.symbol,item.score,utils.keep_3_float(item.score_rate)] for item in score_list]
print(f"{r_list}")

r1 = talib.CORREL(np.array(_score_list), np.array(_score_rate_list), timeperiod=len(_score_list))
print(f"收益相关性:{r1[-1]}")

fDist.showPipChart(limit_show_count=8)

# score_parser = FloatParser(_score_list)
# score_parser.showBarChart()
#
# best_fParser.showBarChart()
