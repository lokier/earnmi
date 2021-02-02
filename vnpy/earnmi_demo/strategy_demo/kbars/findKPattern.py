


from datetime import datetime

from earnmi.chart.FloatEncoder import FloatEncoder
from earnmi.chart.Indicator import Indicator
from earnmi.chart.KPattern2 import KPattern2
from vnpy.trader.object import BarData
import numpy as np
from earnmi.data.SWImpl import SWImpl


class CountItem(object):
    name = None
    count_total:int = 0
    count_earn:int = 0;
    pct_total:float  = 0.0
    pct_earn:float  = 0.0


"""
寻找一个k线形态，这个形态产生之后，第一天卖方力量不超过2%，2,3天后卖方力量突破3%的概率值。
"""
class TraceIn3DayItem(object):
    first_limit_close_pct = 1  ##不管第一天的涨幅
    targ_pct = 2

    def __init__(self,kPattern:int,bar:BarData):
        self.kPattern = kPattern
        self.firstBar = bar  ##k线形态开始生成时的bar
        self.postBars = []
        self.wanted = None
        self.current_sell_pct = -100
        self.current_buy_pct = 100


    """
    下一天的bar值。
    """
    def onTraceBar(self,bar:BarData):
        startBar = self.firstBar
        sell_pct = 100 * ((bar.high_price + bar.close_price) / 2 - startBar.close_price) / startBar.close_price
        buy_pct = 100 * ((bar.low_price + bar.close_price) / 2 - startBar.close_price) / startBar.close_price

        self.postBars.append(bar)
        size = len(self.postBars)
        if size <= 1:
            #第一天
            first_close_pct = (bar.close_price - startBar.close_price) / startBar.close_price
            self.fisrt_sell_pct = sell_pct
            self.first_buy_pct = buy_pct
            #if first_close_price > self.first_limit_close_price:
            if first_close_pct > self.first_limit_close_pct:
                self.wanted = False
                return

        self.current_sell_pct = max(self.current_sell_pct,sell_pct)
        self.current_buy_pct = min(self.current_buy_pct,buy_pct)

        if size >= 3:
            self.wanted = True
            return


    def isFinished(self)->bool:
        return not self.wanted is None

    def isWanted(self)->bool:
        return self.wanted

    def isSuccess(self) ->bool:
        return self.current_sell_pct >= self.targ_pct


def findKPatternThatIn3Day(first_day_pct:float = 3,targe_pct = 3):
    sw = SWImpl()
    lists = sw.getSW2List()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    dataSet = {}
    total_count = 0
    for code in lists:
        # for code in lists:
        barList = sw.getSW2Daily(code, start, end)
        indicator = Indicator(40)
        traceItems:['TraceIn3DayItem'] = []
        for bar in barList:
            ###跟踪数据
            toDeleteList = []
            for traceItem in traceItems:
                traceItem.onTraceBar(bar)
                if traceItem.isFinished():
                    toDeleteList.append(traceItem)
                    if traceItem.isWanted():
                        ###归纳到统计里面
                        dataItem: CountItem = dataSet.get(traceItem.kPattern)
                        if dataItem is None:
                            dataItem = CountItem()
                            dataSet[traceItem.kPattern] = dataItem
                        pct = traceItem.current_sell_pct
                        total_count += 1
                        dataItem.count_total += 1
                        dataItem.pct_total += pct
                        if traceItem.isSuccess():
                            dataItem.count_earn += 1
                            dataItem.pct_earn += pct
                        pass
            for traceItem in toDeleteList:
                traceItems.remove(traceItem)

            indicator.update_bar(bar)
            kEncodeValue = KPattern2.encode2KAgo1(indicator)
            if kEncodeValue is None:
                continue
            traceItem = TraceIn3DayItem(kEncodeValue,bar)
            traceItems.append(traceItem)

        ##打印当前形态
    occur_count = 0
    print(f"总共分析{total_count}个形态，识别出{len(dataSet)}个形态，有意义的形态有：")
    max_succ_rate = 0
    min_succ_rate = 100
    ret_list = []
    for key, dataItem in dataSet.items():
        success_rate = 100 * dataItem.count_earn / dataItem.count_total
        if dataItem.count_total < 300:
            continue
        if success_rate < 40:
            continue
        ret_list.append(key)
        if dataItem.count_earn > 0:
            earn_pct =  dataItem.pct_earn / dataItem.count_earn
        else:
            earn_pct = 0

        avg_pct = dataItem.pct_total / dataItem.count_total
        occur_count += dataItem.count_total
        occur_rate = 100 * dataItem.count_total / total_count
        max_succ_rate = max(success_rate, max_succ_rate)
        min_succ_rate = min(success_rate, min_succ_rate)
        print(f"{key}： total={dataItem.count_total},suc=%.2f%%,occur_rate=%.2f%%,earn_pct:%.2f%%,avg_pct:%.2f%%)" % (
        success_rate, occur_rate, earn_pct, avg_pct))

    total_occur_rate = 100 * occur_count / total_count
    print(f"总共：occur_rate=%.2f%%, min_succ_rate=%.2f%%, max_succ_rate=%.2f%%" % (total_occur_rate, min_succ_rate, max_succ_rate))
    print(f"{ret_list}")


