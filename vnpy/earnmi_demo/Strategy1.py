from datetime import datetime, timedelta

from earnmi.chart.Indicator import Indicator
from earnmi.data.HistoryBarPool import HistoryBarPool
from earnmi.data.Market import Market
from earnmi.strategy.StockStrategy import StockStrategy, Portfolio
from vnpy.trader.utility import ArrayManager

"""
使用三个指标来：
    obv、rsi、boll指标

"""
class Strategy1(StockStrategy):

    def __init__(
            self,

    ):
       pass

    code = "300004"
    window_size = 30;


    def on_create(self):
        """
        决策初始化.
        """
        self.write_log("on_create")


        if( not self.backtestContext is None):
            #从网络上面准备数据。
            startDate = self.backtestContext.start_date  - timedelta(days=100)
            endDate = self.backtestContext.end_date
            self.market = Market(200, startDate, endDate)


        self.market.addTrace(self.code)

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
        self.market.setToday(today)
        self.today_has_buy = False
        self.today_has_sell = False

        pass




    def on_market_open(self,protfolio:Portfolio):
        """
            市场开市.
        """
        bars = self.market.getHistory(self.code)
        if (not bars is None and bars.__len__() > 40):
            indicator = Indicator(40)
            indicator.update_bar(bars)

            dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True);

            # 金叉
            if (macd_bar[-1] > 0 and macd_bar[-2] <= 0):
                if (not self.today_has_buy):
                    targetPrice = self.market.getCurrentPrice(self.code)
                    protfolio.buy(self.code, targetPrice, 1000)
                    self.today_has_buy = True
            elif (macd_bar[-1] <= 0 and macd_bar[-2] > 0):
                if (not self.today_has_sell):
                    targetPrice = self.market.getCurrentPrice(self.code)
                    protfolio.sell(self.code, targetPrice, 1000)
                    self.today_has_sell = True


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



