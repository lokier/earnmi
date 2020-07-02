from collections import defaultdict
from datetime import datetime, timedelta

from pandas import DataFrame

from earnmi.strategy.StockStrategy import BackTestContext
from vnpy.trader.constant import Interval, Exchange, Status, Direction

class utils:
    def to_vt_symbol(code: str) -> str:
        if (not code.__contains__(".")):
            symbol = f"{code}.{Exchange.SZSE.value}"
            if code.startswith("6"):
                symbol = f"{code}.{Exchange.SSE.value}"
            return symbol
        return code

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


    def calculate_result(bactTest:BackTestContext):
        """"""

        if not bactTest.trades:
            print("成交记录为空，无法计算")
            return

        ##计算每天的结果。

        for daily_result in self.daily_results.values():
            fields = [
                "date", "trade_count", "turnover",
                "commission", "slippage", "trading_pnl",
                "holding_pnl", "total_pnl", "net_pnl"
            ]
            for key in fields:
                value = getattr(daily_result, key)
                results[key].append(value)

        self.daily_df = DataFrame.from_dict(results).set_index("date")

        self.output("逐日盯市盈亏计算完成")
        return daily_df


    def __update_daily_close(self, price: float):
        """"""
        d = self.datetime.date()

        daily_result = self.daily_results.get(d, None)
        if daily_result:
            daily_result.close_price = price
        else:
            self.daily_results[d] = DailyResult(d, price)