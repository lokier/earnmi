
"""
行情数据驱动器。
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Sequence, Tuple

from earnmi.data.BarSoruce import BarSource, DefaultBarSource
from earnmi.model.bar import BarData, LatestBar
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

    def createBarSoruce(self, interval=Interval.DAILY, start: datetime = None, end: datetime = None) -> BarSource:
        """
        创建行情市场对象
        参数:
        """
        if not self._inited:
            raise RuntimeError("BarMarket has not inited yet!")

        if start is None or end is None:
            index_symbol = self._driver_index.get_symbol_lists()[0]
            if start is None:
                oldest_bar = self._driver_index.load_oldest_bar(index_symbol,Interval.DAILY,self._storage)
                start = None if oldest_bar is None else oldest_bar.datetime
            if end is None:
                newest_bar  = self._driver_index.load_newest_bar(index_symbol, Interval.DAILY, self._storage)
                end = None if newest_bar is None else newest_bar.datetime
        if start is None or end is None:
            return None
        assert start < end
        source = DefaultBarSource(self.context, self._storage,self._drivers,interval,start,end)
        return source

    def init(self,indexDriver:BarDriver,drivers:['BarDriver']):
        """
        初始化市场行情的时间跨度。
        """
        self._driver_index:BarDriver = indexDriver
        self._drivers = drivers
        self._symbol_to_driver_map = {}
        for code in self._driver_index.get_symbol_lists():
            self._symbol_to_driver_map[code] = self._driver_index
        for driver in self._drivers:
            for code in driver.get_symbol_lists():
                old_driver = self._symbol_to_driver_map.get(code)
                if not old_driver is None:
                    raise RuntimeError(f"init market fail, same symobl:{code} conflict in driver {old_driver.get_name()} between {driver.get_name()}")
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
        limit_end = utils.to_end_date(self.context.now() - timedelta(days=1))

        ## end不能超过今天。
        if end is None:
            end = limit_end
        elif end > limit_end:
            raise RuntimeError("end time must be < today")
        return driver.load_bars(symbol,interval,start,end,self._storage)

    def get_symbol_list(self,symbol:str):
        """
        通过symbol获取子成分股列表。对应BarDriver的get_sub_symbol_lists方法
        """
        if not self._inited:
            raise RuntimeError("BarMarket has not inited yet!")
        driver: BarDriver = self._symbol_to_driver_map.get(symbol)
        if driver is None:
            raise RuntimeError(f" cant't find drvier from symbol: {symbol}")
        return driver.get_sub_symbol_lists(symbol)

    def get_symbol_list_at(self,driver_name:str):
        """
        获取某个驱动名称的成分股列表。
        """
        if not self._inited:
            raise RuntimeError("BarMarket has not inited yet!")
        driver:BarDriver = self._find_bar_driver(driver_name)
        return driver.get_symbol_lists()

    def get_latest_bar(self,symbol_list:['str'] = None)->{}:
        """
        返回最新的行情。
        """
        if symbol_list is None:
            symbol_list = []
            symbol_list.extend(self._driver_index.get_symbol_lists())
            for driver in self._drivers:
                symbol_list.extend(driver.get_symbol_lists())

        driver_symbols_map = defaultdict(list);
        for symbol in symbol_list:
            driver: BarDriver = self._symbol_to_driver_map.get(symbol)
            if driver is None:
                raise RuntimeError(f"can't find bar driver to support symbol: {symbol}")
            driver_symbols_map[driver].append(symbol)
        restult = {}
        latest_bars = None
        for driver,code_list in driver_symbols_map.items():
            for code in code_list:
                restult[code] = None
            if self.context.is_backtest():
                latest_bars = driver.fetch_latest_bar_for_backtest(code_list,self.context.now(),self._storage)
            else:
                latest_bars = driver.fetch_latest_bar(code_list)
            if latest_bars is None:
                continue
            for bar in latest_bars:
                if not bar is None:
                    restult[bar.code] = bar
        return restult


    def clear(self,driver_name:str):
        """
        清空某个行情驱动的数据。
        """
        driver = self._find_bar_driver(driver_name)
        self._storage.clean(driver.get_name())

    def _find_bar_driver(self,driver_name:str)->BarDriver:
        if self._driver_index.get_name() == driver_name:
            return self._driver_index
        else:
            for driver in self._drivers:
                if driver.get_name == driver_name:
                    return driver
        raise RuntimeError(f"clear() error, cant't find drvier {driver_name}")

if __name__ == "__main__":
    from earnmi.core.App import App
    from earnmi.data.driver.StockIndexDriver import StockIndexDriver
    from earnmi.data.driver.ZZ500StockDriver import ZZ500StockDriver

    app = App()
    index_driver = StockIndexDriver() ##A股指数驱动
    drvier2 = ZZ500StockDriver()    ##中证500股票池驱动
    market = app.bar_manager.createBarMarket(index_driver, [])
    bar_updator = app.bar_manager.createUpdator()
    bar_updator.update(market,datetime(2015, 10, 1))

    ##更新市场最新行情数据
    # bar_updator = app.bar_manager.createUpdator()
    # start_time = datetime(year=2020, month=12, day=20)
    # bar_updator.update(market, start_time)
    #
    # bar_list = market.get_bars("000021", Interval.DAILY, start_time)
    #
    # app.log_i(f"market.getBarDataList(): size = [{len(bar_list)}]")
    #
    # bar_source = market.createBarSoruce()
    # bar_count = 0
    # bar_000021_count = 0
    #
    # bars,code = bar_source.nextBars()
    # while not bars is None:
    #     bar_count+= len(bars)
    #     if code == '000021':
    #         bar_000021_count += len(bars)
    #     bars, code = bar_source.nextBars()
    # app.log_i(f"bar_count = {bar_count}, bar_000021_count = {bar_000021_count}")


    # print(f"sll:{SinaUtil.toSinCode('000012')}")
    # latest_bar = market.get_latest_bar(['000012'])
    #
    # print(f"latest_bar:{latest_bar}")

    ##app.bar_manager.registerDriver()  ##注册股票行情驱动器

    # def run_in_ui_thread(app:app):
    #     app.log_i("run_in_ui_thread() start!")
    #     app.log_i("run_in_ui_thread() finished!")
    #
    #
    # app.run()
    # app.post(lambda : run_in_ui_thread(app))




