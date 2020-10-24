import numpy as np
from future.backports.datetime import datetime

from earnmi.chart.Chart import Chart
from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.chart.Indicator import Indicator
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.BarUtils import BarUtils

"""
多空对方分析
多空对比 = [（收盘价- 最低价） - （最高价 - 收盘价）] / （最高价 - 最低价)
"""
def lsosc(pre_close,close,high,low)->float:
    low = min(pre_close, low)
    high = max(pre_close, high)
    return ((close - low) - (high -close)) / (high-low)

def lsosc2(close,high,low)->float:
    return ((close - low) - (high -close)) / (high-low)

if __name__ == "__main__":
    start = datetime(2015, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)

    bars, code = souces.nextBars()

    split = np.arange(-0.989,1.0,0.05)
    encoder = FloatEncoder(list(split))
    print(f"split:{split}")
    size = len(split)
    collect_bars = {}

    limist_size = 50

    collect_bars_1 = []
    collect_bars_minus_1 = []

    runFlag = True
    while runFlag and not bars is None:
        indicator = Indicator(40)
        prebar = None
        for bar in bars:
            indicator.update_bar(bar)
            if indicator.count > 33 and BarUtils.isOpen(bar):
                lsosc_v = lsosc(prebar.close_price,bar.close_price,bar.high_price,bar.low_price)
                if abs(lsosc_v - 1) < 0.05:
                    collect_bars_1.append(bar)
                if abs(lsosc_v + 1) < 0.05:
                    collect_bars_minus_1.append(bar)

                if len(collect_bars_1) >= limist_size and len(collect_bars_minus_1)>=limist_size:
                    runFlag = False
                    break
            prebar = bar
        bars,code = souces.nextBars()

    # showBars = []
    # for i in range(0,encoder.mask()):
    #     bar = collect_bars.get(i)
    #     if bar is None:
    #         print(f"bar is None ,i={i},mask={encoder.mask()}")
    #         continue
    #     showBars.append(bar)
    chart = Chart()
    showBars = BarUtils.arrangePrice(collect_bars_1,100,accumulate=False)
    chart.show(showBars,savefig='files/lsosc_1.png')

    showBars = BarUtils.arrangePrice(collect_bars_minus_1,100,accumulate=False)
    chart.show(showBars,savefig='files/lsosc_minus_1.png')
