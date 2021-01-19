
"""
行情数据驱动器。
"""
from datetime import datetime

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
        pass



if __name__ == "__main__":
    from earnmi.core.App import App
    from earnmi.data.driver.StockIndexDriver import StockIndexDriver

    app = App()
    app.run()

    ##app.bar_manager.registerDriver()  ##注册股票行情驱动器

    def run_bar_updator(app:App):
        app.log_i("run_bar_updator() start!")

        storage = app.bar_manager.getStorage()
        assert not storage is None
        drvier1 = StockIndexDriver()

        bar_updator = BarUpdator(app,storage,[drvier1])

        bar_updator.update(datetime(year=2020,month=1,day=1))
        app.log_i("run_bar_updator() finished!")


    app.post(lambda : run_bar_updator(app))




