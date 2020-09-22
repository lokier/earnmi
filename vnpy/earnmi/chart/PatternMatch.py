from dataclasses import dataclass
from datetime import datetime

import numpy as np
import talib
from werkzeug.routing import Map

from earnmi.chart.Indicator import Indicator
from vnpy.trader.object import BarData



@dataclass
class PattrnResult():
    value:int
    name:str


"""
各种K线指标库
"""
class PatternMatch():

    def matchIndicator(indictor:Indicator)->['PattrnResult']:
        if indictor.count < 20:
            return []
        return PatternMatch.match(indictor.open,indictor.high,indictor.low,indictor.close,indictor.volume)

    def match(open: np.ndarray,high: np.ndarray,low: np.ndarray,close: np.ndarray,volumn: np.ndarray)->['PattrnResult']:
        if(len(open) < 20):
            raise RuntimeError("len must >= 20")
        rets = []
        ##61个形态识别模式
        PatternMatch.__checkIfAdd(rets,     talib.CDL2CROWS(open, high, low, close),    "CDL2CROWS")
        PatternMatch.__checkIfAdd(rets,     talib.CDL3BLACKCROWS(open, high, low, close),    "CDL3BLACKCROWS")
        PatternMatch.__checkIfAdd(rets,     talib.CDL3INSIDE(open, high, low, close),    "CDL3INSIDE")
        PatternMatch.__checkIfAdd(rets,     talib.CDL3LINESTRIKE(open, high, low, close),    "CDL3LINESTRIKE")
        PatternMatch.__checkIfAdd(rets,     talib.CDL3OUTSIDE(open, high, low, close),    "CDL3OUTSIDE")
        PatternMatch.__checkIfAdd(rets,     talib.CDL3STARSINSOUTH(open, high, low, close),    "CDL3STARSINSOUTH")
        PatternMatch.__checkIfAdd(rets,     talib.CDL3WHITESOLDIERS(open, high, low, close),    "CDL3WHITESOLDIERS")
        PatternMatch.__checkIfAdd(rets,     talib.CDLABANDONEDBABY(open, high, low, close,penetration=0),    "CDLABANDONEDBABY")
        PatternMatch.__checkIfAdd(rets,     talib.CDLADVANCEBLOCK(open, high, low, close),    "CDLADVANCEBLOCK")
        PatternMatch.__checkIfAdd(rets,     talib.CDLBELTHOLD(open, high, low, close),    "CDLBELTHOLD")
        PatternMatch.__checkIfAdd(rets,     talib.CDLBREAKAWAY(open, high, low, close),    "CDLBREAKAWAY")
        PatternMatch.__checkIfAdd(rets,     talib.CDLCLOSINGMARUBOZU(open, high, low, close),    "CDLCLOSINGMARUBOZU")
        PatternMatch.__checkIfAdd(rets,     talib.CDLCONCEALBABYSWALL(open, high, low, close),    "CDLCONCEALBABYSWALL")
        PatternMatch.__checkIfAdd(rets,     talib.CDLCOUNTERATTACK(open, high, low, close),    "CDLCOUNTERATTACK")
        PatternMatch.__checkIfAdd(rets,     talib.CDLDARKCLOUDCOVER(open, high, low, close,penetration = 0),    "CDLDARKCLOUDCOVER")
        PatternMatch.__checkIfAdd(rets,     talib.CDLDOJI(open, high, low, close),    "CDLDOJI")
        PatternMatch.__checkIfAdd(rets,     talib.CDLDOJISTAR(open, high, low, close),    "CDLDOJISTAR")
        PatternMatch.__checkIfAdd(rets,     talib.CDLDRAGONFLYDOJI(open, high, low, close),    "CDLDRAGONFLYDOJI")
        PatternMatch.__checkIfAdd(rets,     talib.CDLENGULFING(open, high, low, close),    "CDLENGULFING")
        PatternMatch.__checkIfAdd(rets,     talib.CDLEVENINGDOJISTAR(open, high, low, close),    "CDLEVENINGDOJISTAR")
        PatternMatch.__checkIfAdd(rets,     talib.CDLEVENINGSTAR(open, high, low, close,penetration = 0),    "CDLEVENINGSTAR")
        PatternMatch.__checkIfAdd(rets,     talib.CDLGAPSIDESIDEWHITE(open, high, low, close),    "CDLGAPSIDESIDEWHITE")
        PatternMatch.__checkIfAdd(rets,     talib.CDLGRAVESTONEDOJI(open, high, low, close),    "CDLGRAVESTONEDOJI")
        PatternMatch.__checkIfAdd(rets,     talib.CDLHAMMER(open, high, low, close),    "CDLHAMMER")
        PatternMatch.__checkIfAdd(rets,     talib.CDLHANGINGMAN(open, high, low, close),    "CDLHANGINGMAN")
        PatternMatch.__checkIfAdd(rets,     talib.CDLHARAMI(open, high, low, close),    "CDLHARAMI")
        PatternMatch.__checkIfAdd(rets,     talib.CDLHARAMICROSS(open, high, low, close),    "CDLHARAMICROSS")
        PatternMatch.__checkIfAdd(rets,     talib.CDLHIGHWAVE(open, high, low, close),    "CDLHIGHWAVE")
        PatternMatch.__checkIfAdd(rets,     talib.CDLHIKKAKE(open, high, low, close),    "CDLHIKKAKE")
        PatternMatch.__checkIfAdd(rets,     talib.CDLHIKKAKEMOD(open, high, low, close),    "CDLHIKKAKEMOD")
        PatternMatch.__checkIfAdd(rets,     talib.CDLHOMINGPIGEON(open, high, low, close),    "CDLHOMINGPIGEON")
        PatternMatch.__checkIfAdd(rets,     talib.CDLIDENTICAL3CROWS(open, high, low, close),    "CDLIDENTICAL3CROWS")
        PatternMatch.__checkIfAdd(rets,     talib.CDLINNECK(open, high, low, close),    "CDLINNECK")
        PatternMatch.__checkIfAdd(rets,     talib.CDLINVERTEDHAMMER(open, high, low, close),    "CDLINVERTEDHAMMER")
        PatternMatch.__checkIfAdd(rets,     talib.CDLKICKING(open, high, low, close),    "CDLKICKING")
        PatternMatch.__checkIfAdd(rets,     talib.CDLKICKINGBYLENGTH(open, high, low, close),    "CDLKICKINGBYLENGTH")
        PatternMatch.__checkIfAdd(rets,     talib.CDLLADDERBOTTOM(open, high, low, close),    "CDLLADDERBOTTOM")
        PatternMatch.__checkIfAdd(rets,     talib.CDLLONGLEGGEDDOJI(open, high, low, close),    "CDLLONGLEGGEDDOJI")
        PatternMatch.__checkIfAdd(rets,     talib.CDLLONGLINE(open, high, low, close),    "CDLLONGLINE")
        PatternMatch.__checkIfAdd(rets,     talib.CDLMARUBOZU(open, high, low, close),    "CDLMARUBOZU")
        PatternMatch.__checkIfAdd(rets,     talib.CDLMATCHINGLOW(open, high, low, close),    "CDLMATCHINGLOW")
        PatternMatch.__checkIfAdd(rets,     talib.CDLMATHOLD(open, high, low, close),    "CDLMATHOLD")
        PatternMatch.__checkIfAdd(rets,     talib.CDLMORNINGDOJISTAR(open, high, low, close),    "CDLMORNINGDOJISTAR")
        PatternMatch.__checkIfAdd(rets,     talib.CDLMORNINGSTAR(open, high, low, close),    "CDLMORNINGSTAR")
        PatternMatch.__checkIfAdd(rets,     talib.CDLONNECK(open, high, low, close),    "CDLONNECK")
        PatternMatch.__checkIfAdd(rets,     talib.CDLPIERCING(open, high, low, close),    "CDLPIERCING")
        PatternMatch.__checkIfAdd(rets,     talib.CDLRICKSHAWMAN(open, high, low, close),    "CDLRICKSHAWMAN")
        PatternMatch.__checkIfAdd(rets,     talib.CDLRISEFALL3METHODS(open, high, low, close),    "CDLRISEFALL3METHODS")
        PatternMatch.__checkIfAdd(rets,     talib.CDLSEPARATINGLINES(open, high, low, close),    "CDLSEPARATINGLINES")
        PatternMatch.__checkIfAdd(rets,     talib.CDLSHOOTINGSTAR(open, high, low, close),    "CDLSHOOTINGSTAR")
        PatternMatch.__checkIfAdd(rets,     talib.CDLSHORTLINE(open, high, low, close),    "CDLSHORTLINE")
        PatternMatch.__checkIfAdd(rets,     talib.CDLSPINNINGTOP(open, high, low, close),    "CDLSPINNINGTOP")
        PatternMatch.__checkIfAdd(rets,     talib.CDLSTALLEDPATTERN(open, high, low, close),    "CDLSTALLEDPATTERN")
        PatternMatch.__checkIfAdd(rets,     talib.CDLSTICKSANDWICH(open, high, low, close),    "CDLSTICKSANDWICH")
        PatternMatch.__checkIfAdd(rets,     talib.CDLTAKURI(open, high, low, close),    "CDLTAKURI")
        PatternMatch.__checkIfAdd(rets,     talib.CDLTASUKIGAP(open, high, low, close),    "CDLTASUKIGAP")
        PatternMatch.__checkIfAdd(rets,     talib.CDLTHRUSTING(open, high, low, close),    "CDLTHRUSTING")
        PatternMatch.__checkIfAdd(rets,     talib.CDLTRISTAR(open, high, low, close),    "CDLTRISTAR")
        PatternMatch.__checkIfAdd(rets,     talib.CDLUNIQUE3RIVER(open, high, low, close),    "CDLUNIQUE3RIVER")
        PatternMatch.__checkIfAdd(rets,     talib.CDLUPSIDEGAP2CROWS(open, high, low, close),    "CDLUPSIDEGAP2CROWS")
        PatternMatch.__checkIfAdd(rets,     talib.CDLXSIDEGAP3METHODS(open, high, low, close),    "CDLXSIDEGAP3METHODS")

        return rets

    def __checkIfAdd(rets:[],integer:np.ndarray,name:str):
        value = integer[-1]
        if value!= 0:
            rets.append(PattrnResult(value=value,name=name))



