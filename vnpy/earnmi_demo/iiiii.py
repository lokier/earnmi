import string
from datetime import datetime, timedelta
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta
from earnmi.chart.Chart import Chart
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from vnpy.trader.object import BarData



today = datetime.today()

print(today)
