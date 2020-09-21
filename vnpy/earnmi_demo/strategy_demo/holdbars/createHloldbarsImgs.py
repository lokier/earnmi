from datetime import datetime

from binstar_client.inspect_package import uitls

from earnmi_demo.strategy_demo.holdbars.HoldBarUtils import HoldBarUtils
from vnpy.trader.object import BarData

from earnmi import uitl
from werkzeug.routing import Map

from earnmi.chart.Chart import IndicatorItem, Signal, Chart
from earnmi.chart.Indicator import Indicator
from earnmi.data.SWImpl import SWImpl
from earnmi.uitl.utils import utils


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


def crateHoldbarsImg():
    sw = SWImpl()
    lists = sw.getSW2List()
    start = datetime(2019, 5, 1)
    end = datetime(2020, 8, 17)
    chart = Chart()
    for code in lists:
        bars = sw.getSW2Daily(code, start, end)
        # print(f"bar.size = {bars.__len__()}")

        indictor = kdj()
        chart.run(bars, indictor)

        holdBarList = indictor.getHoldBars();
        barList = utils.to_bars(holdBarList)

        chart.show(barList, item = indictor ,savefig=f'imgs\\{code}.png')

        #print(f"code:{code},cost_pct = %.2f%%" % (total_cost_pct*100))
        break

def createEarnHoldBarsImg():
    from earnmi_demo.strategy_demo.holdbars.HoldBarAnanysic import macd,kdj
    sw = SWImpl()
    lists = sw.getSW2List()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    chart = Chart()
    indictor = macd()
    computeCount = 0
    for code in lists:
        bars = sw.getSW2Daily(code, start, end)
        # print(f"bar.size = {bars.__len__()}")
        chart.run(bars, indictor)

        holdBarList = indictor.getHoldBars();

        for holdBar in holdBarList:
            barList = holdBar.bars
            if(HoldBarUtils.isEarnBarList(barList)):
                tiemStr = holdBar.start_time.strftime( '%Y%m%d' )
                chart.show(barList, savefig=f'imgs\\earn-{code}-{tiemStr}.png')

        # print(f"code:{code},cost_pct = %.2f%%" % (total_cost_pct*100))
        computeCount = computeCount + 1
        if computeCount > 10:
            break




if __name__ == "__main__":
    #crateHoldbarsImg()
    createEarnHoldBarsImg()