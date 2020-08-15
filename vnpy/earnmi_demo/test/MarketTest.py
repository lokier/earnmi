from datetime import datetime, timedelta
from earnmi.data.MarketImpl import MarketImpl
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData


def is_same_day(d1: datetime, d2: datetime) -> bool:
    return d1.day == d2.day and d1.month == d2.month and d1.year == d2.year

def isPostMinitueBar(b1:BarData,b2:BarData)-> bool:
    return b1.low_price >= b2.low_price and b1.high_price <= b2.high_price and b1.volume <=b2.volume


def basicTest():
    market2 = MarketImpl()
    code = "300004"
    assert market2.isNotice(code) == False

    market2.addNotice(code)
    assert market2.isNotice(code) == True
    key1 = market2.getNoticeData(code,"key1")
    assert key1 is None
    market2.putNoticeData(code,"key1","hello")
    key1 = market2.getNoticeData(code,"key1")
    assert key1 == "hello"

    market2.removeNotice(code)
    assert market2.isNotice(code) == False
    try:
        key1 = market2.getNoticeData(code,"key1")
        assert False
    except RuntimeError:
        assert True



def realTimeTest():
    market2 = MarketImpl()
    code = "300004"
    market2.addNotice(code)

    has_data_day1 = datetime(year=2020, month=5, day=8,hour=1)
    market2.setToday(has_data_day1)
    bar = market2.getRealTime().getKBar(code)
    assert bar is  None

    market2.setToday(datetime(year=2020, month=5, day=8,hour=9,minute=31,second=30))
    bar = market2.getRealTime().getKBar(code)
    assert not bar is  None
    bar = market2.getRealTime().getKBar(code,hour=9,minute=31,second=31)
    assert bar is  None


    begin = datetime(year=2020, month=4, day=9,hour=1)
    for i in range(50):
        day = begin + timedelta(days=i)
        market2.setToday(datetime(year=day.year, month=day.month, day=day.day, hour=9, minute=50, second=30))

        bar = market2.getRealTime().getKBar(code)
        todayIsTrade = not bar is None

        if todayIsTrade:

            print(f"realTimeTest：test in trad day : {day}")
            """
            今天是交易日
            """
            day1 = datetime(year=day.year, month=day.month, day=day.day, hour=9, minute=31, second=30)
            day2 = datetime(year=day.year, month=day.month, day=day.day, hour=10, minute=31, second=30)
            day3 = datetime(year=day.year, month=day.month, day=day.day, hour=13, minute=50, second=30)
            day4 = datetime(year=day.year, month=day.month, day=day.day, hour=15, minute=0, second=30)

            market2.setToday(day1)
            bar1 = market2.getRealTime().getKBar(code)

            market2.setToday(day2)
            bar2 = market2.getRealTime().getKBar(code)

            market2.setToday(day3)
            bar3 = market2.getRealTime().getKBar(code)

            market2.setToday(day4)
            bar4 = market2.getRealTime().getKBar(code)

            assert is_same_day(bar1.datetime,bar2.datetime) and is_same_day(bar3.datetime,bar4.datetime) and is_same_day(bar2.datetime,bar3.datetime)
            assert bar1.datetime < bar2.datetime and bar2.datetime < bar3.datetime and bar3.datetime < bar4.datetime
            assert isPostMinitueBar(bar1,bar2) and isPostMinitueBar(bar2,bar3) and isPostMinitueBar(bar3,bar4) and isPostMinitueBar(bar2,bar4)





    # no_data_day = datetime(year=2020, month=5, day=9)
    #
    # has_data_day2 = datetime(year=2020, month=5, day=11)







def historyTest():
    market2 = MarketImpl()
    market2.setToday(datetime.now())

    #获取沪市数据
    code = "600000"
    market2.addNotice(code)
    bars = market2.getHistory().getKbars(code,20)
    assert len(bars) == 20

    ##获取指数数据
    codes = ['000300']
    for code in codes:
        market2.addNotice(code)
        assert len(market2.getHistory().getKbars(code,20)) == 20


    code = "300004"

    market2.addNotice(code)

    todayListBar = market2.getHistory().getKbars(code, 50);

    pre_bares = None
    for todayBar in todayListBar:
        today = datetime(year=todayBar.datetime.year,month=todayBar.datetime.month,day=todayBar.datetime.day,minute=1)
        market2.setToday(today)
        bars1 = market2.getHistory().getKbars(code, 100);

        ##最后一个bar不应该包含今天：
        assert not utils.is_same_day( bars1[-1].datetime,today)


        assert len(bars1) == 100
        pre_bar = None
        for bar in bars1:
            assert bar.datetime < today
            if pre_bar:
                assert  pre_bar.datetime < bar.datetime
            pre_bar = bar

        bars2 = market2.getHistory().getKbarFrom(code,bars1[0].datetime)
        for index in range(len(bars1)):
            assert bars1[index].datetime == bars2[index].datetime

        #昨天的bar数据
        if pre_bares:
            for index in range(len(pre_bares) - 1):
                assert pre_bares[index + 1].datetime == bars1[index].datetime

        pre_bares = bars1

    pass


basicTest()
historyTest()
realTimeTest()

