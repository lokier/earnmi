from collections import defaultdict
from datetime import datetime, timedelta
from typing import Tuple

from pandas import DataFrame

from earnmi.strategy.StockStrategy import BackTestContext
from vnpy.trader.constant import Interval, Exchange, Status, Direction
import jqdatasdk as jq

class utils:

    @staticmethod
    def split_datetime(start:datetime,end:datetime,batch_day:int):
        """
        分割一段时间，以便分批处理。
        返回:
            [[start1,end1],[start2,end2]...]
        """
        assert batch_day > 0
        batch_start = start
        time_span_list = []
        while batch_start.__lt__(end):
            batch_end = batch_start + timedelta(days=batch_day)
            batch_end = utils.to_end_date(batch_end)
            if (batch_end.__gt__(end)):
                batch_end = end
            assert batch_start<=batch_end
            time_span_list.append([batch_start,batch_end])
            batch_start = utils.to_start_date(batch_end + timedelta(days = 1))
            assert batch_start>=batch_end
        assert time_span_list[-1][-1] == end
        assert time_span_list[0][0] == start
        return time_span_list

    """
    计算收益率
    返回: 最终收益率，最大收益率，最小收益率，波动
    """
    def compute_earn_rates(percent_list:[])->Tuple[float, float,float]:
        BASE_VALUE  = 10000.0
        value = BASE_VALUE
        min_value = value
        max_value = value
        for pct in percent_list:
            value = value + pct * value
            if min_value > value:
                min_value = value
            if max_value < value:
                max_value = value

        return [value / BASE_VALUE - 1, max_value / BASE_VALUE - 1,min_value / BASE_VALUE - 1]

    def to_bars(holdBarList:[]):
        barList = []
        close_price = None
        for holdBar in holdBarList:
            if close_price is None:
                barList.append(holdBar.toBarData())
                close_price = holdBar.close_price
            else:
                # barList.append(holdBar.toBarData())
                bar = holdBar.toBarData(new_open_price=close_price);
                barList.append(bar)
                close_price = bar.close_price
        return barList

    def to_vt_symbol(code: str) -> str:
        if (not code.__contains__(".")):
            symbol = f"{code}.{Exchange.SZSE.value}"
            if code.startswith("6"):
                symbol = f"{code}.{Exchange.SSE.value}"
            return symbol
        return code

    def to_jq_symbol(code: str) -> str:
        # 沪深300指数
        if code.startswith("000300"):
            return "000300.XSHG"

        if code.endswith(".XSHG") \
            or code.endswith(".XSHE"):
            return code

        jq_code = jq.normalize_code(code)

        if jq_code is None:
            if code.startswith("6"):
                return f"{code}.XSHG"
            else:
                return f"{code}.XSHE"
        return jq_code

    def getExchange(code: str) -> Exchange:
        if code.startswith("6"):
            return Exchange.SSE
        return Exchange.SZSE

    def is_same_day(d1: datetime, d2: datetime) -> bool:
        return d1.day == d2.day and d1.month == d2.month and d1.year == d2.year

    def is_same_minitue(d1: datetime, d2: datetime) -> bool:
        return utils.is_same_day(d1, d2) and d1.hour == d2.hour and d1.minute == d2.minute

    def is_same_time(d1: datetime, d2: datetime,deltaMinitue:int = 0,deltaSecond:int = 0) -> bool:
        deltaMinitue = abs(deltaMinitue)
        deltaSecond = abs(deltaSecond)
        start = d1 - timedelta(minutes=deltaMinitue) -  timedelta(seconds=deltaSecond)
        if(d2 < start):
            return False
        end = d1 + timedelta(minutes=deltaMinitue) +  timedelta(seconds=deltaSecond)
        if d2 > end:
            return False
        return True

    def isEqualInt(v1:int,v2:int,delta:int)->bool:
        delta = abs(delta)
        if v2 < v1 - delta:
            return False
        if(v2 > v1 + delta):
            return False
        return True

    def isEqualFloat(v1: float, v2: float, delta: float) ->bool:
        delta = abs(delta)
        if v2 < v1 - delta:
            return False
        if (v2 > v1 + delta):
            return False
        return True

    def keep_3_float(value:float) -> float:
        return int(value * 1000) / 1000

    def to_start_date(d: datetime) -> datetime:
        return datetime(year=d.year, month=d.month, day=d.day, hour=00, minute=00, second=00)

    def to_end_date(d: datetime) -> datetime:
        return datetime(year=d.year, month=d.month, day=d.day, hour=23, minute=59, second=59)

    """
    展开参数map，如下
      originParams = {
          'wwf':[1,None,5],
          'zx':['sd',None,'dd']
      }
      将originParams展开为列表模式。
      {'wwf': 1, 'zx': 'sd'}
      {'wwf': 1, 'zx': None}
      {'wwf': 1, 'zx': 'dd'}
      {'wwf': None, 'zx': 'sd'}
      {'wwf': None, 'zx': None}
      {'wwf': None, 'zx': 'dd'}
      {'wwf': 5, 'zx': 'sd'}
      {'wwf': 5, 'zx': None}
      {'wwf': 5, 'zx': 'dd'}
      """
    def expandParamsMap(params: {})->[]:
        paramList = []
        utils.__expandParamMapList(paramList, params, {}, list(params.keys()), 0)
        return paramList

    def __expandParamMapList(list: [], originParams: {}, param: {}, keyList: [], index):
        size = len(keyList)
        if index >= size:
            list.append(param.copy())
            return
        key = keyList[index]
        values = originParams[key]
        for value in values:
            param[key] = value
            utils.__expandParamMapList(list, originParams, param, keyList, index + 1)

    @classmethod
    def changeTime(cls, dt:datetime, year:int =None,month = None, day = None, hour:int = None,minute:int = None,second = None):
        if year is None:
            year = dt.year
        if month is None:
            month = dt.month
        if day is None:
            day = dt.day
        if hour is None:
            hour = dt.hour
        if minute is None:
            minute = dt.minute
        if second is None:
            second = dt.second

        return datetime(year=year,month=month,day=day,hour=hour,minute=minute,second=second)