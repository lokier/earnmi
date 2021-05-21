from datetime import datetime

import talib

from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarManager import BarManager
from earnmi.data.BarStorage import BarV2Storage
from earnmi.data.BarTransform import BarTransformHandle, BarTransformStorage
from earnmi.model.bar import BarData, BarV2
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval
import numpy as np
import numpy as np

_A_DAY = 24 * 60 * 60

"""
BarV2变换器
"""
class RankTransformHandle(BarTransformHandle):

    def __init__(self,driver:BarDriver):
        self.driver = driver

    def get_name(self):
        return "RankTransformHandle"

    def get_symbol_lists(self):
        return self.driver.get_symbol_lists()

    def onTransform(self,manager:BarManager,storage:BarTransformStorage):
        ##清理数据
        # storage.clear()
        #
        # self._generate_rank_value(manager,storage)
        # self._generate_rank_yx(manager,storage)
        barV2Source = manager.createBarSoruce(storage.getBarDriver())
        rank_values = []
        rank_f = []
        for symbol, bars in barV2Source.itemsSequence():
            for bar in bars:
                if not bar.extra.rank_y3 is None:
                    rank_values.append(bar.extra.rank_value)
                    rank_f.append(bar.extra.rank_y3)
        rank_values = np.array(rank_values) * 100
        rank_f = np.array(rank_f) * 1000
        print(f"{rank_values[0:100]}")
        print(f"{rank_f[0:100]}")

        ret = talib.CORREL(rank_values, rank_f, timeperiod=100)
        print(f"ic:{ret[-1]},size={len(rank_f)}")

        ret = talib.CORREL(rank_values[0:200], rank_f[0:200], timeperiod=100)
        print(f"ic:{ret[-1]},size={len(rank_f)}")

    def _generate_rank_value(self,manager:BarManager,storage:BarTransformStorage):
        targetDriver = self.driver
        barSource = manager.createBarSoruce(targetDriver)

        ###基础数据加工: rank_value
        for datetime,bars in barSource.itemsParallel():
            _max_pct,_min_pct = self.find_max_min_pct(bars)
            barv2_list = []
            for bar in bars:
                _pct = self.getPct(bar)
                barV2 = storage.createBarV2(bar)
                rank_value = self.compute_rank_value(_pct,_max_pct,_min_pct)  ##涨幅排名数据
                assert rank_value >= -1
                assert  rank_value <=1
                barV2.extra.rank_value = rank_value
                barv2_list.append(barV2)
            storage.save_bar_data(barv2_list)
            print(f"date: {datetime} ,size = {len(barv2_list)}")

    def _generate_rank_yx(self,manager:BarManager,storage:BarTransformStorage):
        barV2Source = manager.createBarSoruce(storage.getBarDriver())
        """
        + rank_y3: 3天后的收益: y = 3天后[(high_price + close_price)/2] - 当天|open_price
        """
        for symbol, bars in barV2Source.itemsSequence():
            barv2_list = []
            bar_size = len(bars)
            for i in range(0, bar_size):
                bar = bars[i]
                barV2 = storage.createBarV2(bar)
                barV2.extra.rank_y3 = np.nan
                barV2.extra.rank_y7 = np.nan
                barV2.extra.rank_y14 = np.nan
                if i + 3 < bar_size:
                    barV2.extra.rank_y3 = self.computeProfitPct(bars[i + 1:i + 4])
                if i + 7 < bar_size:
                    barV2.extra.rank_y7 = self.computeProfitPct(bars[i + 1:i + 8])
                if i + 14 < bar_size:
                    barV2.extra.rank_y14 = self.computeProfitPct(bars[i + 1:i + 15])
                barv2_list.append(barV2)
            storage.save_bar_data(barv2_list)
            print(f"symbol: {symbol} ,size = {len(bars)}")

    def computeProfitPct(self,bars):
        "y = 3天后[(high_price + close_price)/2] - 当天|open_price"
        high_price = bars[0].high_price
        start_price = bars[0].open_price
        end_price = bars[-1].close_price
        for i in range(1,len(bars)):
            high_price = max(high_price,bars[i].high_price)

        return ((high_price + end_price) / 2 - start_price) / start_price


    def find_max_min_pct(self,bars:[]):
        _max = -10000
        _min = 10000
        assert (len(bars)> 0)
        for bar in bars:
            pct =  self.getPct(bar)
            if pct > _max:
                _max = pct
            if pct < _min:
                _min = pct
        return _max,_min

    def getPct(self,bar:BarData):
        return (bar.close_price - bar.open_price) / bar.open_price


    def compute_rank_value(self,pct,max_pct,min_pct):
        """
        行业当天涨幅排名值，值范围在[-1,1],如果靠近1，说明行业涨幅排名第一，靠近-1说明行业排名最后
        """
        v = (pct - min_pct) / (max_pct - min_pct)
        return  v * 2 - 1

