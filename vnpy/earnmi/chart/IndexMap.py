from typing import Tuple

from vnpy.trader.utility import ArrayManager


class Indexs:

    window_size = 1

    def __init__(self,window_size:int):
        self.window_size = window_size

    """
    设置数据
    """
    def setBarData(self, bars: list):
        self.barDatas = bars

    def macd(self) ->Tuple[float, float, float]:

        am = ArrayManager(self.window_size * 2)
        am.update_bar()

        am.macd()

        pass