


"""
统计所有的行业情况所有的形态识别情况。 识别某种k线形态并判断是否可以分类
"""
import math
from datetime import datetime
import numpy as np
from earnmi.chart.Indicator import Indicator
from earnmi.chart.KEncode import KEncode
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
                    short_pct = ((bar.high_price + bar.close_price) / 2 - preBar.close_price) / preBar.close_price
                    #long_pct = ((bar.high_price + bar.close_price) / 2 - preBar.close_price) / preBar.close_price

                    ###pct = (bar.close_price - preBar.close_price) / preBar.close_price

                    ##收录当前形态
                    dataItem.count_total += 1
                    dataItem.pct_total += short_pct
                    if short_pct > 0.000001:
                        dataItem.count_earn += 1
                        dataItem.pct_earn += short_pct
                    dataItem.values.append(value)
                    dataItem.pcts.append(short_pct)

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
            pct = ((bar.high_price + bar.close_price) / 2 - preBar.close_price) / preBar.close_price
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
    occur_count = 0
    print(f"总共分析{total_count}个形态，识别出{len(dataSet)}个形态，有意义的形态有：")
    max_succ_rate = 0
    min_succ_rate = 100
    ret_list = []
    for key, dataItem in dataSet.items():
       success_rate = 100 * dataItem.count_earn / dataItem.count_total
       if dataItem.count_total < 500:
             continue
       if abs(int(success_rate-50)) <10:
            continue
       ret_list.append(key)
       earn_pct = 100 * dataItem.pct_earn / dataItem.count_earn
       if success_rate < 50:
           earn_pct = 100 * (dataItem.pct_total - dataItem.pct_earn) / (dataItem.count_total - dataItem.count_earn)
       avg_pct = 100 * dataItem.pct_total / dataItem.count_total
       occur_count += dataItem.count_total
       occur_rate = 100*dataItem.count_total / total_count
       max_succ_rate = max(success_rate,max_succ_rate)
       min_succ_rate = min(success_rate,min_succ_rate)
       print(f"{key}： total={dataItem.count_total},suc=%.2f%%,occur_rate=%.2f%%,earn_pct:%.2f%%,avg_pct:%.2f%%)" % (success_rate,occur_rate,earn_pct,avg_pct))

    total_occur_rate = 100 * occur_count / total_count
    print(f"总共：occur_rate=%.2f%%, min_succ_rate=%.2f%%, max_succ_rate=%.2f%%" % (total_occur_rate,min_succ_rate,max_succ_rate))
    print(f"{ret_list}")


"""
计算KEncode_parseAlgro1的分割在sw的动态分布情况
"""
def compute_SW_KEncode_parseAlgro1_split(
        pct_split = [-7,-5, -3, -1.5, -0.5, 0.5, 1.5, 3, 5, 7]
        ,extra_split = [1, 2, 3]):
    from earnmi.data.SWImpl import SWImpl
    sw = SWImpl()
    lists = sw.getSW2List()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    dataSet = {}

    total_count = 0
    pct_code_count = np.zeros(9)
    high_extra_pct_code_count = np.zeros(3)
    low_extra_pct_code_count = np.zeros(3)

    for code in lists:
        #for code in lists:
        barList = sw.getSW2Daily(code, start, end)
        indicator = Indicator(40)
        preBar = None
        for i in range(0,len(barList)):
            bar = barList[i]
            indicator.update_bar(bar)

            if (i > 10):
                k_code,pct_code,high_extra_pct_code,low_extra_pct_code = KEncode.parseAlgro1(indicator.close[-2], indicator.open[-1], indicator.high[-1],
                                              indicator.low[-1], indicator.close[-1],pct_split,extra_split)
                high_extra_pct_code_count[high_extra_pct_code] =  high_extra_pct_code_count[high_extra_pct_code] + 1
                low_extra_pct_code_count[low_extra_pct_code] =  low_extra_pct_code_count[low_extra_pct_code] + 1
                pct_code_count[pct_code] =  pct_code_count[pct_code] + 1
                total_count += 1
            preBar = bar

        ##打印当前形态
    print(f"pct_split: {pct_split}")
    print(f"extra_split: {extra_split}")

    count_list = pct_code_count
    print(f"应该服从正太分布" )
    print(f"\n：pct_code_count分布,avg = %.4f%%" % ( 100 / len(count_list)))
    for codeId in range(0,len(count_list)):
        item_count = count_list[codeId]
        item_occur_rate = 100 * item_count / total_count
        print(f"\t{codeId}: %.4f  %%   count:%d" % (item_occur_rate,item_count))

    count_list = high_extra_pct_code_count
    print(f"\n：high_extra_pct_code_count分布,avg = %.4f%%" % ( 100 / len(count_list)))
    for codeId in range(0, len(count_list)):
        item_count = count_list[codeId]
        item_occur_rate = 100 * item_count / total_count
        print(f"\t{codeId}: %.4f  %%   count:%d" % (item_occur_rate,item_count))

    count_list = low_extra_pct_code_count
    print(f"\n：low_extra_pct_code_count分布,avg = %.4f%%" % ( 100 / len(count_list)))
    for codeId in range(0, len(count_list)):
            item_count = count_list[codeId]
            item_occur_rate =100 *  item_count / total_count
            print(f"\t{codeId}: %.4f  %%   count:%d" % (item_occur_rate,item_count))


if __name__ == "__main__":
    #compute_SW_KPattern_data()
    compute_SW_KEncode_data()
    #compute_SW_KEncode_parseAlgro1_split();