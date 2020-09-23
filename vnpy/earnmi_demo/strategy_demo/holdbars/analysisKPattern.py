


"""
统计所有的行业情况所有的形态识别情况
"""
import math
from datetime import datetime
import numpy as np
from earnmi.chart.Indicator import Indicator
from earnmi.chart.KPattern import KPattern


class CountItem(object):
    name = None
    count_total:int = 0
    count_earn:int = 0;
    pct_total:float  = 0.0
    pct_earn:float  = 0.0

"""
统计申万行业的k线形态识别
"""
def compute_SW_KPattern_data():
    from earnmi.data.SWImpl import SWImpl
    from earnmi.chart.Chart import Chart, IndicatorItem, Signal
    sw = SWImpl()
    lists = sw.getSW2List()

    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)

    dataSet = {}


    total_count  = 0
    for code in lists:
        #for code in lists:
        barList = sw.getSW2Daily(code, start, end)
        indicator = Indicator()
        preBar = None
        for bar in barList:
            ##先识别形态
            rets = KPattern.matchIndicator(indicator)
            size = len(rets)
            if size > 0 and not preBar is None:
                """有形态识别出来
                """
                for item in rets:
                    name = item.name
                    value = item.value
                    total_count+=1
                    dataItem = None
                    if dataSet.__contains__(name):
                        dataItem = dataSet[name]
                    else:
                        dataItem = CountItem()
                        dataItem.values = [] ##形态被识别的值。
                        dataItem.pcts = []   ##识别之后第二天的盈利情况
                        dataSet[name] = dataItem
                    ##第二天的收益
                    pct = (bar.close_price - preBar.close_price) / preBar.close_price

                    ##收录当前形态
                    dataItem.count_total += 1
                    dataItem.pct_total += pct
                    if pct > 0.000001:
                        dataItem.count_earn += 1
                        dataItem.pct_earn += pct
                    dataItem.values.append(value)
                    dataItem.pcts.append(pct)

                pass
            indicator.update_bar(bar)
            preBar = bar

    ##打印当前形态
    print(f"总共分析{total_count}个形态，识别出{len(dataSet)}个形态，有意义的形态有：")
    for key,dataItem in dataSet.items():
        if dataItem.count_total < 1000:
            continue
        success_rate = 100 * dataItem.count_earn / dataItem.count_total
        if abs(int(success_rate - 50)) < 5:
            continue
        values = np.array(dataItem.values)
        pcts = np.array(dataItem.pcts) * 100

        count = len(values)
        long_values = []
        short_value =[]
        long_pcts = []
        long_ok_cnt = 0
        short_pcts = []
        short_ok_cnt = 0
        for i in range(0,count):
            v = values[i]
            if v > 0:
                long_values.append(v)
                long_pcts.append(pcts[i])
                if pcts[i] >=0.000001:
                    long_ok_cnt = long_ok_cnt+1
            else:
                short_value.append(v)
                short_pcts.append(pcts[i])
                if pcts[i] <= -10.000001:
                    short_ok_cnt = short_ok_cnt+1
        long_values = np.array(long_values)
        short_value = np.array(short_value)
        long_pcts = np.array(long_pcts)
        short_pcts = np.array(short_pcts)

        long_pct = 0
        long_std = math.nan
        long_success = math.nan

        short_pct = 0
        short_std = math.nan
        short_success = math.nan
        if len(long_values) > 0:
            long_pct = long_pcts.mean()
            long_std = long_pcts.std()
            long_success = long_ok_cnt / len(long_values)

        if len(short_value) > 0:
            short_pct = short_pcts.mean()
            short_std = short_pcts.std()
            short_success = short_ok_cnt / len(short_value)

        print(f"{key}： count={count},suc_reate=%.2f%%,long(size:{len(long_values)},suc=%.2f%%,pcts:%.2f%%,std=%.2f),short(size:{len(short_value)},suc=%.2f%%,pcts:%.2f%%,std=%.2f)" % (success_rate,long_success*100,long_pct,long_std,short_success*100,short_pct,short_std))

    print("-----------具体情况-----------")
    outputKeys = ["CDLADVANCEBLOCK"]
    for key in outputKeys:
        dataItem = dataSet[key]
        values = np.array(dataItem.values)
        pcts = np.array(dataItem.pcts) * 100
        count = len(dataItem.values);
        print(f"{key}： count={count},values:{values.mean()},pcts:%.2f%%,pcts_std=%.2f" % (pcts.mean(),pcts.std()))

        itemSize = 10
        size = int(count / itemSize)
        if count % itemSize > 0:
            size = size + 1
        for i in range(0,size):
            lineStr = ""
            start = itemSize * i
            end = min(start+itemSize, count)
            for j in range(start,end):
                lineStr = lineStr + (f" %4d->%.2f%%," % (values[j],pcts[j]))
            print(lineStr)


"""
统计申万行业的k线编码识别。
"""
def compute_SW_KEncode_data():
    from earnmi.data.SWImpl import SWImpl
    sw = SWImpl()
    lists = sw.getSW2List()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    dataSet = {}
    total_count = 0
    for code in lists:
        #for code in lists:
        barList = sw.getSW2Daily(code, start, end)
        indicator = Indicator(40)
        preBar = None
        for bar in barList:
            ##先识别形态
            kEncodeValue  = KPattern.encode3KAgo1(indicator)
            if kEncodeValue is None:
                indicator.update_bar(bar)
                preBar = bar
                continue
            total_count += 1
            dataItem:CountItem = None
            if dataSet.__contains__(kEncodeValue):
                dataItem = dataSet[kEncodeValue]
            else:
                dataItem = CountItem()
                dataSet[kEncodeValue] = dataItem
            ##第二天的收益
            pct = (bar.close_price - preBar.close_price) / preBar.close_price
            ##收录当前形态
            #dataItem.values.append(value)
            dataItem.count_total +=1
            dataItem.pct_total +=pct
            if pct>0.000001:
                dataItem.count_earn+=1
                dataItem.pct_earn+=pct
            indicator.update_bar(bar)
            preBar = bar

        ##打印当前形态
    print(f"总共分析{total_count}个形态，识别出{len(dataSet)}个形态，有意义的形态有：")
    for key, dataItem in dataSet.items():
       success_rate = 100 * dataItem.count_earn / dataItem.count_total
       if dataItem.count_total < 500:
             continue
       if abs(int(success_rate-50)) <5:
            continue

       earn_pct = 100 * dataItem.pct_earn / dataItem.count_earn
       if success_rate < 50:
           earn_pct = 100 * (dataItem.pct_total - dataItem.pct_earn) / (dataItem.count_total - dataItem.count_earn)
       avg_pct = 100 * dataItem.pct_total / dataItem.count_total

       occur_rate = 100*dataItem.count_total / total_count
       print(f"{key}： total={dataItem.count_total},suc=%.2f%%,occur_rate=%.2f%%,earn_pct:%.2f%%,avg_pct:%.2f%%)" % (success_rate,occur_rate,earn_pct,avg_pct))


"""
统计申万行业的k线编码识别。
"""
def compute_SW_KEncode_data():

    pass

if __name__ == "__main__":
    #compute_SW_KPattern_data()
    compute_SW_KEncode_data()