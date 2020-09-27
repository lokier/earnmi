

"""
日K线图编码
"""
from earnmi.chart.FloatEncoder import FloatEncoder


class KEncode():


    def encodeAlgro1(pre_close:float,open:float,high:float,low:float,close:float
                     ,pct_split :[]
                     ,extra_split:[]
                     ) ->int:
        ret, pct_code, high_extra_pct_code, low_extra_pct_code = KEncode.parseAlgro1(pre_close,open,high,low,close,pct_split,extra_split);
        return ret
    """
    值范围为：0-80（小于81）
    （坏处：没有把开盘价考虑进去）
    """
    def parseAlgro1(pre_close:float,open:float,high:float,low:float,close:float,pct_split:[],extra_split:[]):

        pct_size = len(pct_split)
        extra_size = len(extra_split)
        pct = 100*(close - pre_close) / pre_close #涨幅
        #open_pct = 100* open / pre_close #开盘涨幅价
        #high_extra_pct = 100 * (high - max(open, close)) / pre_close
        #low_extra_pct = 100 * (min(open, close) - low) / pre_close

        pct_code = 0
        for i in range(pct_size,0,-1):
            if pct > pct_split[i-1]:
                pct_code = i
                break

        high_extra_pct_code = 0
        high_extra_pct = 100 * abs(high - max(open, close)) / pre_close
        for i in range(extra_size,0,-1):
            if high_extra_pct > extra_split[i-1]:
                high_extra_pct_code = i
                break

        low_extra_pct_code = 0
        low_extra_pct = 100 * abs(min(open, close) - low) / pre_close
        for i in range(extra_size,0,-1):
            if low_extra_pct > extra_split[i-1]:
                low_extra_pct_code = i
                break


        PCT_MASK = pct_size + 1
        EXTRA_PCT_MASK = extra_size + 1
        ret = low_extra_pct_code * EXTRA_PCT_MASK* PCT_MASK + high_extra_pct_code * PCT_MASK + pct_code

        return ret,pct_code,high_extra_pct_code,low_extra_pct_code


