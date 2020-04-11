from datetime import datetime,timedelta

from vnpy.trader.constant import Interval

# 1m : 60 * 4 = 240,  240 * 4 = 960 =>4 day
# 1h : 1* 4 = 4,  200 * 4 = 800,    => 200day
# 1d :    900day


a = datetime.today()
yesterday = a - timedelta(days = 1)



print("sdfjkf%s%d" % ('xxxx',3))
print(a)
print(yesterday)
