from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence, Dict

from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import Market2Impl
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
        '600196',
        # '600211',
        # '600316',
        # '600764',
        # '600893',
        # '600988',
        # '600989',
        # '601216',
        # '601633',
        # '603737',
        # '600733',
        # '600738',
        # '600877',
        # '602025',
        # '602081',
        # '602151',
        # '602444',
        # '602506',
        # '602541',
        # '602625',
        # '602985',
        # '300123'
             ]

    def on_create(self):
        """
        决策初始化.
        """
        self.write_log("on_create")

        self.market = Market2Impl()
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
            count = 20
            aroon_down,aroon_up = indicator.aroon(count)
            need_hold = aroon_up > 50 and aroon_up > aroon_down
            position =  protfolio.getLongPosition(code)

            if need_hold:
                if position.pos_total < 1:
                    targetPrice = bars[-1].close_price * 1.05  # 上一个交易日的收盘价作为买如价
                    ok = protfolio.buyAtPercentage(code,targetPrice,1)
                    print(f"buy: price = {targetPrice} , {ok}")

            else:
                if position.pos_total > 0:
                    targetPrice = bars[-1].close_price * 0.92  # 上一个交易日的收盘价作为买如价
                    ok = protfolio.sellAll(code,targetPrice)
                    print(f"sell: price = {targetPrice} , {ok}")

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
    from earnmi.uitl.RaoUtils import RaoUtils

    engine = BacktestingEngine()

    ###2020 - 6 - 1  2020 - 8 - 17
    start = datetime(2018, 5, 1)
    #start = datetime(2019, 4, 26)
    end = datetime(2020, 8, 17)

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
    RaoUtils.calculate(engine)

   # RaoUtils.ca(engine)
    from earnmi.chart.Chart import Chart
    chart = Chart()

    chart.show(strategy.backtestContext.bars)

    #engine.show_chart(df)
