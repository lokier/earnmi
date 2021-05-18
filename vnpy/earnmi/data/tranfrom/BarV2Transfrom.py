from datetime import datetime

from earnmi.data.BarManager import BarManager
from earnmi.data.BarStorage import BarV2Storage
from earnmi.data.BarTransform import BarTransfrom
from earnmi.data.BarV2 import BarV2
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval

"""
BarV2变换器
"""
class BarV2Transform(BarTransfrom):


    def onTransform(self,manager:BarManager,storage: BarV2Storage,driver_name:str):
        _A_DAY = 24 * 60 * 60

        ##清理数据
        storage.clean(driver=driver_name)
        targetDriver = self.driver
        barSource = manager.createBarSoruce(targetDriver)

        symbolist = targetDriver.get_symbol_lists()
        for symbol in symbolist:
            start = barSource.start
            end = barSource.end
            batch_time_list = utils.split_datetime(start, end, 20)
            bar_v2_list = []
            for batch_time in batch_time_list:
                _batch_start, _batch_end = batch_time
                mintue_bars = barSource.get_bars(symbol, Interval.MINUTE, _batch_start, _batch_end)
                if len(mintue_bars) < 1:
                    continue
                _day_info = int(mintue_bars[0].datetime.timestamp() / _A_DAY)
                _a_day_bars = []
                for m_bar in mintue_bars:
                    is_same_day = _day_info == int(m_bar.datetime.timestamp() / _A_DAY)
                    if not is_same_day:
                        bar_v2 = BarV2.convert(_a_day_bars, is_grand_volume=True)
                        _a_day_bars = []
                        _day_info = int(m_bar.datetime.timestamp() / _A_DAY)
                        bar_v2_list.append(bar_v2)
                    _a_day_bars.append(m_bar)
                if len(_a_day_bars) > 0:
                    bar_v2 = BarV2.convert(_a_day_bars, is_grand_volume=True)
                    bar_v2_list.append(bar_v2)
            ###
            storage.save_bar_data(bar_v2_list)
