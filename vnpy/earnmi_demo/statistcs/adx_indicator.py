import os

from earnmi.chart.Chart import Chart
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange
from earnmi.chart.Indicator import Indicator
from earnmi.chart.Factory import Factory
from earnmi.data.MarketImpl import Market2Impl
from datetime import datetime, timedelta
import talib
import numpy as np
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.BarUtils import BarUtils
from earnmi_demo.statistcs.FactoryParser import FactoryParser

"""
统计因子值得分布。
"""
def parse_wave_disbute():
    start = datetime(2015, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    bars, code = souces.nextBars()
    imgeDir = "files/zz500_wave_distbute"
    if not os.path.exists(imgeDir):
        os.makedirs(imgeDir)
    chart = Chart()
    period_list = [14,20,25,30]
    count = 0
    fPraser = FactoryParser()
    while not bars is None:
        indicator = Indicator(40)
        last_33bars = np.full(33, None)
        for bar in bars:
            if not BarUtils.isOpen(bar):
                continue
            indicator.update_bar(bar)
            last_33bars[:-1] = last_33bars[1:]
            last_33bars[-1] = bar
            if indicator.count > 34:
                count += 1
                if count %10000 == 0:
                    print(f"progress: {count}")
                for p in period_list:
                    m_di = indicator.minus_di(p)
                    p_di = indicator.plus_di(p)
                    fPraser.put(f"period[{p}]+id",p_di,0)
                    fPraser.put(f"period[{p}]-id", m_di, 0)
                    fPraser.put(f"period[{p}]_dist", p_di - m_di, 0)

        bars, code = souces.nextBars()
    fPraser.printRange()
    pass


if __name__ == "__main__":
    parse_wave_disbute()