def getData(barList:[],start:int, end:int):
    high = []
    low = []
    close = []
    open = []

    # bars = np.array(barList)
    bars = barList[start:end]

    for i in range(0, len(bars)):
        bar: BarData = bars[i]
        bar.index = i
        high.append(bar.high_price)
        low.append(bar.low_price)
        close.append(bar.close_price)
        open.append(bar.open_price)


    return bars,np.array(high),np.array(low),np.array(close),np.array(open)


"""
统计所有的行业情况所有的形态识别情况
"""
def computeAll():
    from earnmi.data.SWImpl import SWImpl
    from earnmi.chart.Chart import Chart, IndicatorItem, Signal
    sw = SWImpl()
    lists = sw.getSW2List()

    start = datetime(2018, 5, 1)
    end = datetime(2020, 8, 17)

    dataSet = {}

    class DataItem(object):
        pass

    for code in lists:
        #for code in lists:
        barList = sw.getSW2Daily(code, start, end)
        indicator = Indicator()
        for bar in barList:
            ##先识别形态
            rets = PatternMatch.matchIndicator(indicator)
            size = len(rets)
            if size > 0:
                """有形态识别出来
                """
                for item in rets:
                    name = item.name
                    value = item.value

                    dataItem = None
                    if dataSet.__contains__(name):
                        dataItem = dataSet[name]
                    else:
                        dataItem = DataItem()
                        dataItem.values = [] ##形态被识别的值。
                        dataItem.pcts = []   ##识别之后第二天的盈利情况
                        dataSet[name] = dataItem
                    ##第二天的收益
                    pct = (bar.close_price - bar.open_price) / bar.open_price
                    ##收录当前形态
                    dataItem.values.append(value)
                    dataItem.pcts.append(pct)
                pass
            indicator.update_bar(bar)

    ##打印当前形态
    print(f"总共识别出{len(dataSet)}个形态")
    for key,dataItem in dataSet.items():
        values = np.array(dataItem.values)
        pcts = np.array(dataItem.pcts) * 100
        print(f"{key}： len={len(dataItem.values)},values:{values.mean()},pcts:%.2f%%,pcts_std=%.2f" % (pcts.mean(),pcts.std()))


