from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from earnmi.data.BarMarket import BarMarket
from earnmi.model.bar import BarData
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval
import numpy as np
__all__ = [
    # Super-special typing primitives.
    'BarV2',
    'BarV2Market',
]

_A_DAY = 24 * 60 * 60

@dataclass
class BarV2(BarData):
    avg_price: float = 0
    sell_price: float = 0
    buy_price: float = 0
    power_rate: float = 0
    # long_power: float = 0
    # show_power: float = 0
    # watch_power: float = 0

    @staticmethod
    def convert(minute_bars:[],is_grand_volume = True):
        """
        将当天分钟级别的数据转换为BarV2级别的加工数据。
        注意对分钟级别的成交量处理。在这里成交量的处理是已经
        参数:
            is_grand_volume: 分钟级别的成交量是否是累加形式
        """
        first_bar:BarData = minute_bars[0]
        assert first_bar.interval == Interval.MINUTE
        open_price = first_bar.open_price
        high_price = open_price
        low_price = open_price
        close_price = open_price
        volume = first_bar.volume
        __time = first_bar.datetime
        _day_info = int(__time.timestamp() / _A_DAY)
        bar_size = len(minute_bars)
        total_price = (first_bar.open_price + first_bar.close_price) / 2
        for i in range(1,bar_size):
            bar:BarData = minute_bars[i]
            assert __time < bar.datetime
            is_same_day = _day_info == int(bar.datetime.timestamp() / _A_DAY)
            assert is_same_day
            if is_grand_volume:
                ##分钟级别的成交量是否是累加形式
                assert bar.volume >= volume
                ##改成非累加方式
                _minute_volume = bar.volume - volume
                bar.volume = _minute_volume
            volume += bar.volume  ##累计分钟级别成交量
            __time = bar.datetime
            if  high_price < bar.high_price:
                high_price = bar.high_price
            if low_price > bar.low_price:
                low_price = bar.low_price
            close_price = bar.close_price
            total_price+= (bar.open_price + bar.close_price) / 2
        time = datetime(year=__time.year, month=__time.month, day=__time.day, hour=0, minute=0, second=0)

        avg_price = total_price / bar_size
        sell_price_bars = []
        buy_price_bars = []
        for i in range(0, bar_size):
            bar:BarData = minute_bars[i]
            price = (bar.close_price + bar.open_price) / 2
            if price > avg_price:
                sell_price_bars.append(bar)
            elif price < avg_price:
                buy_price_bars.append(bar)

        sell_price_list = np.array([ (bar.open_price + bar.close_price) / 2   for bar in sell_price_bars])
        buy_price_list = np.array([ (bar.open_price + bar.close_price) / 2   for bar in buy_price_bars])
        sell_volume_list = np.array([ bar.volume  for bar in sell_price_bars])
        buy_volume_list = np.array([ bar.volume  for bar in buy_price_bars])

        sell_price = sell_price_list.mean()
        buy_price = buy_price_list.mean()
        power_rate = sell_volume_list.sum() / buy_volume_list.sum()

        dayly_bar = BarV2(
            symbol=first_bar.symbol,
            _driver="barV2",
            datetime=time,
            interval=Interval.DAILY,
            volume=volume,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            open_interest=1.0,
        )
        dayly_bar.avg_price = avg_price
        dayly_bar.sell_price = sell_price
        dayly_bar.buy_price = buy_price
        dayly_bar.power_rate = power_rate
        return dayly_bar


class BarV2Market:

    def __init__(self,market:BarMarket):
        self._market = market

    def get_bars2(self, symbol: str, start: datetime,end:datetime = None,is_grand_volume = True) -> Sequence["BarV2"]:
        start = utils.to_start_date(start)
        end = utils.to_end_date(end)
        mintue_bars = self._market.get_bars(symbol,Interval.MINUTE,start,end)

        if len(mintue_bars) < 1:
            return []
        bar_v2_list = []
        _day_info = int(mintue_bars[0].datetime.timestamp()/_A_DAY)
        _a_day_bars = []
        for m_bar in mintue_bars:
            is_same_day = _day_info == int(m_bar.datetime.timestamp() / _A_DAY)
            if not is_same_day:
                print(f"BarV2.convert:{m_bar.datetime}, size={len(_a_day_bars)}")
                bar_v2 = BarV2.convert(_a_day_bars, is_grand_volume=is_grand_volume)
                print(f"           : {bar_v2}")
                _a_day_bars = []
                _day_info = int(m_bar.datetime.timestamp() / _A_DAY)
                bar_v2_list.append(bar_v2)
            _a_day_bars.append(m_bar)
        return bar_v2_list

    def get_bars(self, symbol: str, start: datetime, end: datetime = None, is_grand_volume=True) -> Sequence["BarV2"]:
        start = utils.to_start_date(start)
        end = utils.to_end_date(end)

        batch_time_list = utils.split_datetime(start, end, 20)
        bar_v2_list = []
        for batch_time in batch_time_list:
            _batch_start, _batch_end = batch_time
            mintue_bars = self._market.get_bars(symbol, Interval.MINUTE, _batch_start, _batch_end)
            if len(mintue_bars) < 1:
                continue
            _day_info = int(mintue_bars[0].datetime.timestamp() / _A_DAY)
            _a_day_bars = []
            for m_bar in mintue_bars:
                is_same_day = _day_info == int(m_bar.datetime.timestamp() / _A_DAY)
                if not is_same_day:
                    bar_v2 = BarV2.convert(_a_day_bars, is_grand_volume=is_grand_volume)
                    _a_day_bars = []
                    _day_info = int(m_bar.datetime.timestamp() / _A_DAY)
                    bar_v2_list.append(bar_v2)
                _a_day_bars.append(m_bar)
            if len(_a_day_bars) > 0:
                bar_v2 = BarV2.convert(_a_day_bars, is_grand_volume=is_grand_volume)
                bar_v2_list.append(bar_v2)
        return bar_v2_list