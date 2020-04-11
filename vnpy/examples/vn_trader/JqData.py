from datetime import datetime
import pandas as pd
from pandas._libs.tslibs.timestamps import Timestamp

from vnpy.app.data_manager import DataManagerApp, ManagerEngine
from vnpy.event import EventEngine
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import database_manager
from vnpy.trader.engine import MainEngine
symbol ="600519.SSE"
exchange = Exchange.SSE
interval = Interval.MINUTE

datas = database_manager.load_bar_data(
    symbol, exchange, interval,   start=datetime(2020, 3, 23),
    end=datetime(2020, 3, 27),
)


for item in datas:
    print(item)


