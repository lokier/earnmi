from dataclasses import dataclass
from datetime import datetime

from werkzeug.routing import Map

from earnmi.chart.Indicator import Indicator
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData
from earnmi.chart.Chart import HoldBar, Chart, HoldBarMaker, IndicatorItem, Signal


@dataclass
class HoldBarData:
    total_cost_pct:float = 0.0 ##总共收益
    total_cost_pct_std:float = 0.0 ##标准差
    total_max_cost_pct:float = 0.0
    total_min_cost_pct:float = 0.0
    avg_eran_cost_pct:float = 0.0  ##每个盈利holdbard的平均盈利


    total_day:int = 0 ##总天数
    total_earn_day:int = 0 ##盈利总天数

    total_holdbar:int = 0;
    total_holdbar_earn:int = 0

    max_cost_pct:float =0.0 ##当中最大收益
    min_cost_pct:float =0.0 ##当中最小收益




class HoldBarUtils:

    def isEarnBarList(bars: []) -> bool:
        size = len(bars)
        if size >= 7:
            startPrice = bars[0].close_price
            maxPrice = startPrice
            for i in range(1, 7):
                maxPrice = max(bars[i].high_price, maxPrice)

            pct = (maxPrice - startPrice) / startPrice
            if pct > 0.0799999:
                return True

        return False

    """
    计算holdbar的指标数据。
    """
    def computeHoldBarIndictor(holdbarList: []) -> HoldBarData:
        max_cost_pct = 0.0
        min_cost_pct = 0.0
        total_day = 0
        total_eran_cost_pct = 0.0
        total_holdbar = len(holdbarList)

        if total_holdbar < 1:
            return None

        total_holdbar_earn = 0
        total_earn_day = 0
        barList = utils.to_bars(holdbarList)

        for i in range(0, total_holdbar):
            bar: BarData = barList[i]
            holdBar: HoldBar = holdbarList[i]
            total_day = total_day + holdBar.getDays()
            pct = holdBar.getCostPct()

            if pct > 0.00001:
                total_holdbar_earn = total_holdbar_earn + 1
                total_eran_cost_pct = total_eran_cost_pct + pct
                total_earn_day = total_earn_day + holdBar.getDays()
            if pct > max_cost_pct:
                max_cost_pct = pct
            if pct < min_cost_pct:
                min_cost_pct = pct

        ret = HoldBarData()
        ret.total_cost_pct = (barList[-1].close_price - barList[0].open_price) / barList[0].open_price
        ret.max_cost_pct = max_cost_pct
        ret.min_cost_pct = min_cost_pct
        ret.total_day = total_day
        ret.total_holdbar = total_holdbar
        ret.total_holdbar_earn = total_holdbar_earn
        if (total_holdbar_earn < 1):
            ret.avg_eran_cost_pct = 0
        else:
            ret.avg_eran_cost_pct = total_eran_cost_pct / total_holdbar_earn
        ret.total_earn_day = total_earn_day
        return ret


    def filterHoldBar(holdbarList: []) ->[]:
        """
        过滤holdbar:
        规则：
        首次涨幅超过2%，且第二天不低于第一天的开盘价格。

        """
        total_holdbar = len(holdbarList)
        hodbarNewList = []

        day_len = []
        to_high_day = []  ##到底最高点的天数
        to_low_day = []  ##到底最高点的天数

        maker = HoldBarMaker()

        for i in range(0, total_holdbar):
            holdBar: HoldBar = holdbarList[i]
            barLen = len(holdBar.bars)
            day_len.append(barLen)
            high_day = -1
            low_day = -1

            add = False
            if barLen >= 5:
                first_pct = None
                for j in range(0, barLen):
                    bar: BarData = holdBar.bars[j]
                    pct = (bar.close_price - bar.open_price) / bar.open_price

                    if high_day == -1 and abs(bar.high_price - holdBar.high_price) < 0.02:
                        high_day = j

                    if low_day == -1 and j > 0 and abs(bar.low_price - holdBar.low_price) < 0.02:
                        low_day = j

                    if j == 0:
                        first_pct = pct
                    to_high_day.append(high_day)
                    to_low_day.append(low_day)

                if first_pct > 0.019999:
                    add = True

            if add:
                maker.onHoldStart(holdBar.bars[0])
                maker.onHoldUpdate(holdBar.bars[1])
                maker.onHoldUpdate(holdBar.bars[2])
                maker.onHoldUpdate(holdBar.bars[3])
                maker.onHoldUpdate(holdBar.bars[4])
                maker.onHoldEnd()

        return maker.getHoldBars()

    """
      打印前5个涨幅分布情况
    """
    def printfPctdispute(holdbarList: []) -> {}:

        total_holdbar = len(holdbarList)
        dict = {}
        dict[0] = []
        dict[1] = []
        dict[2] = []
        dict[3] = []
        dict[4] = []
        day_len = []
        to_high_day = [] ##到底最高点的天数
        to_low_day = [] ##到底最高点的天数

        for i in range(0, total_holdbar):
            holdBar: HoldBar = holdbarList[i]
            barLen = len(holdBar.bars)
            day_len.append(barLen)
            high_day = -1
            low_day = -1
            for j in range(0,barLen):
                bar: BarData = holdBar.bars[j]
                pct = (bar.close_price - bar.open_price) / bar.open_price
                if j <5:
                    dict[j].append(pct)

                if high_day ==-1 and abs(bar.high_price - holdBar.high_price) < 0.02:
                    high_day = j

                if low_day ==-1 and j > 0 and abs(bar.low_price - holdBar.low_price) < 0.02:
                    low_day = j
                    

            assert high_day >= 0
            
            
            to_high_day.append(high_day)

            if low_day >=0:
                to_low_day.append(low_day)


        for i in range(0, 5):
            lists = np.array(dict[i])
            day_len = np.array(day_len)
            to_high_day = np.array(to_high_day)
            to_low_day = np.array(to_low_day)

            lists = lists * 100
            size = len(lists)
            #print(f'{lists}')
            print(f"[{i}]: size = {size}\ncost:avg = %.2f%%, max = %.2f%%,min = %.2f%%,"f"std =%.2f" % (
                     lists.mean() ,lists.max(),lists.min(), np.std(lists),
                    )
                  )
        print( f"\n\tday:total avg = %.2f, high avg=%.2f, low avg=%.2f" % ( day_len.mean(),to_high_day.mean(),to_low_day.mean()))

        return dict


