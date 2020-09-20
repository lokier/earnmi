from dataclasses import dataclass
from datetime import datetime

from earnmi.uitl.utils import utils
from earnmi_demo.strategy_demo.holdbars.HoldBarAnanysic import *
from vnpy.trader.object import BarData


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

    """
    计算holdbar的指标数据。
    """
    def computeHoldBarIndictor(holdbarList: []) -> HoldBarData:
        max_cost_pct = 0.0
        min_cost_pct = 0.0
        total_day = 0
        total_eran_cost_pct = 0.0
        total_holdbar = len(holdbarList)
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
        preHobar = None
        for i in range(0, total_holdbar):
            holdBar: HoldBar = holdbarList[i]
            assert  holdBar!= preHobar
            barLen = len(holdBar.bars)
            for j in range(0,5):
                if j >= barLen:
                    break
                bar:BarData = holdBar.bars[j]
                pct = (bar.close_price - bar.open_price) / bar.open_price
                dict[j].append(pct)

            preHobar = holdBar

        for i in range(0, 5):
            lists = np.array(dict[i])
            lists = lists * 100
            size = len(lists)
            #print(f'{lists}')
            print(f"[{i}]: size = {size},avg = %.2f%%, max = %.2f%%,min = %.2f%%,std =%.2f" % (lists.mean() ,lists.max(),lists.min(), np.std(lists)))

        return dict


if __name__ == "__main__":
    from earnmi.chart.Chart import HoldBar, Chart
    from earnmi.data.SWImpl import SWImpl
    import numpy as np

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
    for code in lists:

        if len(sw.getSW2Stocks(code)) < 10:
            continue

        bars = sw.getSW2Daily(code, start, end)
        # print(f"bar.size = {bars.__len__()}")
        indictor = macd()
        chart.run(bars, indictor)

        data = HoldBarUtils.printfPctdispute(indictor.getHoldBars())
        for i in range(0,5):
            lists = np.array(data[i])
            dict[i].append(lists.mean())

    for i in range(0, 5):
        lists = np.array(data[i])
        print(f"[{i}]: avg = %.2f%%" % (lists.mean()*100))