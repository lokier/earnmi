from dataclasses import dataclass
from datetime import datetime

import numpy as np
import talib

import time
import sched

from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.model.op import OpOrder
from earnmi.uitl.jqSdk import jqSdk



barMap = jqSdk.fethcNowDailyBars(ZZ500DataSource.SZ500_JQ_CODE_LIST)

for code,bar in barMap.items():

    print(f"[{code}]: {bar}")
    pass


