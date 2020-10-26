import math
from typing import Union

import numpy as np
from numba import int32, jit, float64, numba
import talib

from earnmi.chart.Indicator import Indicator


class Factory:



    """
    横向横盘调整因子值，大部分的值落在（0,100）之间，越靠近0,越是盘整状态。
    """
    @jit(nopython=True)  # jit，numba装饰器中的一种
    def vibrate(close: np.ndarray, open: np.ndarray, period: int32 = 12) -> float64:
        total: float64 = 0.0
        for i in np.arange(-period, 0):
            total += (close[i] + open[i]) / 2
        base_price: float64 = total / period
        total: float64 = 0.0
        for i in np.arange(-period, 0):
            dela = close[i] - base_price
            total += (dela * dela)
        return 100 * np.sqrt(total) / base_price

    """
    
    价格与成交量偏离因子值。(-1到1） 
    """
    def pvb(close: np.ndarray, high: np.ndarray,low:np.ndarray,volumn:np.ndarray, period: int32 = 20)->float:
        ##涨幅与多空成交量对比的相关系数。
        pct_list,volumn_pct_list = Factory.__pbv_inter(close,high,low,volumn,period)
        ret = talib.CORREL(pct_list, volumn_pct_list, timeperiod=period)

        return ret[-1]

    @jit(nopython=True)  # jit，numba装饰器中的一种
    def __pbv_inter(close: np.ndarray, high: np.ndarray,low:np.ndarray,volumn:np.ndarray, period: int32 = 20):
        pct_list = np.full(period, np.nan)
        volumn_pct_list = np.full(period , np.nan)
        # _pre_volumn_lsosc = Indicator.lsosc(close[-2-period],close[-1-period],high[-1-period],low[-1-period]) * volumn[-1-period]
        pre_volum = 0
        for i in range(-period, 0):
            pct_list[i] = close[i]
            _low = min(close[i - 1], low[i])
            _high = max(close[i - 1], high[i])
            assert abs(_high - _low) > 0.008
            # print("why")
            lsosc = ((close[i] - _low) - (_high - close[i])) / (_high - _low)
            # volumn_lsosc = Indicator.lsosc(close[i-1],close[i],high[i],low[i]) * volumn[i]
            volumn_pct_list[i] = pre_volum + lsosc * volumn[i]
            pre_volum = volumn_pct_list[i]
        return pct_list,volumn_pct_list