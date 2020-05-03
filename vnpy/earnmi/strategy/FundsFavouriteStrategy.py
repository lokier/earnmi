from typing import List, Dict

from vnpy.app.portfolio_strategy import StrategyTemplate, StrategyEngine
from vnpy.trader.object import TickData, BarData
from vnpy.trader.utility import BarGenerator, ArrayManager


class FundsFavouriteStrategy(StrategyTemplate):
    """"""

    author = "rdm"
    atr_window = 22

    parameters = [
        "atr_window",
        "atr_ma_window",
        "rsi_window",
        "rsi_entry",
        "trailing_percent",
        "fixed_size"
    ]
    variables = [
        "atr_value",
        "atr_ma",
        "rsi_value",
        "rsi_buy",
        "rsi_sell"
    ]

    def __init__(
        self,
        strategy_engine: StrategyEngine,
        strategy_name: str,
        vt_symbols: List[str],
        setting: dict
    ):
        """"""
        super().__init__(strategy_engine, strategy_name, vt_symbols, setting)

        self.vt_symbol = ['300207', '600340']
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        #self.rsi_buy = 50 + self.rsi_entry
        #self.rsi_sell = 50 - self.rsi_entry

        self.load_bars(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        bars = {bar.vt_symbol: bar}
        self.on_bars(bars)

    def on_bars(self, bars: Dict[str, BarData]):
        """"""
        self.cancel_all()

        bar = bars[self.vt_symbol]
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        atr_array = am.atr(self.atr_window, array=True)
        self.atr_value = atr_array[-1]
        self.atr_ma = atr_array[-self.atr_ma_window:].mean()
        self.rsi_value = am.rsi(self.rsi_window)

        pos = self.get_pos(self.vt_symbol)

        if pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.atr_value > self.atr_ma:
                if self.rsi_value > self.rsi_buy:
                    self.buy(self.vt_symbol, bar.close_price + 5, self.fixed_size)
                elif self.rsi_value < self.rsi_sell:
                    self.short(self.vt_symbol, bar.close_price - 5, self.fixed_size)

        elif pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            long_stop = self.intra_trade_high * (1 - self.trailing_percent / 100)

            if bar.close_price <= long_stop:
                self.sell(self.vt_symbol, bar.close_price - 5, abs(pos))

        elif pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            short_stop = self.intra_trade_low * (1 + self.trailing_percent / 100)

            if bar.close_price >= short_stop:
                self.cover(self.vt_symbol, bar.close_price + 5, abs(pos))

        self.put_event()
