from dataclasses import dataclass
from datetime import datetime, timedelta
from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from earnmi.strategy.StockStrategy import StockStrategy, Portfolio
from vnpy.trader.constant import Direction
from vnpy.trader.object import TradeData

"""
  当macd的bar:
    检测当macd出现金叉到死叉后,到最大盈利点是多少，， 盈利8%多久，盈利12%多久，盈利18%多久，超过20%多久
    [出现金叉第二天买入，出现死叉第二天卖出]到达最大盈利点经过耗时多久
"""

@dataclass
class Long_Data_Item:
    symbol:str
    start_time:datetime  #金叉出现时间
    start_price:float
    end_time:datetime = None  #死叉出现时间
    end_price:float = -1
    max_price:float = -1
    max_price_time:datetime = None
    max_price_day:int = -1  # 到底最高价经过多长时间
    max_pnl_3_day:int = -1  # 盈利3%多久
    max_pnl_5_day:int = -1  # 盈利5%多久
    max_pnl_7_day:int = -1  # 盈利7%多久
    max_pnl_9_day:int = -1  # 盈利9%多久
    max_pnl_11_day:int = -1  # 盈利11%多久
    max_pnl_13_day:int = -1  # 盈利13%多久
    max_pnl_15_day:int = -1  # 盈利15%多久
    max_pnl_17_day:int = -1  # 盈利17%多久
    max_pnl_19_day:int = -1  # 盈利19%多久
    max_pnl_21_more_day:int = -1  # 盈利21%多久
    to_deal_cross_day:int = 0  #到底死叉的时间

@dataclass
class Short_Data_Item:
    symbol: str
    start_time: datetime  # 金叉出现时间
    start_price: float
    end_time: datetime = None  # 死叉出现时间
    end_price: float = -1
    min_price: float = -1
    min_price_time: datetime = None
    min_price_day: int = -1  # 到底最高价经过多长时间
    min_pnl_3_day: int = -1  # 盈利3%多久
    min_pnl_5_day: int = -1  # 盈利5%多久
    min_pnl_7_day: int = -1  # 盈利7%多久
    min_pnl_9_day: int = -1  # 盈利9%多久
    min_pnl_11_day: int = -1  # 盈利11%多久
    min_pnl_13_day: int = -1  # 盈利13%多久
    min_pnl_15_day: int = -1  # 盈利15%多久
    min_pnl_17_day: int = -1  # 盈利17%多久
    min_pnl_19_day: int = -1  # 盈利19%多久
    min_pnl_21_more_day: int = -1  # 盈利21%多久
    to_deal_cross_day: int = 0  # 到底死叉的时间



