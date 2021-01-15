from datetime import datetime, timedelta

from earnmi.chart.Indicator import Indicator
from earnmi.data.Market2 import Market
from earnmi.data.MarketImpl import MarketImpl
from earnmi.strategy.StockStrategy import StockStrategy, Portfolio

"""
使用三个指标来：
    obv、rsi、boll指标

"""
class Strategy1(StockStrategy):

    def __init__(self):
       pass

    code = "300004"
    window_size = 30;


    def on_create(self):
        """
        决策初始化.
        """
        self.write_log("on_create")

        self.market = MarketImpl()
        self.market.addNotice(self.code)

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



    __history_bar100 = None

    def on_market_open(self,protfolio:Portfolio):
        """
            市场开市.
        """



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
        #每天两点半的后尝试去做交易。
        if time.hour==14 and time.minute ==30:
            self.__history_bar100 = self.market.getHistory().getKbars(self.code,100);
            assert  len(self.__history_bar100) == 100
            bars = self.__history_bar100

            todayBar = self.market.getRealTime().getKBar(self.code)

            indicator = Indicator(40)
            indicator.update_bar(bars)
            dif, dea, macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9, array=True);



            if (not self.today_has_buy):
                # 预测金叉
                todayBar.close_price = todayBar.close_price * 1.01
                indicator.update_bar(todayBar)
                dif, dea, predict_macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9,
                                                            array=True);
                print(f"[{self.market.getToday()}]:bar={macd_bar[-1]},predic_bar={predict_macd_bar[-1]}")

                if (predict_macd_bar[-1] > 0 and macd_bar[-1] <= 0):
                    targetPrice = todayBar.close_price  # 上一个交易日的收盘价作为买如价
                    print(f"   gold cross!!!")
                    if protfolio.buy(self.code, targetPrice, 100):
                        self.today_has_buy = True
            elif (not self.today_has_sell):
                todayBar.close_price = todayBar.close_price * 0.99
                indicator.update_bar(todayBar)
                dif, dea, predict_macd_bar = indicator.macd(fast_period=12, slow_period=26, signal_period=9,
                                                            array=True);
                print(f"[{self.market.getToday()}]:bar={macd_bar[-1]},predic_bar={predict_macd_bar[-1]}")
                if (predict_macd_bar[-1] <= 0 and macd_bar[-1] > 0):
                    targetPrice = todayBar.close_price
                    print(f"   dead cross!!!")
                    if protfolio.sell(self.code, targetPrice, 100):
                        self.today_has_sell = True
