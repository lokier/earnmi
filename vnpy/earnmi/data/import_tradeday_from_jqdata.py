from datetime import datetime, timedelta
import jqdatasdk as jq
import numpy as np
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from vnpy.trader.object import BarData

"""
  导入指定时间范围的交易。 数据保存到：AAAAAA:SSE
"""
def save_bar_data_from_jqdata(start_date: datetime, end_date: datetime):
    exechage = Exchange.SSE

    code = "AAAAAA"
    batch_day = 900
    interval = Interval.DAILY

    batch_start = start_date
    while(batch_start.__lt__(end_date)):
        batch_end = batch_start + timedelta(days = batch_day)
        if(batch_end.__gt__( end_date)):
            batch_end = end_date
        print(" start:%s , end :%s" % (batch_start.__str__(), batch_end.__str__()))

        tradedays = jq.get_trade_days(start_date=batch_start, end_date=end_date)
        bars = []
        for day in tradedays:
            date = datetime(year=day.year, month=day.month, day=day.day);
            bar = BarData(
            symbol=code,
            exchange=exechage,
            datetime=date,
            interval=interval,
            volume=0,
            open_price=0.0,
            high_price=0.0,
            low_price=0.0,
            close_price=0.0,
            open_interest=1,
            gateway_name="DB"
            )
            bars.append(bar)
        print("save size:%d" % bars.__len__())
        database_manager.save_bar_data(bars)
        batch_start = batch_end + timedelta(days = 1)
    pass



# start main

start_day = datetime.strptime("2010-01-01","%Y-%m-%d")
end_day = datetime.strptime("2020-03-29","%Y-%m-%d")

if(not jq.is_auth()):
    jq.auth('13530336157','Qwer4321') #ID是申请时所填写的手机号；Password为聚宽官网登录密码，新申请用户默认为手机号后6位

if(not jq.is_auth()):
    print('jq is not auth,exist')
    exit()
print('jq is auth')

code = 'AAAAAA'
database_manager.clean(code)
save_bar_data_from_jqdata(start_date=start_day,end_date=end_day)