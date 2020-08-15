import random
from typing import Sequence

from earnmi.data.MarketImpl import MarketImpl
from earnmi.data.import_tradeday_from_jqdata import TRAY_DAY_VT_SIMBOL
from earnmi.strategy.StockStrategyBridge import StockStrategyBridge
from earnmi.strategy.StockStrategy import StockStrategy, Portfolio
from earnmi.uitl.utils import utils
from vnpy.app.cta_strategy import StopOrder
from vnpy.trader.constant import Interval, Direction, Offset
from vnpy.app.portfolio_strategy import BacktestingEngine

from datetime import datetime

from vnpy.trader.object import OrderData, TradeData, TickData, BarData


def is_same_day(d1: datetime, d2: datetime) -> bool:
    return d1.day == d2.day and d1.month == d2.month and d1.year == d2.year

def is_same_minitue(d1: datetime, d2: datetime) -> bool:
    return is_same_day(d1,d2) and d1.hour == d2.hour and d1.minute == d2.minute




class StrategyTest(StockStrategy):

    market_open_count = 0
    start_trade_time = None
    end_trade_time =None
    final_valid_capital = 0;
    portfolio: Portfolio = None

    def __init__(
            self,

    ):
       pass

    def on_create(self):
        """
        决策初始化.
        """
        self.market_open_count = 0
        self.market = MarketImpl()


        self.market.addNotice("601318") ##工商银行

        if (not self.backtestContext is None):
            # 从网络上面准备数据。
            self.write_log(f"on_create from backtestEngine, start={self.backtestContext.start_date},end={self.backtestContext.end_date}")
        else:
            self.write_log("on_create")
        pass

    def on_destroy(self):
        """
            决策结束.（被停止之后）
        """
        self.write_log("on_destroy")
        pass

    daily_pre_tick:TickData = None

    def on_market_prepare_open(self,protfolio:Portfolio,toady:datetime):
        self.portfolio = protfolio
        """
            市场准备开始（比如：竞价）.
        """
        assert is_same_day(toady,self.market.getToday())

        if(self.start_trade_time is None) :
            self.start_trade_time = toady
        self.end_trade_time = toady

        self.daily_pre_tick = None

        pass




    def on_market_open(self,protfolio:Portfolio):
        """
            市场开市.
        """
        self.market_open_count = self.market_open_count + 1
        self.on_bar_per_minute_count = 0


        if(is_same_day(datetime(2019, 2, 23),self.market.getToday())):
            ###刚刚开始，没有任何持仓
            assert protfolio.sell("601318",67.15,100) == False
            assert protfolio.cover("601318",67.15,100) == False




        # 中国平安601318 在datetime(2019, 2, 26, 10, 28)时刻，最低到达 low_price=67.15
        # 中国平安601318 在datetime(2019, 2, 27, 9, 48)时刻，最高到达 high_price=68.57
        # 中国平安601318 在datetime(2019, 2, 28)时刻，9点40分左右到最低点66.8，10:47最高到达68.08，然后14:00后面出现新的第二低点67.2-67.4

        self.daily_pre_tick = self.market.getRealTime().getTick("601318")

        if(is_same_day(datetime(2019, 2, 26, 10, 28),self.market.getToday())):
            assert protfolio.buy("601318",67.15,100) == True
            assert protfolio.buy("601318",67.15,100) == False  ##钱不够
            assert protfolio.buy("601318", 67.15, 1) == True
            assert protfolio.buy("601318", 67.10, 1) == True   ##价格过低，能委托成功，但没发成交
            assert protfolio.buy("601318", 66.10, 1) == True   ##价格过低，能委托成功，但没发成交
            assert protfolio.buy("601318", 66.10, 1) == True   ##价格过低，能委托成功，但没发成交



        if (is_same_day(datetime(2019, 2, 27, 9, 48), self.market.getToday())):
            position = protfolio.getLongPosition("601318")
            assert position.is_long == True
            assert position.pos_total == 121*100
            assert position.getPosAvailable() == 121*100  # 昨天买入的，所以今天可用

            assert protfolio.sell("601318", 68.54, 500) == False  ##持仓数不够
            assert protfolio.sell("601318", 68.54, 55) == True
            assert protfolio.sell("601318", 68.54, 46) == True

            assert protfolio.short("601318",68.54,10) == True  ###开始做空买入在datetime(2019, 2, 27, 9, 48)时刻，最高到达 high_price=68.57
            assert protfolio.short("601318", 68.70, 1) == True   ##价格过低，能委托成功，但没发成交


        if (is_same_day(datetime(2019, 2, 28, 10, 48), self.market.getToday())):
            assert protfolio.buy("601318", 67.40, 120) == True

        # 4月23日，清空持仓
        if (is_same_day(datetime(2019, 4, 23), self.market.getToday())):
            longPos = protfolio.getLongPosition("601318")
            shortPos= protfolio.getShortPosition("601318")
            assert longPos.pos_lock == 0 and shortPos.pos_lock == 0 #这个时间是没有冻结的
            #high: 2019 - 04 - 23  13: 47:00: open = 83.77, close = 83.88
            #low: 2019 - 04 - 23  09: 31:00: open = 81.38, close = 81.35
            protfolio.cover("601318",83.77,shortPos.pos_total/100)
            protfolio.sell("601318",81.35,longPos.pos_total/100)

        pass

    def on_market_prepare_close(self,protfolio:Portfolio):
        """
            市场准备关市.
        """
        time = self.market.getToday()
        assert time.hour == 14 and time.minute== 57

        # 最开始datetime(2019, 2, 26, 10, 28)买入100股，由于A股T+1的限制，是不可以当天卖的
        if( utils.is_same_day(datetime(2019, 2, 26, 10, 28),time)):
            assert protfolio.sell("601318",67.00,100) == False


        pass

    def on_market_close(self,protfolio:Portfolio):
        """
            市场关市.
        """
        time = self.market.getToday()
        assert time.hour == 15 and time.minute == 0

        assert self.on_bar_per_minute_count > 200

        self.final_valid_capital = protfolio.getValidCapital()

        # 中国平安601318 在datetime(2019, 2, 26, 10, 28)时刻，最低到达 low_price=67.15
        if utils.is_same_day(datetime(2019, 2, 26),self.market.getToday()):
             #当天已经买入121*100股，持有仓位资金不为0
             assert protfolio.getTotalHoldCapital() > 810700
             position = protfolio.getLongPosition("601318")
             assert  position.is_long == True
             assert  position.pos_total == 121*100
             assert  position.getPosAvailable() == 0  # 因为今天才交易，可用仓位为0
        pass

    sell_time_01_tag = False

    def on_bar_per_minute(self, time: datetime,protfolio:Portfolio):
        """
            市场开市后的每分钟。
        """
        self.on_bar_per_minute_count = self.on_bar_per_minute_count + 1

        assert is_same_minitue(time,self.market.getToday())
        assert time.hour >= 9  #9点后开市
        if(time.hour > 9 or (time.hour==9 and time.minute > 32)):
            ##开市之后的实时信息不应该为none
            bar = self.market.getRealTime().getKBar("601318")
            assert not bar is None

            tickData:BarData = self.market.getRealTime().getTick("601318")
            preTickData:BarData = self.daily_pre_tick

            assert not tickData is None
            assert not preTickData is None
            deltaFloat = preTickData.close_price * 0.015;
            assert utils.isEqualFloat(preTickData.close_price,tickData.open_price,deltaFloat);

        self.daily_pre_tick = self.market.getRealTime().getTick("601318")




        # 中国平安601318
        # 2019-03-25 10:35:00:open = 71.03,close=70.96 一天最高点
        # 2019-03-25 13:12:00:open = 69.97,close=69.79  下午开盘的一个低点
        # 2019-03-25 13:47:00:open = 70.33,close=70.41   下午的一个高点
        sell_time_01 =  datetime(2019, 3, 25, 13, 12)
        if not self.sell_time_01_tag:
            if(utils.is_same_minitue(sell_time_01,time)):
                protfolio.sell("601318",70.35,120)
                self.sell_time_01_tag = True

        #self.write_log(f"     on_bar_per_minute:{time}" )
        # 中国平安601318 在datetime(2019, 2, 26, 10, 28)时刻，最低到达 low_price=67.15
        if(utils.is_same_time(datetime(2019, 2, 26, 10, 28),self.market.getToday(),deltaSecond=30)):
            protfolio.buy("601318", 70.75, 20) ##测试交割价格在67.15附近

        # 中国平安601318 在datetime(2019, 2, 27, 9, 48)时刻，最高到达 high_price=68.57
        if(utils.is_same_time(datetime(2019, 2, 27, 9, 48),self.market.getToday(),deltaSecond=30)):
            protfolio.sell("601318", 60.75, 20) ##测试交割价格在68.57附近

        ###开始做空买入在datetime(2019, 2, 27, 9, 48)时刻，最高到达 high_price=68.57
        # 中国平安601318 在datetime(2019, 2, 28)时刻，9点40分左右到最低点66.8，10:47最高到达68.08，然后14:00后面出现新的第二低点67.2-67.4
        if(utils.is_same_time(datetime(2019, 2, 28, 11, 00),self.market.getToday(),deltaSecond=30)):
           assert protfolio.cover("601318", 67.3, 10) == True ## 11点后开始平仓，以当天第二低价格平仓



        # 4月1日 - 20日随机交易
        today = self.market.getToday()
        #today >= datetime(2019,3,2,0) and today <= datetime(2019,3,20,0) or
        # if  today >= datetime(2019,4,1,0) and today <= datetime(2019,4,20,0):
        #     happen = random.random()
        #     if happen <= 0.1:
        #         self.__randomTrade(protfolio)





    def __randomTrade(self,protfolio:Portfolio):
        happen = random.random()
        code = "601318"
        price = self.market.getRealTime().getTick(code).close_price
        trade_price = price * random.uniform(0.94,1.06)
        volume = random.randint(3,100)
        if happen <= 0.25:
            protfolio.buy(code,trade_price,volume)
        elif happen<=0.5:
            protfolio.sell(code,trade_price,volume)
        elif happen<=0.75:
            protfolio.short(code,trade_price,volume)
        else:
            protfolio.cover(code,trade_price,volume)


    def on_order(self, order: OrderData):
        print(f"{self.market.getToday()}：onOrder: {order}")

    sell_at_2019_2_27_9_48 = False
    buy_at_2019_2_26_10_28 = 0
    sell_at_2019_3_25_13_47 = False
    short_at_2019_2_27_9_48 = False
    cover_at_2019_2_28_14_more = False

    def on_trade(self, trade: TradeData):
        print(f"{self.market.getToday()}：on_trade: {trade}")
        # 中国平安601318 在datetime(2019, 2, 26, 10, 28)时刻，最低到达 low_price=67.15,到达买入价
        # 中国平安601318 在datetime(2019, 2, 27, 9, 48)时刻，最高到达 high_price=68.57，到达卖出价
        # 中国平安601318 在datetime(2019, 3, 25, 13, 10)时刻，从最高价71到一个新底69.75, 后面再到一个新的高点。7.38左右
        # 中国平安601318 在datetime(2019, 2, 28)时刻，9点40分左右到最低点66.8，10:47最高到达68.08，然后14:00后面出现新的第二低点67.2-67.4

        is_buy = trade.direction == Direction.LONG and trade.offset == Offset.OPEN
        is_sell = trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE
        is_short = trade.direction == Direction.SHORT and trade.offset == Offset.OPEN
        is_cover = trade.direction == Direction.LONG and trade.offset == Offset.CLOSE

        if(utils.is_same_time(datetime(2019, 2, 26, 10, 28),self.market.getToday(),deltaSecond=30)):
            if is_buy:
                self.buy_at_2019_2_26_10_28 = self.buy_at_2019_2_26_10_28+1
                assert utils.isEqualFloat(67.15,trade.price,0.5) #成交价格在67.15中间

        if (utils.is_same_day(datetime(2019, 2, 28), self.market.getToday())):
            if is_cover:
                assert self.cover_at_2019_2_28_14_more == False
                self.cover_at_2019_2_28_14_more = True
                assert utils.isEqualFloat(67.3,trade.price,0.5) #成交价格在67.15中间


        if (utils.is_same_time(self.market.getToday(),datetime(2019, 2, 27, 9, 48),deltaMinitue=1,deltaSecond=2)):
            if is_sell:
                self.sell_at_2019_2_27_9_48 = True
                assert utils.isEqualFloat(68.57, trade.price, 0.5)  # 成交价格在68.57中间
            if is_short:
                self.short_at_2019_2_27_9_48 = True
                assert utils.isEqualFloat(68.57, trade.price, 0.5)  # 成交价格在68.57中间


        # 中国平安601318
        # 2019-03-25 10:35:00:open = 71.03,close=70.96 一天最高点
        # 2019-03-25 13:12:00:open = 69.97,close=69.79  下午开盘的一个低点
        # 2019-03-25 13:47:00:open = 70.33,close=70.41   下午的一个高点
        if (utils.is_same_time(self.market.getToday(),datetime(2019, 3, 25, 13, 47),deltaMinitue=4,deltaSecond=2)):
            if is_sell:
                self.sell_at_2019_3_25_13_47 = True
                assert utils.isEqualFloat(70.36, trade.price, 0.5)  # 成交价格在68.57中间

    def on_stop_order(self, stop_order: StopOrder):
        print(f"{self.market.getToday()}：on_stop_order: {stop_order}")


