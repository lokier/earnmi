from collections import defaultdict
from typing import Callable
from earnmi.data.BarSoruce import BarSource
from earnmi.model.bar import BarData
from earnmi.uitl.BarUtils import BarUtils


class KPattern:

    # ALGO1_PCT_LIST = [-7, -5, -3, -1.5, -0.5, 0.5, 1.5, 3, 5, 7]
    # ALGO1_EXTRA_PCT_LIST = [0.3, 1.2, 3]

    ALGO1_PCT_LIST = [-7, -4, -2, -0.8, 0.8, 2, 4, 7]
    ALGO1_EXTRA_PCT_LIST = [0.3, 1.6]

    @staticmethod
    def encode_k_bars(pre_close:float,open:float,high:float,low:float,close:float,pct_split:[],extra_split:[]):
        """
        使用算法1计算2日K线图的编码值。
            生成4个维度的值并进行编码.
        返回:
            如果有编码值，返回对应的编码值，否则返回None
        """
        pct_size = len(pct_split)
        extra_size = len(extra_split)
        pct = 100 * (close - pre_close) / pre_close  # 涨幅
        open_pct = 100* (close - open) / open #开盘涨幅价

        pct_code = 0
        for i in range(pct_size, 0, -1):
            if pct > pct_split[i - 1]:
                pct_code = i
                break
        open_pct_code = 0
        for i in range(pct_size, 0, -1):
            if open_pct > pct_split[i - 1]:
                open_pct_code = i
                break

        high_extra_pct_code = 0
        high_extra_pct = 100 * abs(high - max(open, close)) / close
        for i in range(extra_size, 0, -1):
            if high_extra_pct > extra_split[i - 1]:
                high_extra_pct_code = i
                break

        low_extra_pct_code = 0
        low_extra_pct = 100 * abs(min(open, close) - low) / close
        for i in range(extra_size, 0, -1):
            if low_extra_pct > extra_split[i - 1]:
                low_extra_pct_code = i
                break

        PCT_MASK = pct_size + 1
        EXTRA_PCT_MASK = extra_size + 1
        ret = low_extra_pct_code * EXTRA_PCT_MASK * PCT_MASK * PCT_MASK + high_extra_pct_code * PCT_MASK * PCT_MASK + pct_code * PCT_MASK + open_pct_code
        return [ret,EXTRA_PCT_MASK*EXTRA_PCT_MASK*PCT_MASK*PCT_MASK]


    @staticmethod
    def encode_2k_by_algo1(bars:['BarData'])->int:
        """
        使用算法1计算2日K线图的编码值。
        """
        if len(bars) < 3:
            return None
        ret = 0
        for i in range(-2,0,):
            bar:BarData = bars[i]
            encode,mask = KPattern.encode_k_bars(bars[i-1].close_price,
                                               bar.open_price,bar.high_price,bar.low_price,bar.close_price,
                                               KPattern.ALGO1_PCT_LIST,KPattern.ALGO1_EXTRA_PCT_LIST)
            ret = ret * mask + encode
        return ret

    @staticmethod
    def encode_3k_by_algo1(bars: ['BarData']) -> int:
        """
        使用算法1计算2日K线图的编码值。
        """
        if len(bars) < 4:
            return None
        ret = 0
        for i in range(-3, 0, ):
            bar: BarData = bars[i]
            encode, mask = KPattern.encode_k_bars(bars[i - 1].close_price,
                                                  bar.open_price, bar.high_price, bar.low_price, bar.close_price,
                                                  KPattern.ALGO1_PCT_LIST, KPattern.ALGO1_EXTRA_PCT_LIST)
            ret = ret * mask + encode
        return ret


def anaylsisPatternCoverity(bar_source:BarSource,calc_pattern_value:Callable,min_coverity_rate = 0.0005):
    from earnmi.core.analysis.FloatRange import FloatDistribute
    pattern_value_map = defaultdict(int)
    total_count = 0
    for symbol,bars in bar_source.items():
        print(f"symbol:{symbol}: size = {len(bars)}")
        bar_list = []
        for bar in bars:
            if BarUtils.isOpen(bar):
                bar_list.append(bar)
                pattern_value = calc_pattern_value(bar_list)  ##前2个交易日的k线形态编码
                if not pattern_value is None:
                    total_count+=1
                    pattern_value_map[pattern_value] = pattern_value_map[pattern_value] +1
            else:
                bar_list = []
    accept_min_count = total_count * min_coverity_rate
    accept_pattern_list = []
    accept_pattern_count_list = []
    accept_count =0.0
    for pattern_value,count in pattern_value_map.items():
        if count >  accept_min_count:
            accept_pattern_list.append(pattern_value)
            accept_pattern_count_list.append(float(count))
            accept_count+=count
    dist = FloatDistribute(accept_pattern_count_list)
    print(f"发生总共{total_count}个形态识别事件，设定的最小满足覆盖率{min_coverity_rate*100}% = {int(accept_min_count)}")
    print(f"  满足最小覆盖率的形态个数:{len(accept_pattern_list)}, 最终覆盖率为:{accept_count/total_count *100}%")
    print(f"  各个形态的个数分布为: {dist.toStr(limit_show_count=6)}")
    print(f"  满足形态的模式值: {accept_pattern_list}")