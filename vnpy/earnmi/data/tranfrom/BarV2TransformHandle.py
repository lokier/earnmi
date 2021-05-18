from datetime import datetime

from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarManager import BarManager
from earnmi.data.BarStorage import BarV2Storage
from earnmi.data.BarTransform import BarTransformHandle
from earnmi.model.bar import BarData, BarV2
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval
import numpy as np

_A_DAY = 24 * 60 * 60


"""
BarV2变换器
"""
class BarV2TransformHandle(BarTransformHandle):

    def __init__(self,driver:BarDriver):
        self.driver = driver

    def get_name(self):
        return "BarV2Transform"

    def get_symbol_lists(self):
        return self.driver.get_symbol_lists()

    def onTransform(self,manager:BarManager,storage: BarV2Storage,driver_name:str):
        _A_DAY = 24 * 60 * 60

        ##清理数据
        storage.clean(driver=driver_name)
        targetDriver = self.driver
        barSource = manager.createBarSoruce(targetDriver)

        symbolist = targetDriver.get_symbol_lists()
        for symbol in symbolist:
            print(f"start transform: {symbol}")

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
                        bar_v2 = BarV2TransformHandle.convert(_a_day_bars,driver_name, is_grand_volume=True)
                        _a_day_bars = []
                        _day_info = int(m_bar.datetime.timestamp() / _A_DAY)
                        bar_v2_list.append(bar_v2)
                    _a_day_bars.append(m_bar)
                if len(_a_day_bars) > 0:
                    bar_v2 = BarV2TransformHandle.convert(_a_day_bars, driver_name,is_grand_volume=True)
                    bar_v2_list.append(bar_v2)
            ###
            storage.save_bar_data(bar_v2_list)
            print(f"end transform: size =  {len(bar_v2_list)}")
            break;

    @staticmethod
    def convert(minute_bars: [], driver_name:str,is_grand_volume=True):
        """
        将当天分钟级别的数据转换为BarV2级别的加工数据。
        注意对分钟级别的成交量处理。在这里成交量的处理是已经
        参数:
            is_grand_volume: 分钟级别的成交量是否是累加形式
        """
        first_bar: BarData = minute_bars[0]
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
        for i in range(1, bar_size):
            bar: BarData = minute_bars[i]
            assert __time < bar.datetime
            is_same_day = _day_info == int(bar.datetime.timestamp() / _A_DAY)
            assert is_same_day
            if is_grand_volume:
                ##分钟级别的成交量是否是累加形式
                ##改成非累加方式
                _minute_volume = bar.volume - volume
                # if bar.volume < volume:
                #     print(f"why")
                assert bar.volume >= volume
                bar.volume = _minute_volume
            volume += bar.volume  ##累计分钟级别成交量
            __time = bar.datetime
            if high_price < bar.high_price:
                high_price = bar.high_price
            if low_price > bar.low_price:
                low_price = bar.low_price
            close_price = bar.close_price
            total_price += (bar.open_price + bar.close_price) / 2
        time = datetime(year=__time.year, month=__time.month, day=__time.day, hour=0, minute=0, second=0)

        avg_price = total_price / bar_size
        sell_price_bars = []
        buy_price_bars = []
        for i in range(0, bar_size):
            bar: BarData = minute_bars[i]
            price = (bar.close_price + bar.open_price) / 2
            if price > avg_price:
                sell_price_bars.append(bar)
            elif price < avg_price:
                buy_price_bars.append(bar)

        sell_price_list = np.array([(bar.open_price + bar.close_price) / 2 for bar in sell_price_bars])
        buy_price_list = np.array([(bar.open_price + bar.close_price) / 2 for bar in buy_price_bars])
        # sell_volume_list = np.array([ bar.volume  for bar in sell_price_bars])
        # buy_volume_list = np.array([ bar.volume  for bar in buy_price_bars])

        sell_price = sell_price_list.mean()
        buy_price = buy_price_list.mean()
        power_rate = ((avg_price - buy_price) - (sell_price - avg_price)) / (sell_price - buy_price)

        dayly_bar = BarV2(
            symbol=first_bar.symbol,
            _driver= driver_name,
            datetime=time,
            interval=Interval.DAILY,
            volume=volume,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            open_interest=1.0,
        )
        dayly_bar.extra.avg_price = avg_price
        dayly_bar.extra.sell_price = sell_price
        dayly_bar.extra.buy_price = buy_price
        dayly_bar.extra.power_rate = power_rate
        return dayly_bar