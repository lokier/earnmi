#%%
from earnmi.data.import_tradeday_from_jqdata import TRAY_DAY_VT_SIMBOL
from earnmi.strategy.StockStrategyBridge import StockStrategyBridge
from earnmi_demo.Strategy1 import Strategy1
from vnpy.app.portfolio_strategy import BacktestingEngine
from vnpy.event import Event
from vnpy.trader.constant import Interval
from datetime import datetime

from vnpy.trader.event import EVENT_LOG


def printLog(event:Event):
    print(event.data)

#%%
engine = BacktestingEngine()


start = datetime(2019, 2, 23)
end = datetime(2019, 4, 24)

engine.set_parameters(
    vt_symbols=[TRAY_DAY_VT_SIMBOL],
    interval=Interval.DAILY,
    start=start,
    end=end,
    rates={TRAY_DAY_VT_SIMBOL:0.3/10000},  #交易佣金
    slippages={TRAY_DAY_VT_SIMBOL:0.1},  # 滑点
    sizes={TRAY_DAY_VT_SIMBOL:100},  #一手的交易单位
    priceticks={TRAY_DAY_VT_SIMBOL:0.01},  #四舍五入的精度
    capital=1_000_000,
)
engine.add_strategy(StockStrategyBridge, { "strategy":Strategy1()})

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