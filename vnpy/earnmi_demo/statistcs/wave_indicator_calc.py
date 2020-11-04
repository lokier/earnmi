import numpy as np
from future.backports.datetime import datetime
from earnmi.chart.Chart import Chart
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange
from earnmi.chart.Indicator import Indicator
from earnmi.chart.Factory import Factory
from earnmi.data.MarketImpl import MarketImpl
from datetime import datetime, timedelta
import talib
import numpy as np
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.BarUtils import BarUtils
import os



def parse_wave_disbute():
    start = datetime(2015, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    bars, code = souces.nextBars()
    imgeDir = "files/zz500_wave_distbute"
    if not os.path.exists(imgeDir):
        os.makedirs(imgeDir)

    chart = Chart()
    period_list = [9,12,20,25]
    value_list_map = {}
    for p in period_list:
        value_list_map[p] = [
            [],#wave_down
            [],#wave_up
        ]

    count = 0

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
                    #break
                #v = indicator.macd_rao(period=30)
                for p in period_list:
                    aroon_down, aroon_up = indicator.aroon(p)
                    if aroon_down > 0  or aroon_up < 100:
                        continue
                    wave_down, wave_up = Factory.wave(p, indicator.close,indicator.high,indicator.low)
                    value_list_map[p][0].append(wave_down)
                    value_list_map[p][1].append(wave_up)
                    # value_list_map[p].append(v)
                    # if p == 30:
                    #     if  v< -0.85:
                    #         print(f"find:{v}")
                    #         chart.show(last_33bars,
                    #             savefig=f"{imgeDir}/z80_1_minus_{bar.symbol}time_{bar.datetime.year}_{bar.datetime.month}_{bar.datetime.day}.jpg")
                    #
        bars, code = souces.nextBars()


    for period, value_list_array in value_list_map.items():
        print(f"===period:{period}===============")
        for i in range(0,len(value_list_array)):
            value_list = np.array(value_list_array[i])
            _min, _max = [value_list.min(), value_list.max()]
            print(f"    valuesList[{i}]:, max:%.2f,min:%.2f,count:{len(value_list)}" % (_max, _min))
            N = 5
            spli_list = []
            for i in range(0, N + 1):
                spli_list.append(_min + i * (_max - _min) / N)
            # spli_list = [ 0,100]
            dif_encoder = FloatEncoder(spli_list)
            print(f"                分布:{FloatRange.toStr(dif_encoder.computeValueDisbustion(value_list), dif_encoder)}")
    pass


if __name__ == "__main__":
    parse_wave_disbute()

