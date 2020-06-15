from datetime import datetime, timedelta

from earnmi.data.HistoryBarPool import HistoryBarPool
from earnmi.strategy.StockStrategy import StockStrategy, Portfolio

"""
使用三个指标来：
    obv、rsi、boll指标

"""
class Strategy1(StockStrategy):

    def __init__(
            self,

    ):
       pass


    def on_create(self):
        """
        决策初始化.
        """
        self.write_log("on_create")
        self.historyData = HistoryBarPool("300004",30)

        if( not self.backtestContext is None):
            #从网络上面准备数据。
            startDate = self.backtestContext.start_date  - timedelta(days=100)
            endDate = self.backtestContext.end_date
            self.historyData.initPool(startDate,endDate)

        pass

    def on_destroy(self):
        """
            决策结束.（被停止之后）
        """
        self.write_log("on_destroy")
        pass

    def on_market_prepare_open(self,protfolio:Portfolio,today:datetime):
        """
            市场准备开始（比如：竞价）.
        """

        #准备线程池，准备数据。
        self.historyData.setToday(today)


        pass




    def on_market_open(self,protfolio:Portfolio):
        """
            市场开市.
        """
        pass

    def on_market_prepare_close(self,protfolio:Portfolio):
        """
            市场准备关市.
        """


        pass

    def on_market_close(self, protfolio:Portfolio):
        """
            市场关市.
        """

        pass

    def on_bar_per_minute(self, time: datetime, protfolio:Portfolio):
        """
            市场开市后的每分钟。
        """
        pass


