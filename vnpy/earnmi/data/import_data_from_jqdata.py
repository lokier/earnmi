from datetime import datetime, timedelta
import jqdatasdk as jq
import numpy as np
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.database import database_manager
from vnpy.trader.object import BarData

"""
  保存数据库。
"""
def save_bar_data_from_jqdata(code: str, interval: Interval, start_date: datetime, end_date: datetime)->int:
    exechage = Exchange.SZSE
    vn_code = code+".XSHE"
    if(code.startswith("6")):
        vn_code = code+".XSHG"
        exechage = Exchange.SSE

    print("save_bar_data_from_jqdata:code =%s" % code)
    # 1m : 60 * 4 = 240, 240 * 4 = 960 =>4 day
    # 1h : 1* 4 = 4, 200 * 4 = 800, => 200day
    # 1d : 900day
    # interval.__str__()
    batch_day = 900
    jq_frequency = '1d'
    if(interval == Interval.MINUTE):
        batch_day = 4
        jq_frequency = '1m'
    elif(interval == Interval.HOUR):
        batch_day = 200
        jq_frequency ='60m'
    elif (interval == Interval.DAILY):
        jq_frequency = '1d'



    batch_start = start_date
    saveCount = 0
    while(batch_start.__lt__(end_date)):
        batch_end = batch_start + timedelta(days = batch_day)
        if(batch_end.__gt__( end_date)):
            batch_end = end_date
        print(" start:%s , end :%s" % (batch_start.__str__(), batch_end.__str__()))

        prices = jq.get_price(vn_code, start_date=batch_start, end_date=batch_end,
        fields=['open', 'close', 'high', 'low', 'volume'], frequency=jq_frequency)

        if(prices is None):
            break

        bars = []
        lists = np.array(prices)
        for rowIndex in range(0, lists.shape[0]):
            open_interest = 0
            row = prices.iloc[rowIndex]
            wd = prices.index[rowIndex]
            date = datetime(year=wd.year, month=wd.month, day=wd.day, hour=wd.hour, minute=wd.minute, second=wd.second);

            bar = BarData(
            symbol=code,
            exchange=exechage,
            datetime=date,
            interval=interval,
            volume=row['volume'],
            open_price=row['open'],
            high_price=row['high'],
            low_price=row['low'],
            close_price=row['close'],
            open_interest=open_interest,
            gateway_name="DB"
            )
            bars.append(bar)
        saveCount += bars.__len__()
        print("save size:%d" % bars.__len__())
        database_manager.save_bar_data(bars)
        batch_start = batch_end #+ timedelta(days = 1)
    return saveCount



if __name__ == "__main__":
    code = "300004"
    start = datetime.now() - timedelta(days=600)
    end = datetime.now()
    database_manager.clean(code)
    count = save_bar_data_from_jqdata(code, Interval.DAILY, start_date=start, end_date=end)

    exchange = Exchange.SZSE
    if (code.startswith("6")):
        exchange = Exchange.SSE

    db_data = database_manager.load_bar_data(code, exchange, Interval.DAILY, start, end)

    print(f"db.size={db_data.__len__()},count ={count}")
    assert count == len(db_data)
# start main

# start_day = datetime.strptime("2018-03-29","%Y-%m-%d")
# end_day = datetime.strptime("2020-03-29","%Y-%m-%d")
#
# if(not jq.is_auth()):
#     jq.auth('13530336157','Qwer4321') #ID是申请时所填写的手机号；Password为聚宽官网登录密码，新申请用户默认为手机号后6位
#
# if(not jq.is_auth()):
#     print('jq is not auth,exist')
#     exit()
# print('jq is auth')
#
# code = '600009'
# database_manager.clean(code)
# save_bar_data_from_jqdata(code,Interval.DAILY,start_date=start_day,end_date=end_day)