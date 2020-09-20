from dataclasses import dataclass

from earnmi.chart.Chart import HoldBar
from earnmi.uitl.utils import utils
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
