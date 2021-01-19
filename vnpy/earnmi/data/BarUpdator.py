
"""
行情数据驱动器。
"""
from datetime import datetime, timedelta

from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval

from earnmi.core.Context import Context
from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarStorage import BarStorage


class BarUpdator:
    """
    行情更新器，将最新的行情数据下载到数据。
    """
    def __init__(self,context:Context,storage:BarStorage,drivers:['BarDriver']):
       self.context = context
       self._storage = storage
       self._drivers = drivers
       assert len(self._drivers) > 0


    def update(self,start:datetime,end:datetime = None,clear = False):
        """
        参数:
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

        for driver in self._drivers:
            driver_name = driver.get_name()
            if clear:
                self._storage.clean(driver=driver_name)
            update_count = driver.download_bars_from_net(self.context,start,end,self._storage);
            self.context.log_i(f'BarUpdator update : driver = {driver_name},update_count = {update_count}')




    # def _updateSymbol(self,symbol,driver:BarDriver,start:datetime,end:datetime,clear,interval:Interval):
    #
    #     ###增量更新
    #     _newest_bar = self._storage.get_newest_bar_data(symbol,driver_name,interval)
    #     _oldest_bar = self._storage.get_oldest_bar_data(symbol,driver_name,interval)



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




