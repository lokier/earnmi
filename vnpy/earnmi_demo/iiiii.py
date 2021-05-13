from dataclasses import dataclass
from datetime import datetime

from werkzeug.routing import Map

from earnmi.chart.Chart import Chart, IndicatorItem, Signal
from earnmi.chart.Indicator import Indicator
from earnmi.core.App import App
from earnmi.data.BarV2 import BarV2Market, BarV2
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.model.bar import BarData

app = App()
start = datetime(year=2020,month=1,day=6)
end = datetime(year=2021,month=2,day=5)
drvier = SW2Driver()
index_driver = StockIndexDriver()  ##A股指数驱动
market = app.getBarManager().createBarMarket(index_driver,[drvier])
v2_market = BarV2Market(market)

def tofloat(v):
    return f"%.2f" % v

ret1 = [517, 6.526847754280934, 16.34816247582205, 47.38878143133462, 4.448742746615087, 48.16247582205029, ',[1.00:3.00)=48.16%,[-3.00:-1.00)=47.39%,[-1.00:1.00)=4.45%', ',[18.00:23.67)=38.49%,[1.00:6.67)=31.91%,[6.67:12.33)=20.70%,[12.33:18.00)=8.90%']
ret2 = [519, 4.92336908172046, 15.895953757225433, 52.215799614643544, 4.8169556840077075, 42.96724470134875, ',[-3.00:-1.00)=52.22%,[1.00:3.00)=42.97%,[-1.00:1.00)=4.82%', ',[18.00:23.67)=31.02%,[6.67:12.33)=25.24%,[1.00:6.67)=23.89%,[12.33:18.00)=19.85%']
print(f"%-5s%-5s%-6s%-6s%-7s%-7s%-7s" % ('',' 总数','均收益','均持天数','收益<-1%',"收益>1%","收益其它"))
print(f"%-5s%-5s%-6s%-6s%-7s%-7s%-7s" % ('',' 总数','均收益','均持天数','收益<-1%',"收益>1%","收益其它"))

print(f"%-5s%-5s%-6s%-6s%-7s%-7s%-7s" % ('正向','dd',tofloat(ret1[1])
                                         ,tofloat(ret1[2]),tofloat(ret1[3]),tofloat(ret1[4]),tofloat(ret1[5])))






