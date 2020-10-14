from datetime import datetime, timedelta
from functools import cmp_to_key
from typing import Sequence

import pandas as pd
import numpy as np
import sklearn
from sklearn import model_selection
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
import pickle


from earnmi.data.SWImpl import SWImpl
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineImpl import SWDataSource
from earnmi.model.CoreEngineRunner import CoreEngineRunner
from earnmi.model.PredictData2 import PredictData
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData

if __name__ == "__main__":
    dirName = "mdoels/predict_current_sw_top2"


    trainDataSouce = SWDataSource( start = datetime(2015, 7, 1),end = datetime(2020, 8, 20))
    from earnmi.model.EngineModel2KAlgo1 import EngineModel2KAlgo1
    strategy = EngineModel2KAlgo1()
    engine = CoreEngine.create(dirName,strategy,trainDataSouce)
    #engine = CoreEngine.load(dirName,strategy)
    runner = CoreEngineRunner(engine)

    dimeValues = [885,884,8628,1061,2822,1060,710,708,1062,886,1063,887,8630,577,1072,1240,1412,1281,882,1105]
    runner.computeSWLatestTop(strategy,dimenValues = dimeValues)
    #runner.backtest(testDataSouce,strategy,limit=99999)