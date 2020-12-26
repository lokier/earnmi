import json

from playhouse.shortcuts import dict_to_model, model_to_dict

from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from datetime import datetime, timedelta
import talib

from earnmi.model.OpOrder2 import OpOrderDataBase, OpOrder2, OpLog

datetime = datetime.now()
dt = datetime - timedelta(days = 60)



