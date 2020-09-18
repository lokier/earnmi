from datetime import datetime

from ibapi.common import BarData
from werkzeug.routing import Map

from earnmi.chart.Chart import IndicatorItem, Signal, Chart
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl

class kdj(IndicatorItem):
    def getValues(self, indicator: Indicator,bar:BarData,signal:Signal) -> Map:
        values = {}
        count = 30
        if indicator.count >= count:
            k, d, j = indicator.kdj(fast_period=9, slow_period=3, array=True)
            ##金叉出现
            if (k[-1] >= d[-1] and k[-2] <= d[-2]):
                if not signal.hasBuy:
                    signal.buy = True
            ##死叉出现
            if (k[-1] <= d[-1] and k[-2] >= d[-2]):
                if signal.hasBuy:
                    signal.sell = True

        return values


if __name__ == "__main__":
    sw = SWImpl()
    lists = sw.getSW2List()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    chart = Chart()

    for code in lists:
        bars = sw.getSW2Daily(code, start, end)
        # print(f"bar.size = {bars.__len__()}")

        indictor = kdj()
        chart.run(bars, indictor)

        holdBarList = indictor.getHoldBars();
        barList = []
        close_price = None
        for holdBar in holdBarList:
            if close_price is None:
                barList.append(holdBar.toBarData())
                close_price = holdBar.close_price
            else:
                # barList.append(holdBar.toBarData())
                bar = holdBar.toBarData(new_open_price=close_price);
                barList.append(bar)
                close_price = bar.close_price

        chart.show(barList, savefig=f'imgs\\{code}.png')
