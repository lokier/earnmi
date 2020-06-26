from datetime import datetime

from earnmi.strategy.StockStrategy import StockStrategy, Portfolio


class StrategyTest(StockStrategy):

    def __init__(self):
       pass


    def on_create(self):
        """
        决策初始化.
        """

        if (not self.backtestContext is None):
            # 从网络上面准备数据。
            self.write_log(f"on_create from backtestEngine, start={self.backtestContext.start_date},end={self.backtestContext.end_date}")
        else:
            self.write_log("on_create")
        pass

    def on_destroy(self):
        """
            决策结束.（被停止之后）
        """
        self.write_log("on_destroy")
        pass

    def on_market_prepare_open(self,protfolio:Portfolio):
        """
            市场准备开始（比如：竞价）.
        """
        self.write_log("on_market_prepare")

        protfolio.buy("000034",344.23,200)

        pass




    def on_market_open(self,protfolio:Portfolio):
        """
            市场开市.
        """
        self.write_log("on_market_open")

        pass

    def on_market_prepare_close(self,protfolio:Portfolio):
        """
            市场准备关市.
        """
        self.write_log("on_market_prepare_close")
        protfolio.sell("000034",344.23,200)

        pass

    def on_market_close(self,protfolio:Portfolio):
        """
            市场关市.
        """
        self.write_log("on_market_close")

        pass

    def on_bar_per_minute(self, time: datetime,protfolio:Portfolio):
        """
            市场开市后的每分钟。
        """
        self.write_log(f"     on_bar_per_minute:{time}" )
        pass