"""
K线形态图收集器
"""
class KPatternCollector:

    def onCreate(self):
        pass

    """
    开始新的股票遍历,如果不需要最终，返回false。
    """
    def onStart(self,code:str) ->bool:
        return True

    """
    检查是否追踪某个k线形态，是的话，创建一个最终值对象。
    """
    def checkIfTrace(self,newBar:BarData)->TraceIn3DayItem:
        pass

    def onTraceFinish(self,traceItem:TraceIn3DayItem):
        pass

    def onEnd(self,code:str):
        pass

    def onDestroy(self):
        pass




"""
生成训练数据。
"""
def ganerateKPatternTrainData( ):

    class MyPattherCollector(KPatternCollector):
        # 收集指定的k线
        collectKPatternOnly = True
        KPattern: [] = [712]
        pct_split = [-7, -5, -3, -1.5, -0.5, 0.5, 1.5, 3, 5, 7]
        # pct_split = [-7, -5, -3, -1.0, 0, 1, 3, 5, 7]
        # pct_split = [-0.5,0.5]
        pctEncoder = FloatEncoder(pct_split);

        def __init__(self):
            self.kPattersMap = {}
            self.sw = SWImpl()
            self.dataSet = []
            for value in self.KPattern:
                self.kPattersMap[value] = True

        def onStart(self, code: str) ->bool:
            self.indicator = Indicator(40)
            self.traceCode = code
            self.traceName = self.sw.getSw2Name(code)
            return True
        """
        检查是否追踪某个k线形态，是的话，创建一个最终值对象。
        """
        def checkIfTrace(self, newBar: BarData) -> TraceIn3DayItem:
            self.indicator.update_bar(newBar)
            kEncodeValue = KPattern2.encode2KAgo1(self.indicator)
            if kEncodeValue is None:
                return None
            if self.collectKPatternOnly and self.kPattersMap.get(kEncodeValue) is None:
                return None
            return TraceIn3DayItem(kEncodeValue, newBar)

        def onTraceFinish(self, traceItem: TraceIn3DayItem):
            if traceItem.isWanted():
                ##收集数据。
                data = []
                data.append(self.traceCode)
                data.append(self.traceName)
                data.append(traceItem.kPattern)
                data.append(traceItem.first_buy_pct)
                data.append(traceItem.fisrt_sell_pct)
                data.append(traceItem.current_sell_pct)
                data.append(traceItem.current_buy_pct)
                self.dataSet.append(data)

        def onDestroy(self):
            import pandas as pd
            cloumns = ["code", "name", "kPattern", "buy_price", "sell_price", "label_sell_price", "label_buy_price"]
            wxl = pd.DataFrame(self.dataSet, columns=cloumns)
            writer = pd.ExcelWriter('files/sw_train_data_sample.xlsx')
            wxl.to_excel(writer, sheet_name="sample", index=False)
            writer.save()
            writer.close()
            print(f"dataSize = {len(self.dataSet)}")



    collector: KPatternCollector = MyPattherCollector()
    sw = SWImpl()
    lists = sw.getSW2List()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    collector.onCreate()
    for code in lists:
        collector.onStart(code)
        barList = sw.getSW2Daily(code, start, end)
        traceItems= []
        for bar in barList:
            toDeleteList = []
            for traceItem in traceItems:
                traceItem.onTraceBar(bar)
                if traceItem.isFinished():
                    toDeleteList.append(traceItem)
                    collector.onTraceFinish(traceItem)
            for traceItem in toDeleteList:
                traceItems.remove(traceItem)
            traceItem = collector.checkIfTrace(bar)
            if traceItem is None:
                continue
            traceItems.append(traceItem)
        collector.onEnd(code)
    collector.onDestroy()


