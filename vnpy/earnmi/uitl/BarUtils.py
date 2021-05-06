from typing import Sequence

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

import numpy as np

class BarUtils:

    """
    返回np.narray形式：low,high,open,close,volume
    """
    def to_np_array(bars:['BarData']):
        size = len(bars)
        low = np.full(size,0.0)
        high = np.full(size,0.0)
        open = np.full(size,0.0)
        close = np.full(size,0.0)
        volume = np.full(size,0.0)
        for i in range(size):
            low[i] = bars[i].low_price
            high[i] = bars[i].high_price
            open[i] = bars[i].open_price
            close[i] = bars[i].close_price
            volume[i] = bars[i].volume
        return low,high,open,close,volume

    """
    将零散的整理bars的价格
    """
    def arrangePrice(bars:['BarData'],basePrice:float,accumulate=True)->['BarData']:

        barList = []
        new_open_price = basePrice
        for bar in bars:
            open_price = bar.open_price
            close_price = bar.close_price
            high_price = bar.high_price
            low_price = bar.low_price
            close_price = close_price * new_open_price / open_price
            high_price = high_price * new_open_price / open_price
            low_price = low_price * new_open_price / open_price
            open_price = new_open_price

            barList.append( BarData(
                symbol=bar.symbol,
                exchange=Exchange.SSE,
                datetime=bar.datetime,
                interval=Interval.WEEKLY,
                volume=bar.volume,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                gateway_name='arrangePrice'
            ))
            if accumulate:
                new_open_price = close_price
        return barList

    @staticmethod
    def isAllOpen(bars:['BarData']) ->bool:
        for bar in bars:
            if not BarUtils.isOpen(bar):
                return False
        return True

    @staticmethod
    def isOpen(bar:BarData) ->bool:
        return bar.volume > 0

    """
    返回最大的间隔天数
    """
    @staticmethod
    def getMaxIntervalDay(bars:Sequence['BarData'])->int:
        _len = len(bars)
        if _len < 2:
            return 0
        max_day = 1
        for i in range(1,_len):
            _day = (bars[i].datetime - bars[i-1].datetime).days
            assert _day > 0
            if _day > max_day:
                max_day = _day
        return max_day

    def getMaxSellBuyPct(bars:Sequence['BarData'],basePrice):
        sell_pct = 100 * ((bars[0].high_price + bars[0].close_price) / 2 - basePrice) / basePrice
        buy_pct = 100 * ((bars[0].low_price + bars[0].close_price) / 2 - basePrice) / basePrice
        for i in range(1,len(bars)):
            bar = bars[i]
            _s_pct = 100 * ((bar.high_price + bar.close_price) / 2 - basePrice) / basePrice
            _b_pct = 100 * ((bar.low_price + bar.close_price) / 2 - basePrice) / basePrice
            sell_pct = max(_s_pct, sell_pct)
            buy_pct = min(_b_pct, buy_pct)
        return  sell_pct,buy_pct

    def getAvgClosePct(bars:Sequence['BarData'],basePrice):
        close_price = 0
        size = len(bars)
        for i in range(0,size):
            bar = bars[i]
            close_price += bar.close_price
        return  100 * (close_price / size - basePrice) / basePrice

    """
    在各个天的涨幅情况。
    """
    def getPctList(bars:Sequence['BarData'],basePrice)->np.ndarray:
        size = len(bars)
        pct_list = np.full(len(bars),size)
        for i in range(0,size):
            bar = bars[i]
            pct_list[i] = 100 * (bar.close_price - basePrice) / basePrice
        return  pct_list

    @classmethod
    def filterNoOpen(cls, bars):
        new_bars = []
        for bar in bars:
            if BarUtils.isOpen(bar):
                new_bars.append(bar)
        return new_bars