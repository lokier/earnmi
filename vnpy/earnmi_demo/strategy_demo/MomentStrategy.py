from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence, Dict

from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from earnmi.strategy.StockStrategy import StockStrategy, Portfolio
from vnpy.trader.constant import Direction, Offset
from vnpy.trader.object import TradeData

"""
  动量指标

"""


class MomentStrategy(StockStrategy):

    def __init__(self):
        pass

    codes = [
             '000069',
             # '000100',
             # '000157',
             # '000166',
             # '000333',
             # '000338',
             # '000425',
             # '000538',
             # '000568',
             # '000596',
             # '000625',
             # '000627',
             # '000651',
             # '000656',
             # '000661',
             # '000671',
             # '000703',
             # '000708',
             # '000709',
             # '000723',
             # '000725',
             # '000728',
             # '000768',
             # '000776',
             # '000783',
             # '000786',
             # '000858',
             # '000860',
             # '000876',
             # '000895',
             # '000938',
             # '000961',
             # '000963',
             # '000977',
             # '001979',
             # '002001',
             # '002007',
             # '002008',
             # '002024',
             # '002027',
             # '002032',
             # '002044',
             # '002050',
             # '002120',
             # '002129',
             # '002142',
             # '002146',
             # '002153',
             # '002157',
             # '002179',
             ]

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

    """
    当 AroonUp大于AroonDown，并且AroonUp大于50，多头开仓；
    当 AroonUp小于AroonDown，或者AroonUp小于50，多头平仓；
    """
    def on_market_prepare_open(self, protfolio: Portfolio, today: datetime):
        """
            市场准备开始（比如：竞价）.
        """
        indicator = Indicator(40)
        for code in self.codes:
            bars = self.market.getHistory().getKbars(code, 100);
            indicator.update_bar(bars)
            aroon_up, aroon_down = indicator.aroon(15)
            need_hold = aroon_up > 50 and aroon_up > aroon_down
            position =  protfolio.getLongPosition(code)

            if need_hold:
                if position.pos_total < 1:
                    tradePrice = bars[-1].close_price * 1.01  # 上一个交易日的收盘价作为买如价
                    protfolio.buy(code,tradePrice,1)
            else:


                if position.pos_total > 0:
                    targetPrice = bars[-1].close_price * 0.99  # 上一个交易日的收盘价作为买如价
                    protfolio.sell(code,targetPrice,position.pos_total/100)

        pass


    def on_market_open(self, protfolio: Portfolio):
        """
            市场开市.
        """

    def on_market_prepare_close(self, protfolio: Portfolio):
        """
            市场准备关市.
        """

        pass

    def on_market_close(self, protfolio: Portfolio):
        """
            市场关市.
        """

        pass

    def on_bar_per_minute(self, time: datetime, protfolio: Portfolio):
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
    strategy = MomentStrategy()
    engine.add_strategy(StockStrategyBridge, {"strategy": strategy})

    # %%
    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    engine.calculate_statistics()

