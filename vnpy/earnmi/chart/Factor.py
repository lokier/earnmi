
from earnmi.chart.Indicator import Indicator
import numpy as np
import talib

class Factor(object):


    def obv(close:np.ndarray,volume:np.ndarray,period:int=30)->float:
      assert len(close) >= period
      values = talib.OBV(close, volume)
      pass

    def obv_indicator(indicator:Indicator,period:int = 30)->float:
      return Factor.obv(indicator.close,indicator.volume,period)