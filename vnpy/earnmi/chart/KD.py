import math

import numpy as np
from numba import int32, jit, float64, numba


class KD:

    @jit(nopython=True)  # jit，numba装饰器中的一种
    def macd_rao(close:np.ndarray,open:np.ndarray, period: int32 = 30) -> float64:
        total: float64 = 0.0
        for i in np.arange(-period, 0):
            total += (close[i] + open[i]) / 2
        base_price: float64 = total / period
        total: float64 = 0.0
        for i in np.arange(-period, 0):
            dela = close[i] - base_price
            if dela > 0:
                total += (dela * dela)
            else:
                total -= (dela * dela)
        if abs(total) < 0.001:
            return 0
        if total < 0:
            return -100 * np.sqrt(-total) / base_price
        return 100 * np.sqrt(total) / base_price

    @jit(nopython=True)  # jit，numba装饰器中的一种
    def macd_rao2(close: np.ndarray, open: np.ndarray, period: int32 = 30) -> float64:
        total: float64 = 0.0
        for i in np.arange(-period, 0):
            total += (close[i] + open[i]) / 2
        base_price: float64 = total / period
        total: float64 = 0.0
        for i in np.arange(-period, 0):
            total += close[i] - base_price

        if abs(total) < 0.001:
            return 0
        return 100 * total / base_price

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

    @jit(nopython=True)  # jit，numba装饰器中的一种
    def macd_rao3(close: np.ndarray, open: np.ndarray, period: int32 = 30) -> float64:
        total: float64 = 0.0
        _max:float64 = -9999999999
        _min:float64 = 99999999999
        for i in np.arange(-period, 0):
            total += (close[i] + open[i]) / 2
            _max = max(_max,close[i])
            _min = min(_min,close[i])
        base_price: float64 = total / period
        total: float64 = 0.0
        for i in np.arange(-period, 0):
            total += close[i] - base_price

        if abs(total) < 0.001:
            return 0
        return 100 * total / base_price