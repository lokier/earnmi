from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from datetime import datetime, timedelta
import talib

code = "600155"
#code = '000300'
#801161.XSHG
market = MarketImpl()
market.addNotice(code)
market.setToday(datetime.now())


bars = market.getHistory().getKbars(code,80)

indicator = Indicator()
indicator.update_bar(bars)

beta = talib.CORREL(indicator.high,indicator.low,30)
print(beta)