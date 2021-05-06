import numpy as np
import talib
from numba import int32, jit, float64


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
      改进后的arron指标。 以买方、卖方力量为准
    """
    def arron(period,close:np.ndarray, high: np.ndarray,low:np.ndarray):
        sell = (high + close) / 2
        buy =  (low+ close) / 2
        aroon_down, aroon_up = talib.AROON(sell, buy, period)
        return aroon_down,aroon_up

    """
       参考Arron方式，wave指标统计在一个period周期内的波动率，也就是创新高值的能力。创新高的有create_high个，创新低的有几个create_low。
       返回wave_down,wave_up。[0,100]之间。
    """
    @jit(nopython=True)  # jit，numba装饰器中的一种
    def wave(period, close: np.ndarray, high: np.ndarray, low: np.ndarray):
        sell = (high + close) / 2
        buy = (low + close) / 2

        high_cnt = 0
        low_cnt = 0
        high_value = sell[-period]
        low_value = buy[-period]
        for i in range(-period+1,0):
            if sell[i] >= high_value:
                high_cnt +=1
                high_value = sell[i]
            if buy[i] <= low_value:
                low_cnt+=1
                low_value = buy[i]
        wave_down = 100 * low_cnt / period
        wave_up = 100 * high_cnt / period
        return wave_down, wave_up

    """
     能量波动潮因子。
     wave+obv结合。
    """

    @jit(nopython=True)  # jit，numba装饰器中的一种
    def obv_wave(period, close: np.ndarray, high: np.ndarray, low: np.ndarray,volumn:np.ndarray):

        # assert abs(_high - _low) > 0.008
        # print("why")
        assert  len(close) > period
        obv = np.zeros(period)
        for i in range(-period,0):
            _low = min(close[i-1], low[i])
            _high = max(close[i-1], high[i])
            obv[i] = ((close[i] - _low) - (_high - close[i])) / (_high - _low) * volumn[i]
        ##统计obv创新高和创新低的个数
        high_cnt = 0
        low_cnt = 0
        high_value = obv[-period]
        low_value = obv[-period]
        high_index = -period
        low_index = -period
        for i in range(-period + 1, 0):
            if obv[i] >= high_value:
                high_cnt += 1
                high_index = i
                high_value = obv[i]
            if obv[i] <= low_value:
                low_cnt += 1
                low_index = i
                low_value = obv[i]

        obv_wave_down = 100 * low_cnt / period
        obv_wave_up = 100 * high_cnt / period
        #Aroon(上升) = [(计算期天数 - 最高价后的天数) / 计算期天数] * 100
        #Aroon(下降) = [(计算期天数 - 最低价后的天数) / 计算期天数] * 100

        high_day_prirod = abs(high_index) - 1
        low_day_period = abs(low_index) -1
        arron_up = 100 * (period - high_day_prirod) / period
        arron_down = 100 * (period - low_day_period) / period

        return  arron_down * obv_wave_down /100, arron_up * obv_wave_up / 100

    """
    
    价格与成交量偏离因子值。(-1到1） 没有验证过。
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


    """
    第一个元素总是为0
    """
    def ad_diff(close: np.ndarray,high: np.ndarray,low:np.ndarray,volumn:np.ndarray):
        size = len(close)
        ad_diff_list = np.full(size, 0.0)

        for i in range(1,size):
            # 多空对比 = [（收盘价- 最低价） - （最高价 - 收盘价）] / （最高价 - 最低价)
            dk1 = ((close[i] - low[i]) - (high[i] - close[i])) /(high[i] - low[i])

            adj_high = max(high[i],close[i-1])
            adj_low = min(low[i],close[i-1])
            dk2 = ((close[i] - adj_low) - (adj_high - close[i])) /(adj_high - adj_low)

            diff = abs(dk1-dk2)
            ad_diff_list[i] = ad_diff_list[i-1]+ diff * volumn[i]
        return ad_diff_list

    def ad_diff2(close: np.ndarray,high: np.ndarray,low:np.ndarray,volumn:np.ndarray):
        size = len(close)
        ad_diff_list = np.full(size, 0.0)

        for i in range(1,size):
            # 多空对比 = [（收盘价- 最低价） - （最高价 - 收盘价）] / （最高价 - 最低价)
            dk1 = ((close[i] - low[i]) - (high[i] - close[i])) /(high[i] - low[i])

            adj_high = max(high[i],close[i-1])
            adj_low = min(low[i],close[i-1])
            dk2 = ((close[i] - adj_low) - (adj_high - close[i])) /(adj_high - adj_low)

            diff = dk2-dk1
            ad_diff_list[i] = ad_diff_list[i-1]+ diff * volumn[i]
        return ad_diff_list