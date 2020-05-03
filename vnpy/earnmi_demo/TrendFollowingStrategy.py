from datetime import datetime

from vnpy.app.portfolio_strategy import BacktestingEngine
from vnpy.app.portfolio_strategy.strategies.trend_following_strategy import TrendFollowingStrategy
from vnpy.trader.constant import Interval

#%%
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbols=["IF888.CFFEX"],
    interval=Interval.MINUTE,
    start=datetime(2010, 2, 1),
    end=datetime(2020, 4, 30),
    rates={"IF888.CFFEX": 0.3/10000},
    slippages={"IF888.CFFEX": 0.2},
    sizes={"IF888.CFFEX": 300},
    priceticks={"IF888.CFFEX": 0.2},
    capital=1_000_000,
)
engine.add_strategy(TrendFollowingStrategy, {})


#%%
engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()