###------------------main---------------------------

engine = BacktestingEngine()
strategy = StrategyTest()

"""
 交易日开始时间 2019, 2, 25 ，交易日结束时间：2019, 4, 24
  
"""
start = datetime(2019, 2, 23)
end = datetime(2019, 4, 24)
slippage = 0.001
commission = 3/10000
capital = 1_000_000
def compute_commission(price:float,volume,slippage:float = slippage,commission:float = commission):
    s = volume * 100 * slippage * price
    commission = volume *  100 * price * commission
    return commission + s

engine.set_parameters(
    vt_symbols=[TRAY_DAY_VT_SIMBOL],
    interval=Interval.DAILY,
    start=start,
    end=end,
    rates={TRAY_DAY_VT_SIMBOL:commission},  #交易佣金
    slippages={TRAY_DAY_VT_SIMBOL:slippage},  # 滑点
    sizes={TRAY_DAY_VT_SIMBOL:100},  #一手的交易单位
    priceticks={TRAY_DAY_VT_SIMBOL:0.01},  #四舍五入的精度
    capital=capital,
)
engine.add_strategy(StockStrategyBridge, { "strategy":strategy})
engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()

print(f"final_valid_capital:{strategy.final_valid_capital}")
print(f"final_total_capital:{strategy.portfolio.getTotalCapital()}")
print(f"total_commison:{strategy.backtestContext.commission}")

