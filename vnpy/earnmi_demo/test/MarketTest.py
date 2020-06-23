from datetime import datetime
from earnmi.data.MarketImpl import MarketImpl


def historyTest():
    market2 = MarketImpl()


    code = "300004"
    startDate = datetime(2019, 4, 1)
    endDate = datetime(2020, 5, 1)
    today = datetime(2020, 3, 24)

    market2.setToday(today)

    market2.getHistory().getKbars(code,100);

    pass


historyTest()

