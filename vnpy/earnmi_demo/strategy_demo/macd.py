from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence, Dict

from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from earnmi.strategy.StockStrategy import StockStrategy, Portfolio
from vnpy.trader.constant import Direction, Offset
from vnpy.trader.object import TradeData

"""
  当macd的bar:
    检测当macd出现金叉到死叉后,到最大盈利点是多少，， 盈利8%多久，盈利12%多久，盈利18%多久，超过20%多久
    [出现金叉第二天买入，出现死叉第二天卖出]到达最大盈利点经过耗时多久
"""

@dataclass
class Long_Item:
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
    duration_days =-1

@dataclass
class Short_Item:
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
    duration_days =-1



class macd(StockStrategy):

    def __init__(self):
       pass
    codes = ["300004"]

    activity_long_dict:Dict[str,Long_Item] = {}
    activity_short_dict:Dict[str,Short_Item] = {}
    long_datas:Sequence["Long_Item"] = []
    short_datas:Sequence["Short_Item"] = []


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
            indicator.update_bar(bars)
            dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True);

                ##金叉出现
            if (macd_bar[-1] >= 0 and macd_bar[-2] <= 0):
                tradePrice = bars[-1].close_price * 1.01  # 上一个交易日的收盘价作为买如价
                protfolio.buy(code, tradePrice, 1)
                protfolio.cover(code,tradePrice,1)  ##平仓做空
                ##死叉出现
            if (macd_bar[-1] <= 0 and macd_bar[-2] >=0):
                targetPrice = bars[-1].close_price * 0.99  # 上一个交易日的收盘价作为买如价
                protfolio.sell(code, targetPrice, 1)
                protfolio.short(code, targetPrice, 1)  ##开仓做空



        pass

    def on_trade(self, trade: TradeData):
        is_buy = trade.direction == Direction.LONG and trade.offset == Offset.OPEN
        is_sell = trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE
        is_short = trade.direction == Direction.SHORT and trade.offset == Offset.OPEN
        is_cover = trade.direction == Direction.LONG and trade.offset == Offset.CLOSE

        today = self.market.getToday()
        if is_buy:
            long_data = Long_Item(symbol=trade.symbol,start_time=today,start_price=trade.price)
            self.activity_long_dict[trade.symbol] = long_data
            self.__update_long_max_price(trade.symbol,trade.price)
        elif is_sell:
            self.__update_long_max_price(trade.symbol,trade.price)
            long_data = self.activity_long_dict.get(trade.symbol)
            if not long_data is None:
                long_data.end_time = today
                long_data.end_price = trade.price
                long_data.duration_days = (today - long_data.start_time).days
                self.long_datas.append(long_data)
                del self.activity_long_dict[trade.symbol]
        elif is_short:
            short_data = Short_Item(symbol=trade.symbol, start_time=today, start_price=trade.price)
            self.activity_short_dict[trade.symbol] = short_data
            self.__update_short_min_price(trade.symbol,trade.price)

        elif is_cover:
            self.__update_short_min_price(trade.symbol,trade.price)
            short_data = self.activity_short_dict.get(trade.symbol)
            if not short_data is None:
                short_data.end_time = today
                short_data.end_price = trade.price
                short_data.duration_days = (today - short_data.start_time).days
                self.short_datas.append(short_data)
                del self.activity_short_dict[trade.symbol]

    def __update_long_max_price(self,code:str,max_price:float):
        data_item = self.activity_long_dict.get(code)
        if data_item is None:
            return
        today = self.market.getToday()
        delta_day = (today - data_item.start_time).days
        if max_price > data_item.max_price:
            data_item.max_price = max_price
            data_item.max_price_time = today
            data_item.max_price_day = delta_day
            delta_pnl = (data_item.max_price - data_item.start_price) / data_item.start_price
            if (delta_pnl >= 0.03 and data_item.max_pnl_3_day < 0):
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

    def __update_short_min_price(self, code:str, min_price:float):
        data_item:Short_Item = self.activity_short_dict.get(code)
        if data_item is None:
            return
        today = self.market.getToday()
        delta_day = (today - data_item.start_time).days
        if min_price < data_item.min_price:
            data_item.min_price = min_price
            data_item.min_price_time = today
            data_item.min_price_day = delta_day
            delta_pnl = (data_item.min_price - data_item.start_price) / data_item.start_price
            if (delta_pnl >= 0.03 and data_item.min_pnl_3_day < 0):
                data_item.min_pnl_3_day = delta_day

            if (delta_pnl >= 0.05 and data_item.min_pnl_5_day < 0):
                data_item.min_pnl_5_day = delta_day

            if (delta_pnl >= 0.07 and data_item.min_pnl_7_day < 0):
                data_item.min_pnl_7_day = delta_day

            if (delta_pnl >= 0.09 and data_item.min_pnl_9_day < 0):
                data_item.min_pnl_9_day = delta_day

            if (delta_pnl >= 0.11 and data_item.min_pnl_11_day < 0):
                data_item.min_pnl_11_day = delta_day

            if (delta_pnl >= 0.13 and data_item.min_pnl_13_day < 0):
                data_item.min_pnl_13_day = delta_day

            if (delta_pnl >= 0.15 and data_item.min_pnl_15_day < 0):
                data_item.min_pnl_15_day = delta_day

            if (delta_pnl >= 0.17 and data_item.min_pnl_17_day < 0):
                data_item.min_pnl_17_day = delta_day

            if (delta_pnl >= 0.19 and data_item.min_pnl_19_day < 0):
                data_item.min_pnl_19_day = delta_day

            if (delta_pnl >= 0.21 and data_item.min_pnl_21_more_day < 0):
                data_item.min_pnl_21_more_day = delta_day



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
        for code in self.codes:
            bar  = self.market.getRealTime().getKBar(code)
            self.__update_long_max_price(code,bar.high_price)
            self.__update_short_min_price(code,bar.low_price)

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

    print(f"trade size:{len(engine.trades)}")

    print("============long_data==========")
    long_columns =["symbol","start_time","end_time","duration","max_price","max_price_day",
                   "pnl_3_day","pnl_5_day","pnl_7_day","pnl_9_day","pnl_11_day","pnl_13_day",
                   "pnl_15_day","pnl_17_day","pnl_19_day","pnl_21_more_day"];
    long_data = []
    for data_item in strategy.long_datas:
        long_item = [data_item.symbol,data_item.start_time,data_item.end_time,data_item.duration_days,data_item.max_price,data_item.max_pnl_3_day,
                     data_item.max_pnl_3_day,data_item.max_pnl_5_day,data_item.max_pnl_7_day,data_item.max_pnl_9_day,data_item.max_pnl_11_day,data_item.max_pnl_13_day,
                     data_item.max_pnl_15_day,data_item.max_pnl_17_day,data_item.max_pnl_19_day,data_item.max_pnl_21_more_day]
        long_data.append(long_item)
        print(data_item)

    print("============short_data==========")
    for data_item in strategy.short_datas:
        print(data_item)

import pandas as pd
import numpy as np
df = pd.DataFrame(long_data,columns=long_columns)
df.to_excel(excel_writer="tmp.xlsx",index=False,encoding='utf-8')