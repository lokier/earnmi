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
print(f"%-3s%-8s%-8s%-8s%-8s%-8s%-8s" % ('',' total','avgPct','avgHold','pct<-1%',"pct>1%","pctOther"))
print(f"%-3s%-8s%-8s%-8s%-8s%-8s%-8s" % ('',' 总数','均收益','均持天数','收益<-1%',"收益>1%","收益其它"))

"""
交易数： 数量超过100个才有意义
均收益： 每个操作的平均收益
均天数： 每个操作的平均持有天数
正向收益分布：
反向收益分布：
反向值：
"""


html = "<table>"
html = html + " \n<thead>"
html = html + (' \n <tr><th rowspan="2"></th>  <th rowspan="2">交易数</th> <th rowspan="2" >均收益</th> <th rowspan="2">均天数</th> <th colspan="3">收益分布概率</th> </tr>')
html = html + (' \n <tr><th>小于-1%</th> <th> [-1,1]左右</th> <th>大于1%</th> </tr>')
html = html + " \n</thead>\n<tbody>"
html = html + (f"\n <tr><td>正向</td>  <td>{ret1[0]}</td> <td>{tofloat(ret1[1])}</td> <td>{tofloat(ret1[2])}</td> <td>{tofloat(ret1[3])}</td> <td>{tofloat(ret1[4])}</td> <td>{tofloat(ret1[5])}</td> </tr>")
html = html + (f"\n <tr><td>反向</td>  <td>{ret2[0]}</td> <td>{tofloat(ret2[1])}</td> <td>{tofloat(ret2[2])}</td> <td>{tofloat(ret2[3])}</td> <td>{tofloat(ret2[4])}</td> <td>{tofloat(ret2[5])}</td> </tr>")
html = html + (f'\n <tr><td>反向值</td>  <td >dd</td>  <td>天数分布</td>  <td colspan="4"></td></tr>')
html = html+ ("  \n</tbody>\n</table>")

print(f"%-3s%-8s%-8s%-8s%-8s%-8s%-8s" % ('+','dd',tofloat(ret1[1])
                                         ,tofloat(ret1[2]),tofloat(ret1[3]),tofloat(ret1[4]),tofloat(ret1[5])))

print(f"{html}")






