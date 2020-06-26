#%%
from earnmi.data.import_tradeday_from_jqdata import TRAY_DAY_VT_SIMBOL
from earnmi.strategy.CtaStrategyBridge import CtaStrategyBridage
from earnmi.strategy.FundsFavouriteStrategy import FundsFavouriteStrategy
from earnmi.strategy.TestMultiStrategy import TestMultiStrategy
from earnmi_demo.Strategy1 import Strategy1
from vnpy.app.cta_strategy.strategies.test_strategy import TestStrategy
from vnpy.event import Event
from vnpy.trader.constant import Interval

from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import (
    AtrRsiStrategy
)
from datetime import datetime

from vnpy.trader.event import EVENT_LOG


def printLog(event:Event):
    print(event.data)

#%%
engine = BacktestingEngine()
#engine.register(EVENT_LOG, printLog)

engine.set_parameters(
    vt_symbol=TRAY_DAY_VT_SIMBOL,
    interval=Interval.DAILY,
    start=datetime(2019, 2, 23),
    end=datetime(2019, 4, 24),
    rate=0.3/10000,
    slippage=0.2,
    size=300,
    pricetick=0.2,
    capital=1_000_000,
)
engine.add_strategy(CtaStrategyBridage, {"strategy":Strategy1()})

#%%
engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()

# setting = OptimizationSetting()
# setting.set_target("sharpe_ratio")
# setting.add_parameter("atr_length", 3, 39, 1)
# setting.add_parameter("atr_ma_length", 10, 30, 1)
#
# engine.run_ga_optimization(setting)