total_free = 0.0
total_get = 0.0
total_trade_money = 0.0
long_holding_volume = 0
short_holding_volume = 0
for dt,v in engine.trades.items():
    trade:TradeData = v
    trage_tag = "买"
    if(trade.direction == Direction.SHORT):
        trage_tag = "卖"
    is_buy = trade.direction == Direction.LONG and trade.offset == Offset.OPEN
    is_sell = trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE
    is_short = trade.direction == Direction.SHORT and trade.offset == Offset.OPEN
    is_cover = trade.direction == Direction.LONG and trade.offset == Offset.CLOSE
    total_free += compute_commission(trade.price, trade.volume)
    total_trade_money+= trade.price * trade.volume * 100
    if is_buy:
        total_get -= trade.price * trade.volume * 100
        print(f"[{trade.datetime}] buy: price={trade.price}, volume={trade.volume}")
    if is_sell:
        total_get += trade.price * trade.volume * 100
        print(f"[{trade.datetime}] sell: price={trade.price}, volume={trade.volume}")

    if is_short:
        total_get += trade.price * trade.volume * 100
        print(f"[{trade.datetime}] short: price={trade.price}, volume={trade.volume}")

    elif is_cover:
        total_get -= trade.price * trade.volume * 100
        print(f"[{trade.datetime}] cover: price={trade.price}, volume={trade.volume}")


print(f"total_get:{total_get}, total_free={total_free}, final= {total_get + capital},   pnl= {total_get + capital - total_free}, total_trade_money={total_trade_money}")

assert is_same_day(datetime(year=2019,month=2,day=25),strategy.start_trade_time)
assert is_same_day(datetime(year=2019,month=4,day=24),strategy.end_trade_time)

assert  strategy.market_open_count == 42
assert  strategy.sell_at_2019_2_27_9_48 == True
assert  strategy.buy_at_2019_2_26_10_28 == 3
assert  strategy.sell_time_01_tag == True
assert  strategy.sell_at_2019_3_25_13_47 == True
assert  strategy.short_at_2019_2_27_9_48 == True
assert  strategy.cover_at_2019_2_28_14_more == True

###账号里面没有任何筹码
assert  strategy.portfolio.getLongPosition("601318").pos_total == 0
assert  strategy.portfolio.getShortPosition("601318").pos_total == 0
assert strategy.portfolio.getTotalHoldCapital() < 0.00001


strategy.backtestContext.showChart()

#engine.show_chart()

