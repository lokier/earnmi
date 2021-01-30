
"""
行情数据驱动器。
"""
from datetime import datetime, timedelta
from typing import Sequence

from earnmi.data.BarMarket import BarMarket
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.uitl.utils import utils

from earnmi.core.Context import Context
from earnmi.data.BarDriver import BarDriver, DayRange
from earnmi.data.BarStorage import BarStorage
from vnpy.trader.constant import Interval



class _dayRange_impl(DayRange):

    def __init__(self,start:datetime,end:datetime,daylist:[]=None):
        self.daylist = daylist
        self._start = start
        self._end = end

    def start(self) -> datetime:
        return self._start

    def end(self) -> datetime:
        return self._end

    def items(self) -> Sequence['datetime']:
        if self.daylist is None:
            return self._make_day_list(self._start,self._end)
        else:
            return self._sub_day_list(self.daylist,self._start,self._end)

    def _make_day_list(self,start:datetime,end:datetime):
        day_list = []
        assert start <= end
        day_list.append(start)
        day = start
        while not utils.is_same_day(day,end):
            day = day + timedelta(days=1)
            day_list.append(day)
        assert utils.is_same_day(start, day_list[0])
        assert utils.is_same_day(end, day_list[-1])
        return day_list

    def _sub_day_list(self,day_list:[],start:datetime,end:datetime):
        start_index = 0
        for i in range(0,len(day_list)):
            if utils.is_same_day(day_list[i], start):
                start_index = i
                break
            elif start < day_list[i]:
                start_index = i
                break

        assert start_index>=0
        end_index = len(day_list)
        for i in range(start_index,len(day_list)):
            if utils.is_same_day(day_list[i],end):
                end_index = i +1
                break
            elif day_list[i] > end:
                end_index = i
                break
        assert start_index>=0
        assert start_index<=end_index
        subList =  day_list[start_index:end_index]
        #assert utils.is_same_day(start,subList[0])
        #assert utils.is_same_day(end,subList[-1])
        return subList

class BarUpdator:
    """
    行情更新器，将最新的行情数据下载到数据。
    """
    def __init__(self,context:Context,storage:BarStorage):
       """
       参数：
            context:
            storage:
            indexDriver: 指数行情驱动器
            drivers:
       """
       self.context = context
       self._storage = storage


    def update(self,market:BarMarket,start:datetime,end:datetime = None, clear = False):
        """
        参数:
            market: 行情市场
            start:开始时间
            end：结束时间，None表示当前时间
            clear: 更新之前是否清空行情数据。
        """
        self.update_drivers(market._driver_index,market._drivers,start,end,clear)

    def update_drivers(self,index_driver: BarDriver,drivers:[],start:datetime,end:datetime = None, clear = False):
        today = datetime.now()
        limit_end_day = utils.to_end_date(today - timedelta(days=1))  ##最新数据为昨天。
        if end is None:
            end = limit_end_day
        elif (end.__gt__(today)):
            end = limit_end_day

        storage = self._storage

        ###先更新市场指数行情
        update_count = self._update_driver(index_driver, _dayRange_impl(start, end), clear)
        self.context.log_i("BarUpdator",f'update  index({index_driver.get_name()}): update_count = {update_count}')

        ##根据指数日行情，修正更新时间节点（过滤那些不在的交易日的时间）
        index_symbol = index_driver.get_symbol_lists()[0]
        oldest_bar = index_driver.load_oldest_bar(index_symbol, Interval.DAILY, storage)
        if oldest_bar is None:
            ##更新市场行情指数失败
            self.context.log_w("BarUpdator",f'update index drivers error')
            return
        newest_bar = index_driver.load_newest_bar(index_symbol, Interval.DAILY, storage)
        assert not newest_bar is None

        newest_time = utils.to_end_date(newest_bar.datetime)
        oldest_time = utils.to_start_date(oldest_bar.datetime)
        index_bars = index_driver.load_bars(index_symbol,Interval.DAILY,start,end,storage)
        trade_day_list = self._to_day_list(index_bars)

        ##更新的时间范围(start,end)不能超过市场指数的时间范围
        if start < oldest_time:
            start = oldest_time
        if end > newest_time:
            end = newest_time
        _day_list = _dayRange_impl(start, end, trade_day_list)

        update_count = 0
        for driver in drivers:
            update_count += self._update_driver(driver, _day_list, clear)
        self.context.log_i("BarUpdator",f'update  drivers: update_count = {update_count}')

    def _to_day_list(self,bars:Sequence["BarData"]):
        day_list = []
        for bar in bars:
            day_list.append(bar.datetime)
        return day_list

    def _update_driver(self, driver:BarDriver, days:_dayRange_impl, clear)->int:
        driver_name = driver.get_name()
        if clear:
            self._storage.clean(driver=driver_name)
        download_cnt = 0
        start = days.start()
        end = days.end()
        start_date = utils.to_start_date(start)
        end_date = utils.to_end_date(end)
        storage = self._storage
        for symbol in driver.get_symbol_lists():
            newest_bar = storage.get_newest_bar_data(symbol, driver.get_name(), Interval.DAILY)
            if newest_bar is None:
                # 不含数据，全量更新
                download_cnt += driver.download_bars_from_net(self.context, symbol,days, self._storage)
            else:
                # 已经含有数据，增量更新
                oldest_bar = storage.get_oldest_bar_data(symbol, driver.get_name(), Interval.DAILY)
                assert not oldest_bar is None
                oldest_datetime = utils.to_end_date(oldest_bar.datetime - timedelta(days=1))
                newest_datetime = utils.to_start_date(newest_bar.datetime + timedelta(days=1))  ##第二天一开始
                if start_date < oldest_datetime:
                    _the_day_list = _dayRange_impl(start_date, oldest_datetime, days.daylist)
                    download_cnt += driver.download_bars_from_net(self.context,symbol, _the_day_list,self._storage)
                if newest_datetime < end_date:
                    _the_day_list = _dayRange_impl(newest_datetime, end_date, days.daylist)
                    download_cnt += driver.download_bars_from_net(self.context,symbol, _the_day_list,self._storage)
        return download_cnt



if __name__ == "__main__":
    from earnmi.core.App import App
    from earnmi.data.driver.StockIndexDriver import StockIndexDriver
    from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver

    app = App()
    app.run()

    ##app.bar_manager.registerDriver()  ##注册股票行情驱动器

    def run_bar_updator(app:App):
        app.log_i("xxxx","run_bar_updator() start!")

        storage = app.bar_manager.getStorage()
        assert not storage is None
        drvier1 = StockIndexDriver()
        drvier2 = ZZ500StockDriver()
        driver3 = SW2Driver()

        bar_updator = BarUpdator(app,storage)

        bar_updator.update_drivers(drvier1,[driver3],datetime(year=2021,month=1,day=8),clear=False)
        app.log_i("xxxx","run_bar_updator() finished!")


    app.post(lambda : run_bar_updator(app))