"""
  打印指定有意义的k线形态更多的信息
"""
def printKPatterMoreDetail(
        kPatters = [535, 359, 1239, 1415, 1072, 712, 1412, 1240, 1413, 888, 2823, 706, 1414, 1064]
):
    from vnpy.trader.constant import Exchange
    from vnpy.trader.constant import Interval
    sw = SWImpl()
    lists = sw.getSW2List()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)

    pct_split = [-7, -5, -3, -1.5, -0.5, 0.5, 1.5, 3, 5, 7]
    #pct_split = [-7, -5, -3, -1.0, 0, 1, 3, 5, 7]
    pct_split = [2]

    pctEncoder = FloatEncoder(pct_split);

    kPattersMap = {}
    for value in kPatters:
        kPattersMap[value] = True

    class InnerData(object):
        kValue:int ##
        sell_disbute = np.zeros(pctEncoder.mask())  ##卖方力量分布情况
        buy_disbute = np.zeros(pctEncoder.mask())  #买方力量分布情况
        pass

    dataSet = {}
    occurDayMap = {}
    allTrayDay = 1

    for code in lists:
        # for code in lists:
        barList = sw.getSW2Daily(code, start, end)
        indicator = Indicator(40)
        traceItems:['TraceIn3DayItem'] = []
        allTrayDay = max(allTrayDay,len(barList))

        for bar in barList:
            ###跟踪数据
            toDeleteList = []
            for traceItem in traceItems:
                traceItem.onTraceBar(bar)
                if traceItem.isFinished():
                    toDeleteList.append(traceItem)
                    if traceItem.isWanted():
                        occurBar = traceItem.firstBar
                        dayKey = occurBar.datetime.year * 13 * 35 + occurBar.datetime.month * 13 + occurBar.datetime.day
                        occurDayMap[dayKey] = True
                        ###归纳到统计里面
                        innerData: InnerData = dataSet.get(traceItem.kPattern)
                        if innerData is None:
                            innerData = InnerData()
                            innerData.kValue = traceItem.kPattern
                            dataSet[traceItem.kPattern] = innerData

                        sell_pct = traceItem.current_sell_pct
                        buy_pct = traceItem.current_buy_pct
                        innerData.buy_disbute[pctEncoder.encode(buy_pct)] += 1
                        innerData.sell_disbute[pctEncoder.encode(sell_pct)] += 1
                        pass
            for traceItem in toDeleteList:
                traceItems.remove(traceItem)

            indicator.update_bar(bar)
            kEncodeValue = KPattern2.encode2KAgo1(indicator)
            if kEncodeValue is None or kPattersMap.get(kEncodeValue) is None:
                continue
            traceItem = TraceIn3DayItem(kEncodeValue,bar)
            traceItems.append(traceItem)

    print(f"所有交易日中，有意义的k线形态出现占比：%.2f%%" % (100 * len(occurDayMap) / allTrayDay))
    for kValue, dataItem in dataSet.items():
        total_count1 = 0
        total_count2 = 0
        for cnt in dataItem.sell_disbute:
            total_count1 += cnt
        for cnt in dataItem.buy_disbute:
            total_count2 += cnt
        assert  total_count1 == total_count2
        assert total_count1 > 0

        print(f"\n\nk:%6d, " % (kValue))

        print(f"   卖方价格分布：")
        for encode in range(0,len(dataItem.sell_disbute)):
            occurtRate = 100 * dataItem.sell_disbute[encode] / total_count1
            print(f"   {pctEncoder.descriptEncdoe(encode)}：%.2f%%" % (occurtRate))

        print(f"   买方价格分布：")
        for encode in range(0, len(dataItem.buy_disbute)):
            occurtRate = 100 * dataItem.buy_disbute[encode] / total_count1
            print(f"   {pctEncoder.descriptEncdoe(encode)}：%.2f%%" % (occurtRate))

    pass

if __name__ == "__main__":
    #findKPatternThatIn3Day()
    printKPatterMoreDetail(kPatters=[712])
    #ganerateKPatternTrainData()
    pass
