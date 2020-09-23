

"""
日K线图编码
"""
class KEncode():

    """
    值范围为：0-80（小于81）
    （坏处：没有把开盘价考虑进去）
    """
    def encodeAlgro1(pre_close:float,open:float,high:float,low:float,close:float) ->int:
        pct = 100*(close - pre_close) / pre_close #涨幅
        #open_pct = 100* open / pre_close #开盘涨幅价
        #high_extra_pct = 100 * (high - max(open, close)) / pre_close
        #low_extra_pct = 100 * (min(open, close) - low) / pre_close

        pct_code = 0  #9个值
        if pct > 0.5:
            if pct < 2.0:
                pct_code = 1
            elif pct < 4.1:
                pct_code = 2
            elif pct < 6.7:
                pct_code = 3
            else:
                pct_code = 4
        elif pct < -0.5:
            if pct > -2.0:
                pct_code = 5
            elif pct > -4.1:
                pct_code = 6
            elif pct > -6.7:
                pct_code = 7
            else:
                pct_code = 8

        pct_length = abs(open - close) #3个值
        high_extra_length = abs(high - max(open,close))
        low_extra_length = abs(min(close,open)-low)
        high_extra_pct_code = 0
        if high_extra_length > pct_length:
            if high_extra_length < 2.5 * pct_length:
                high_extra_pct_code = 1
            else:
                high_extra_pct_code = 2

        low_extra_pct_code = 0  #3个值
        if low_extra_length > pct_length:
            if low_extra_length < 2.5 * pct_length:
                low_extra_pct_code = 1
            else:
                low_extra_pct_code = 2
        return low_extra_pct_code * 3* 9 + high_extra_pct_code * 9 + pct_code