if __name__ == "__main__":
    computeAll()

    from earnmi.data.MarketImpl import MarketImpl
    # from earnmi.data.SWImpl import SWImpl
    # from earnmi.chart.Chart import Chart, IndicatorItem, Signal
    #
    #
    # class pos(IndicatorItem):
    #     def __init__(self, integes):
    #         IndicatorItem.__init__(self,False)
    #         self.integes = integes
    #
    #     def getValues(self, indicator: Indicator, bar: BarData, signal: Signal) -> Map:
    #
    #         index = bar.index
    #         value = self.integes[index]
    #         if value == -100:
    #             signal.sell = True
    #         elif value == 100:
    #             signal.buy = True
    #         return {}
    #
    # sw = SWImpl()
    # lists = sw.getSW2List()
    #
    # code = "801743"
    #
    # start = datetime(2018, 5, 1)
    # end = datetime(2020, 8, 17)
    #
    # #for code in lists:
    # barList = sw.getSW2Daily(code, start, end)
    # # print(f"barlist size ={len(barList)}")
    #
    # bars, high, low, close, open = getData(barList, 320, 357)
    #
    # integes = talib.CDL3BLACKCROWS(open, high, low, close)
    # print(f"code:{code},orign size:{len(open)},v size:{len(integes)},value={integes}")
    #
    # rets =  PatternMatch.match(open, high, low, close,None)
    # print(f"code:{rets}")
    #
    #
    # chart = Chart()
    # chart.show(bars,pos(integes))