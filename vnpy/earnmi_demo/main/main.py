from datetime import datetime

from earnmi.data.MarketImpl import MarketImpl
from earnmi.data.SWImpl import SWImpl
import time

sw = SWImpl()

swCode = sw.getSW2List()[0]

stockslist = sw.getSW2Stocks(swCode)

print(f"stockslist:{len(stockslist)}")

startDate = datetime(2015,4,1)
endDate = datetime(2020,5,1)
market = MarketImpl()
market.setToday(endDate)

market.addNotice('002852')
bars = market.getHistory().getKbars('002852', 300 * 3);



for code in stockslist:
    market.addNotice(code)
    print(f"getBars:{code}")
    bars = market.getHistory().getKbars(code,300 * 3);
    #time.sleep(2)

    print(f"getBars size:{len(bars)}")

