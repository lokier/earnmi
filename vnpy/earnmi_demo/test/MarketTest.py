from datetime import datetime, timedelta
from earnmi.data.MarketImpl import MarketImpl


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


def historyTest():
    market2 = MarketImpl()


    code = "300004"

    market2.addNotice(code)

    market2.setToday(datetime.now())
    todayListBar = market2.getHistory().getKbars(code, 50);

    pre_bares = None
    for todayBar in todayListBar:
        today = todayBar.datetime
        market2.setToday(today)
        bars1 = market2.getHistory().getKbars(code, 100);
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

