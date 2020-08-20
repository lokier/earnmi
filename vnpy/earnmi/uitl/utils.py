from collections import defaultdict
from datetime import datetime, timedelta

from pandas import DataFrame

from earnmi.strategy.StockStrategy import BackTestContext
from vnpy.trader.constant import Interval, Exchange, Status, Direction
import jqdatasdk as jq

class utils:
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

    def to_start_date(d: datetime) -> datetime:
        return datetime(year=d.year, month=d.month, day=d.day, hour=00, minute=00, second=1)

    def to_end_date(d: datetime) -> datetime:
        return datetime(year=d.year, month=d.month, day=d.day, hour=23, minute=59, second=59)


