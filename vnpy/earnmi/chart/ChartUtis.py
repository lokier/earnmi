import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

import mplfinance as mpf
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np

from earnmi.chart.Chart import Chart
from earnmi.model.CollectData import CollectData

from earnmi.uitl.BarUtils import BarUtils
from vnpy.trader.constant import Exchange, Interval
from werkzeug.routing import Map

from earnmi.chart.Indicator import Indicator
import abc

from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData

class ChartUtils:

    @staticmethod
    def show_collect_data(data:CollectData):
        bars = []
        bars.extend(data.occur_bars)
        bars.extend(data.unkown_bars)
        chart = Chart()
        chart.show(bars)
