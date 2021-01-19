
"""
行情数据驱动器。
"""
from datetime import datetime, timedelta
from typing import Sequence
from earnmi.model.bar import BarData
from earnmi.core.Context import Context
from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarStorage import BarStorage
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval


class BarMarket:
    """
    行情市场。
    """
    def __init__(self,context:Context,storage:BarStorage):
       """
       参数：
            context:
            storage:
            indexDriver: 指数行情驱动器，比如:A股的指数是上证指数。
            drivers:  各种股票池行情驱动器。
       """
       self.context = context
       self._storage = storage
       self._inited = False
       self._symbol_to_driver_map = {}

    def init(self,indexDriver:BarDriver,drivers:['BarDriver']):
        """
        初始化市场行情的时间跨度。
        """
        self._driver_index:BarDriver = indexDriver
        self._drivers = drivers
        for code in self._driver_index.get_symbol_lists():
            self._symbol_to_driver_map[code] = self._driver_index
        for driver in self._drivers:
            for code in driver.get_symbol_lists():
                self._symbol_to_driver_map[code] = driver

        self._inited = True

    def get_bars(self, symbol: str,interval:Interval, start: datetime,end:datetime = None) -> Sequence["BarData"]:
        """
        返回股票的历史行情。不包含今天now的行情数据。
        """
        if not self._inited:
            raise RuntimeError("BarMarket has not inited yet!")
        driver:BarDriver = self._symbol_to_driver_map.get(symbol)
        if driver is None:
            raise RuntimeError(f"can't find bar driver to support symbol: {symbol}")
        if not driver.support_interval(interval):
            raise RuntimeError(f"bar driver({driver.get_name()}) can't support interval : {interval}")
        if end is None:
            end = utils.to_end_date(datetime.now())
        return self._storage.load_bar_data(symbol,driver.get_name(),interval,start,end)





if __name__ == "__main__":
    from earnmi.core.App import App
    from earnmi.data.driver.StockIndexDriver import StockIndexDriver
    from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver
    from earnmi.data.BarUpdator import BarUpdator

    app = App()
    app.run()

    ##app.bar_manager.registerDriver()  ##注册股票行情驱动器

    def run_in_ui_thread(context:Context):
        app.log_i("run_in_ui_thread() start!")

        storage = app.bar_manager.getStorage()
        assert not storage is None
        index_driver = StockIndexDriver()
        drvier2 = ZZ500StockDriver()

        start_time = datetime(year=2020,month=12,day=20)

        ##创建一个市场行情对象
        market = BarMarket(context,storage)
        market.init(index_driver,[drvier2])

        ##更新市场最新行情数据
        bar_updator = BarUpdator(context,storage)
        bar_updator.update(market,start_time)

        bar_list = market.get_bars("000021",Interval.DAILY,start_time)

        # bar_updator = BarUpdator(app,storage,[drvier1,drvier2])
        #
        # bar_updator.update(datetime(year=2020,month=12,day=21),clear=False)
        app.log_i(f"market.getBarDataList(): size = [{len(bar_list)}]")

        app.log_i("run_in_ui_thread() finished!")


    app.post(lambda : run_in_ui_thread(app))