class macd(StockStrategy):

    def __init__(self):
       pass
    codes = ["300004"]

    long_data_item_list = []   #数据
    long_data_item_activie = {}

    def on_create(self):
        """
        决策初始化.
        """
        self.write_log("on_create")

        self.market = MarketImpl()
        for code in self.codes:
            self.market.addNotice(code)

        pass

    def on_destroy(self):
        """
            决策结束.（被停止之后）
        """
        self.write_log("on_destroy")
        pass

    def on_market_prepare_open(self,protfolio:Portfolio,today:datetime):
        """
            市场准备开始（比如：竞价）.
        """
        indicator = Indicator(40)
        for code in self.codes:
            bars = self.market.getHistory().getKbars(code, 100);
            actvity_data_item = self.long_data_item_activie.get(code)
            indicator.update_bar(bars)
            dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True);

            if actvity_data_item is None:
                ##等待金叉买入
                if (macd_bar[-1] >= 0 and macd_bar[-2] <= 0):
                    targetPrice = bars[-1].close_price * 1.01  # 上一个交易日的收盘价作为买如价
                    protfolio.buy(code, targetPrice, 1)
            else:
                ##等待死叉卖出
                if (macd_bar[-1] <= 0 and macd_bar[-2] >=0):
                    targetPrice = bars[-1].close_price * 0.99  # 上一个交易日的收盘价作为买如价
                    protfolio.sell(code, targetPrice, 1)


        pass

    def on_trade(self, trade: TradeData):
        if trade.direction == Direction.LONG:
            #买入
            old_data_item = self.long_data_item_activie.get(trade.symbol)
            assert  old_data_item is None
            data_item = Long_Data_Item(symbol=trade.symbol, start_price=trade.price, start_time=trade.datetime)
            self.long_data_item_activie[trade.symbol] = data_item
        elif trade.direction == Direction.SHORT:
            #卖出
            data_item:Long_Data_Item = self.long_data_item_activie.pop(trade.symbol)
            assert not data_item is None
            data_item.end_time = trade.datetime
            data_item.end_price = trade.price
            self.__update_data_item(data_item)
            self.long_data_item_list.append(data_item)



    def __update_data_item_all(self):
        for data_item in self.long_data_item_activie.values():
            self.__update_data_item(data_item)


    def __update_data_item(self, data_item:Long_Data_Item):
        today = self.market.getToday()
        delta_day = (today - data_item.start_time).days

        if data_item.end_time is None:
           today_bar = self.market.getRealTime().getKBar(data_item.symbol)
           max_price = today_bar.high_price
        else:
           max_price = data_item.end_price
           data_item.to_deal_cross_day = delta_day

        if max_price > data_item.max_price:
            data_item.max_price = max_price
            data_item.max_price_time = today
            data_item.max_price_day = delta_day

        delta_pnl = (data_item.max_price - data_item.start_price) / data_item.start_price

        if(delta_pnl >= 0.03 and data_item.max_pnl_3_day < 0):
            data_item.max_pnl_3_day = delta_day

        if (delta_pnl >= 0.05 and data_item.max_pnl_5_day < 0):
            data_item.max_pnl_5_day = delta_day

        if (delta_pnl >= 0.07 and data_item.max_pnl_7_day < 0):
            data_item.max_pnl_7_day = delta_day

        if (delta_pnl >= 0.09 and data_item.max_pnl_9_day < 0):
            data_item.max_pnl_9_day = delta_day

        if (delta_pnl >= 0.11 and data_item.max_pnl_11_day < 0):
            data_item.max_pnl_11_day = delta_day

        if (delta_pnl >= 0.13 and data_item.max_pnl_13_day < 0):
            data_item.max_pnl_13_day = delta_day

        if (delta_pnl >= 0.15 and data_item.max_pnl_15_day < 0):
            data_item.max_pnl_15_day = delta_day

        if (delta_pnl >= 0.17 and data_item.max_pnl_17_day < 0):
            data_item.max_pnl_17_day = delta_day

        if (delta_pnl >= 0.19 and data_item.max_pnl_19_day < 0):
            data_item.max_pnl_19_day = delta_day

        if (delta_pnl >= 0.21 and data_item.max_pnl_21_more_day < 0):
            data_item.max_pnl_21_more_day = delta_day




    def on_market_open(self,protfolio:Portfolio):
        """
            市场开市.
        """



    def on_market_prepare_close(self,protfolio:Portfolio):
        """
            市场准备关市.
        """

        pass

    def on_market_close(self, protfolio:Portfolio):
        """
            市场关市.
        """
        self.__update_data_item_all()
        pass

    def on_bar_per_minute(self, time: datetime, protfolio:Portfolio):
        """
            市场开市后的每分钟。
        """
        pass


if __name__ == "__main__":
    from vnpy.app.portfolio_strategy import BacktestingEngine
    from earnmi.data.import_tradeday_from_jqdata import TRAY_DAY_VT_SIMBOL
    from earnmi.strategy.StockStrategyBridge import StockStrategyBridge
    from vnpy.trader.constant import Interval, Direction

    engine = BacktestingEngine()

    start = datetime(2019, 2, 23)
    end = datetime(2020, 4, 24)

    engine.set_parameters(
        vt_symbols=[TRAY_DAY_VT_SIMBOL],
        interval=Interval.DAILY,
        start=start,
        end=end,
        rates={TRAY_DAY_VT_SIMBOL: 0.3 / 10000},  # 交易佣金
        slippages={TRAY_DAY_VT_SIMBOL: 0.1},  # 滑点
        sizes={TRAY_DAY_VT_SIMBOL: 100},  # 一手的交易单位
        priceticks={TRAY_DAY_VT_SIMBOL: 0.01},  # 四舍五入的精度
        capital=1_000_000,
    )
    strategy = macd()
    engine.add_strategy(StockStrategyBridge, {"strategy": strategy})

    # %%
    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    engine.calculate_statistics()

    for data_item in strategy.long_data_item_list:
        print(data_item)
        # print(f"symbol={data_item.symbol},start_price={data_item.buy_price},max_price={data_item.max_price},end_price={data_item.end_price}"
        #       f"")