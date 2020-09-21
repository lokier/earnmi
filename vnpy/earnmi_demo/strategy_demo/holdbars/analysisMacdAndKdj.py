##统计macd金叉时，kdj的情况
from dataclasses import dataclass
from datetime import datetime

from werkzeug.routing import Map

from earnmi.data.SWImpl import SWImpl
from vnpy.trader.object import BarData

from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator


KDJ_DIS_SIZE = 10

@dataclass
class AnalysisData:
    count = 0
    k_large_than_d_count = 0
    kdj_dis:[] = None

    def __post_init__(self):
        self.kdj_dis = []
        for i in range(0,KDJ_DIS_SIZE):
            self.kdj_dis.append(0)

    def print(self):
        print(f"count=%d,kd_count=%d,dis:{self.kdj_dis}" % (self.count,self.k_large_than_d_count))


def computeAndPrint(bars: []) -> AnalysisData:
    data = AnalysisData()

    total_count = len(bars)
    previous_macd = -1
    previouc_kdj = -1
    indicator = Indicator(50)
    for i in range(0,total_count):
        bar:BarData = bars[i]
        indicator.update_bar(bar)

        k_large_than_d = False
        if indicator.count >= 13:
            k, d, j = indicator.kdj(fast_period=9, slow_period=3, array=True)

            k_large_than_d = k[-1] >= d[-1]
            ##金叉出现
            if (k[-1] >= d[-1] and k[-2] <= d[-2]):
                previouc_kdj = i

        if indicator.count >= 30:
            dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True);
            ##金叉出现
            if (macd_bar[-1] >= 0 and macd_bar[-2] <= 0):
                previous_macd = i
                if previouc_kdj > 0:
                    data.count = data.count + 1
                    if k_large_than_d:
                        data.k_large_than_d_count = data.k_large_than_d_count + 1

                    dis = previous_macd - previouc_kdj
                    if (dis >=0 and dis < KDJ_DIS_SIZE):
                        data.kdj_dis[dis] = data.kdj_dis[dis] + 1
    return data

if __name__ == "__main__":

    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    sw = SWImpl()
    lists = sw.getSW2List()
    for code in lists:
        if len(sw.getSW2Stocks(code)) < 10:
            continue
        bars = sw.getSW2Daily(code, start, end)
        data = computeAndPrint(bars)
        data.print()
        #break