if __name__ == "__main__":
    from earnmi.chart.Chart import HoldBar, Chart, IndicatorItem, Signal
    from earnmi.data.SWImpl import SWImpl
    import numpy as np


    class macd(IndicatorItem):
        def getValues(self, indicator: Indicator, bar: BarData, signal: Signal) -> Map:
            values = {}
            count = 30
            if indicator.count >= count:
                dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True);
                ##金叉出现
                if (macd_bar[-1] >= 0 and macd_bar[-2] <= 0):
                    if not signal.hasBuy:
                        signal.buy = True

                    ##死叉出现
                if (macd_bar[-1] <= 0 and macd_bar[-2] >= 0):
                    if signal.hasBuy:
                        signal.sell = True
            return values

    sw = SWImpl()
    lists = sw.getSW2List()
    chart = Chart()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    dict = {}
    dict[0] = []
    dict[1] = []
    dict[2] = []
    dict[3] = []
    dict[4] = []

    indictor = macd()
    for code in lists:

        if len(sw.getSW2Stocks(code)) < 10:
            continue

        bars = sw.getSW2Daily(code, start, end)
        # print(f"bar.size = {bars.__len__()}")
        chart.run(bars, indictor)

        holdbars = indictor.getHoldBars()
        # maker = HoldBarMaker()
        # for holdbar in holdbars:
        #     if(HoldBarUtils.isEarnBarList(holdbar.bars)):
        #         barList = holdbar.bars
        #         maker.onHoldStart(barList[0])
        #         for i in range(1,len(barList)):
        #             maker.onHoldUpdate(barList[i])
        #         maker.onHoldEnd()
        # holdbars = maker.getHoldBars()

        data = HoldBarUtils.printfPctdispute(holdbars)
        for i in range(0,5):
            lists = np.array(data[i])
            dict[i].append(lists.mean())

    for i in range(0, 5):
        lists = np.array(dict[i])
        lists = lists * 100
        print(f"[{i}]: avg = %.2f%%,std=%.2f" % (lists.mean(),lists.std()))

    print(f"{dict[0]}")