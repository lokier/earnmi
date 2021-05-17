from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import cmp_to_key
from typing import Callable, Sequence, Union
from earnmi.chart.ChartUtis import ChartUtils
from earnmi.chart.KPattern import KPattern, anaylsisPatternCoverity
from earnmi.chart.Chart import Chart
from earnmi.chart.Indicator import Indicator
from earnmi.chart.KPattern2 import KPattern2
from earnmi.core.App import App
from earnmi.core.analysis.FloatRange import FloatParser, FloatDistribute
from earnmi.data.BarSoruce import BarSource
from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver
from earnmi.model.CollectData import CollectHandler, CollectData
from earnmi.model.bar import BarData

from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.constant import Interval
import numpy,pandas

class Pattern_2k_by_algo1_handler(CollectHandler):
    def __init__(self):
        self.pattern_values = [206671, 265649, 213961, 265639, 265720, 206580, 324769, 81283, 265629, 29443, 206590,
                                 206337, 199381, 265619, 259159, 265963, 265376,
                                 442867, 14944, 265710, 258430, 265719, 280300, 206428, 265801, 265467, 81040, 36814,
                                 21991, 251140, 265477, 88330, 88492, 95863, 265497, 265740, 265711,
                                 265487, 88482, 199138, 199300, 265638, 88320, 206347, 88573, 22234, 206681, 258420,
                                 279571, 265730, 273010, 266449, 205942, 265386, 265721, 272281, 265729, 265406,
                                 273020, 192091, 265457, 273000, 251869, 88563, 258187, 103153, 221251, 258440, 73993,
                                 264991, 258349, 265700, 265659, 272919, 272929]

    def onTraceStart(self, symbol: str):
        self.bar_list = []
        print(f"onTraceStart:{symbol}")
        pass

    # def onCollected(self, data: CollectData):
    #     if data.isFinished() and data.dimen_value == 265801:
    #         ChartUtils.show_collect_data(data)

    def onTraceBar(self, bar: BarData):
        if not BarUtils.isOpen(bar):
            self.bar_list = []
            return None
        self.bar_list.append(bar)
        pattern_vaule = KPattern.encode_2k_by_algo1(self.bar_list)
        if self.pattern_values.__contains__(pattern_vaule):
            ##产生一个收集数据
            return CollectData(dimen_value=pattern_vaule,occur_bars=self.bar_list[-3:])
        return None

    def onCollecting(self, data: CollectData, bar: BarData):
        data.unkown_bars.append(bar)
        cur_size = len(data.unkown_bars)
        if cur_size>= 14:
            data.setFinished() ##收集到有14天的数据就算收集完成。

app = App()
start = datetime(year=2018,month=1,day=6)
end = datetime(year=2021,month=1,day=6)
drvier2 = ZZ500StockDriver()
bar_source = app.getBarManager().createBarSoruce(drvier2,start,end)

finished_list = []
CollectHandler.visit(Pattern_2k_by_algo1_handler(),bar_source,finished_list=finished_list)
print(f"finished size :{len(finished_list)}")

value_list_1_map = defaultdict(list)
value_list_3_map = defaultdict(list)
value_list_7_map = defaultdict(list)
value_list_14_map = defaultdict(list)

def cal_pct(close_price_list:[], pre_close_price)->float:
    close_price_list = numpy.array(close_price_list)
    close_price = close_price_list.mean()
    return 100 * (close_price - pre_close_price) / pre_close_price
### 收集对应的涨幅列表
for cData in finished_list:
    assert len(cData.unkown_bars) >= 14
    pattern_vaule = cData.dimen_value
    pre_close_price = cData.occur_bars[-1].close_price
    pct_1 = cal_pct([cData.unkown_bars[0].close_price],pre_close_price)
    pct_3 = cal_pct([cData.unkown_bars[i].close_price for i in range(1,3)],pre_close_price)
    pct_7 = cal_pct([cData.unkown_bars[i].close_price for i in range(4,7)],pre_close_price)
    pct_14 = cal_pct([cData.unkown_bars[i].close_price for i in range(11,14)],pre_close_price)
    value_list_1_map[pattern_vaule].append(pct_1)  #收集1日K线的涨幅情况
    value_list_3_map[pattern_vaule].append(pct_3)  #收集3日K线的涨幅情况
    value_list_7_map[pattern_vaule].append(pct_7)   #收集7日K线的涨幅情况
    value_list_14_map[pattern_vaule].append(pct_14)   #收集14日K线的涨幅情况

dataSet  = {}
fParser = FloatParser()
pattern_value_list = list(value_list_1_map.keys())
##计算分叉线值
dataSet['pattern_value'] = pattern_value_list
dataSet['1日分叉线'] = [ fParser.calc_avg_line(value_list_1_map[pattern_value])  for pattern_value in pattern_value_list]
dataSet['3日分叉线'] = [ fParser.calc_avg_line(value_list_3_map[pattern_value])  for pattern_value in pattern_value_list]
dataSet['7日分叉线'] = [ fParser.calc_avg_line(value_list_7_map[pattern_value])  for pattern_value in pattern_value_list]
dataSet['14日分叉线'] = [ fParser.calc_avg_line(value_list_14_map[pattern_value])  for pattern_value in pattern_value_list]

# dataSet['1日score'] = [ fParser.calc_op_score(value_list_1_map[pattern_value])  for pattern_value in pattern_value_list]
# dataSet['3日score'] = [ fParser.calc_op_score(value_list_3_map[pattern_value])  for pattern_value in pattern_value_list]
# dataSet['7日score'] = [ fParser.calc_op_score(value_list_7_map[pattern_value])  for pattern_value in pattern_value_list]
# dataSet['14日score'] = [ fParser.calc_op_score(value_list_14_map[pattern_value])  for pattern_value in pattern_value_list]

# for pattern_value in pattern_value_list:
#     print(f"{value_list_14_map[pattern_value]}\n")

print(f"{value_list_14_map[258420]}\n")

pData = pandas.DataFrame(dataSet).sort_values(by='7日分叉线')
print(f"{pData}")