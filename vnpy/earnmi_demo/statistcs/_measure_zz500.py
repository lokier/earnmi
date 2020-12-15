from datetime import datetime

from earnmi.chart.Indicator import Indicator
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.uitl.BarUtils import BarUtils
from earnmi.uitl.utils import utils
from earnmi_demo.statistcs.__indicator_measure__ import IndicatorMeasure


def getLast10KdjHoldDay(indicator,min_dist):
    k, d, j = indicator.kdj(fast_period=9, slow_period=3, array=True)
    dif, dea, macd = indicator.macd(fast_period=12, slow_period=26, signal_period=9,array=True)
    p_di = indicator.plus_di(period, array=True)
    m_di = indicator.minus_di(period, array=True)
    holdDay = 0
    for i in range(-1,-8,-1):
        #isHold = k[i] >= d[i] and p_di[i] - m_di[i] > min_dist
        isHold = k[i] >= d[i] and dif[i] > 0 and dif[i] > dea[i]
        if not isHold:
            break
        holdDay +=1
    return holdDay

if __name__ == "__main__":
    start = datetime(2017, 10, 1)
    end = datetime(2020, 9, 30)
    souces = ZZ500DataSource(start, end)
    measure = IndicatorMeasure()
    bars, code = souces.nextBars()
    while not bars is None:
        print(f"new session=>code:{code},bar.size = {len(bars)}")
        measure.startSession()
        indicator = Indicator(42)
        latesBars = []
        for bar in bars:
            if not BarUtils.isOpen(bar):
                continue
            indicator.update_bar(bar)
            latesBars.append(bar)
            if not indicator.inited:
                continue

            paramsMap = {
                "period":[14],
                'min_dist': [10,15,20],
                'x':[2],
                'duration':[4]
                #'max_dist': [ 70],
                #'min_p_id': [4,7,10,13,15,50],
            }

            paramList = utils.expandParamsMap(paramsMap)
            for param in paramList:
                period = param['period']
                min_dist = param['min_dist']
                x = param['x']
                duration = param['duration']

                #max_dist = param['max_dist']
                # p_di = indicator.plus_di(period)
                # m_di = indicator.minus_di(period)

                holdKdjDay = getLast10KdjHoldDay(indicator,min_dist)

                # dist = p_di - m_di
                ##金叉形成之后有一天的缓冲时间去考虑是否买入，所以holdKdjDay>1
                hold =  holdKdjDay >= x and holdKdjDay <= x+duration

                measure.measure(f"di指标因子:{param}",bar,hold,putIntoWhileNotHold=False)

        measure.endSession()
        bars, code = souces.nextBars()
    ##打印因子策略结果
    measure.printBest()