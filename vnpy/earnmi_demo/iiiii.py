from dataclasses import dataclass
from datetime import datetime
from earnmi.core.App import App
from earnmi.data.BarV2 import BarV2Market
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver

app = App()
start = datetime(year=2020,month=1,day=24)
end = datetime(year=2021,month=2,day=5)
drvier = SW2Driver()
index_driver = StockIndexDriver()  ##A股指数驱动
market = app.getBarManager().createBarMarket(index_driver,[drvier])
v2_market = BarV2Market(market)
bars = v2_market.get_bars("801101",start,end)
print(f"len:{len(bars)}")

