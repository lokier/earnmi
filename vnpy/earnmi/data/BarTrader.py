from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from earnmi.core.analysis.FloatRange import FloatRange

'''
简单买卖交易对象
'''
class SimpleTrader:

    @dataclass
    class _cross_order:
        code:str
        buy_price:float
        updateTime:datetime
        sell_price:float = None
        hold_day = 0 ##交易日

    def __init__(self):
        self.processingOrderMap = defaultdict()
        self.doneOrderList = []

    def hasBuy(self,code):
        return self.processingOrderMap.__contains__(code)

    def buy(self,code:str,price:float,time:datetime):
        if self.hasBuy(code):
            raise RuntimeError(f"code: {code} 已经buy")
        order = SimpleTrader._cross_order(code=code,buy_price=price,updateTime=time)
        self.processingOrderMap[code] = order

    def sell(self,code:str,price:float,time:datetime):
        if not self.hasBuy(code):
            raise RuntimeError(f"code: {code} can't sell")
        order: SimpleTrader._cross_order = self.processingOrderMap.pop(code)
        assert not order is None
        order.sell_price = price
        self.doneOrderList.append(order)
        self.watch(time)

    def resetWatch(self):
        self.processingOrderMap.clear()

    '''
    监听持有天数
    '''
    def watch(self,time:datetime):
        for code,order in self.processingOrderMap.items():
            if not order.updateTime is None:
                days = (time - order.updateTime).days
                ##assert days >=0  ## watch 必须必之前的时间早，否则会有问题
                if days > 0:
                    order.hold_day += 1  ##持有天数+1
                elif days < 0:
                    raise RuntimeError(f"watch的时间必须有顺序：code:{code}, updateTime:{order.updateTime},but time:{time}")
            order.updateTime = time

    def print(self):
        ##计算涨幅比例
        pct_list = []
        hold_day_list = []
        total_hold_day = 0.0
        total_pct = 0.0
        total_size = len(self.doneOrderList)
        for order in self.doneOrderList:
            pct = 100 * (order.sell_price - order.buy_price) / order.buy_price
            pct_list.append(pct)
            total_pct+=pct
            total_hold_day+= order.hold_day
            hold_day_list.append(order.hold_day)
        pct_range = FloatRange(-10, 10, 4)  # 生成浮点值范围区间对象
        hold_day_rang = FloatRange(1, 20, 3)
        print(f"交易总数:{total_size},平均涨幅:%.2f, 平均持有天数:%.2f" % (total_pct/total_size,total_hold_day/total_size))
        print(f"涨幅分布情况:{pct_range.calculate_distribute(pct_list).toStr()}")
        print(f"持有天数分布情况:{hold_day_rang.calculate_distribute(hold_day_list).toStr()}")
