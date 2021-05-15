from datetime import datetime

from earnmi.core.App import App
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.uitl.jqSdk import jqSdk

code = "601318" #在datetime(2019, 2, 27, 9, 48)，到达 high_price=68.57

drvier1 = StockIndexDriver()
drvier2 = SW2Driver()
app = App()
start = datetime(year=2020,month=1,day=1)
end = datetime(year=2021,month=3,day=20)
barSource = app.getBarManager().createBarParallel(drvier2,start,end)

###按日期并行遍历bar数据
for day,bars in barSource.items():
    print(f"day={day}: size= {len(bars)}")




