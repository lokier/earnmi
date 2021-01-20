
"""
行情数据驱动器。
"""
from datetime import datetime, timedelta

from earnmi.data.BarMarket import BarMarket
from earnmi.uitl.utils import utils

from earnmi.core.Context import Context
from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarStorage import BarStorage
from vnpy.trader.constant import Interval


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
        today = datetime.now()
        limit_end_day = utils.to_end_date(today - timedelta(days=1))  ##最新数据为昨天。
        if end is None:
            end = limit_end_day
        elif (end.__gt__(today)):
            end = limit_end_day

        storage = self._storage

        ###先更新市场指数行情
        index_driver:BarDriver = market._driver_index
        update_count = self._update_driver(index_driver, start, end, clear)
        self.context.log_i(f'BarUpdator update market index({index_driver.get_name()}): update_count = {update_count}')

        ##根据指数日行情，修正更新时间节点（过滤那些不在的交易日的时间）
        index_symbol = index_driver.get_symbol_lists()[0]
        oldest_bar = index_driver.load_oldest_bar(index_symbol,Interval.DAILY,storage)
        if oldest_bar is None:
            ##更新市场行情指数失败
            self.context.log_w(f'BarUpdator update market index drivers error')
            return
        newest_bar = index_driver.load_newest_bar(index_symbol, Interval.DAILY,storage)
        assert not newest_bar is None

        newest_time = utils.to_end_date(newest_bar.datetime)
        oldest_time = utils.to_start_date(oldest_bar.datetime)

        ##更新的时间范围(start,end)不能超过市场指数的时间范围
        if start < oldest_time:
            start = oldest_time
        if end > newest_time:
            end = newest_time

        update_count = 0
        for driver in market._drivers:
            update_count+=self._update_driver(driver,start,end,clear)
        self.context.log_i(f'BarUpdator update market drivers: update_count = {update_count}')

    def _update_driver(self,driver:BarDriver,start,end,clear)->int:
        driver_name = driver.get_name()
        if clear:
            self._storage.clean(driver=driver_name)
        return driver.download_bars_from_net(self.context, start, end, self._storage)


if __name__ == "__main__":
    from earnmi.core.App import App
    from earnmi.data.driver.StockIndexDriver import StockIndexDriver
    from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver

    app = App()
    app.run()

    ##app.bar_manager.registerDriver()  ##注册股票行情驱动器

    def run_bar_updator(app:App):
        app.log_i("run_bar_updator() start!")

        storage = app.bar_manager.getStorage()
        assert not storage is None
        drvier1 = StockIndexDriver()
        drvier2 = ZZ500StockDriver()

        bar_updator = BarUpdator(app,storage,[drvier1,drvier2])

        bar_updator.update(datetime(year=2020,month=12,day=21),clear=False)
        app.log_i("run_bar_updator() finished!")


    app.post(lambda : run_bar_updator(app))




