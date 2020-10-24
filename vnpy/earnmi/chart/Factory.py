import math
from typing import Union

import numpy as np
from numba import int32, jit, float64, numba


class Factory:
    """
    这是一个因子值。
    横向横盘调整指标，大部分的值落在（0,100）之间，越靠近0,越是盘整状态。
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

