from typing import Any

from vnpy.trader.constant import Direction

from vnpy.trader.object import TradeData
import numpy as np
from vnpy.app.portfolio_strategy import BacktestingEngine


class RaoUtils:
    """
    股票市值编码：
    0    0
	10亿：  1
	25亿：  2
    78：  2
    78： 3
    117
	175
	262
	393
	590
	885
	1327
	1990
	2985
	4448
	6672
	10008
    """
    def encodeMarketValue(value:float)->int:
        value = value / 100000000
        __encode_list = [0,10,25,78,117,175,262,393,590,885,1327,1990,2985,4448,6672,10008]
        size = len(__encode_list)
        for i in range(1,size):
            if value <__encode_list[i]:
                return i - 1
        return size - 1;

    def calculate(engine:BacktestingEngine):
        trades = engine.trades;

        print("\n===============================================================")

        hold_trades = {}

        total_pnl = 0
        cross_cnt = 0  ##交割次数
        cross_cnt_win = 0
        captial_init = 100000000.0
        capital = captial_init
        captial_max = captial_init
        captial_min = captial_init
        for dt, v in trades.items():
            trade: TradeData = v
            trage_tag = "买"
            if (trade.direction == Direction.SHORT):
                trage_tag = "卖"
            print(
                f"{trade.datetime}:order_id={trade.vt_orderid},{trage_tag}:{trade.volume},price:{trade.price},time={trade.time}")

            if trade.direction == Direction.SHORT:
                ###
                buy_trade = hold_trades[trade.vt_symbol]
                assert  buy_trade.volume == trade.volume

                buy_price = buy_trade.price
                sell_price = trade.price
                rate = (sell_price - buy_price) / buy_price

                ###剔除手续费
                rate =  rate - 0.0001 * 2
                capital = capital * (1 + rate)
                ##total_pnl += np.log(rate)
                cross_cnt = cross_cnt + 1

                if rate > 0.00:
                    cross_cnt_win = cross_cnt_win + 1


                if capital > captial_max:
                    captial_max = capital
                if capital < captial_min:
                    captial_min = capital

                pass
            else:
                hold_trades[trade.vt_symbol] = trade
                pass

        pnl =  capital / captial_init - 1

        print(f"完整交割次数:{cross_cnt},  盈利交割个数:{cross_cnt_win},  总盈利: {pnl * 100}%")
