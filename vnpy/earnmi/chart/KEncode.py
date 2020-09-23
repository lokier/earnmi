

"""
日K线图编码
"""
class KEncode():


    def encodeAlgro1(pre_close:float,open:float,high:float,low:float,close:float) ->int:
        ret, pct_code, high_extra_pct_code, low_extra_pct_code = KEncode.__parseAlgro1(pre_close,open,high,low,close);
        return ret
    """
    值范围为：0-80（小于81）
    （坏处：没有把开盘价考虑进去）
    """
    def __parseAlgro1(pre_close:float,open:float,high:float,low:float,close:float
                      ,pct_split=[-6.7,-4.1,-2.0,-0.5,0.5,2.0,4.1,6.7]
                      ,extra_split=[0.5,0.7]):

        pct_size = len(pct_split)
        extra_size = len(extra_split)
        pct = 100*(close - pre_close) / pre_close #涨幅
        #open_pct = 100* open / pre_close #开盘涨幅价
        #high_extra_pct = 100 * (high - max(open, close)) / pre_close
        #low_extra_pct = 100 * (min(open, close) - low) / pre_close

        pct_code = 0
        for i in range(0,pct_size):
            if pct > pct_split[i]:
                pct_code = i
        if pct_code ==-1:
            pct_code = pct_size - 1

        high_extra_pct_code = -1
        high_extra_pct =abs(high - max(open, close)) / pre_close
        for i in range(0, extra_size - 1):
            if high_extra_pct < extra_split[i]:
                high_extra_pct_code = i
        if high_extra_pct_code == -1:
            high_extra_pct_code = extra_size - 1

        pct_length = abs(open - close) #3个值

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
        ret = low_extra_pct_code * 3* 9 + high_extra_pct_code * 9 + pct_code
        return ret,pct_code,high_extra_pct_code,low_extra_pct_code


