


"""
统计所有的行业情况所有的形态识别情况
"""
from datetime import datetime
import numpy as np
from earnmi.chart.Indicator import Indicator
from earnmi.chart.PatternMatch import PatternMatch

"""
统计申万行业的k线形态识别
"""
def compute_SW_KPattern_data():
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

        count = len(values)
        long_values = []
        short_value =[]
        long_pcts = []
        short_pcts = []
        for i in range(0,count):
            v = values[i]
            if v > 0:
                long_values.append(v)
                long_pcts.append(pcts[i])
            else:
                short_value.append(v)
                short_pcts.append(pcts[i])
        long_values = np.array(long_values)
        short_value = np.array(short_value)
        long_pcts = np.array(long_pcts)
        short_pcts = np.array(short_pcts)

        print(f"{key}： count={count},long(values:{long_values.mean()},pcts:%.2f%%,std=%.2f),short(values:{short_value.mean()},pcts:%.2f%%,std=%.2f)" % (long_pcts.mean(),long_pcts.std(),short_pcts.mean(),short_pcts.std()))

    print("-----------具体情况-----------")
    outputKeys = ["CDLABANDONEDBABY","CDLHIKKAKE"]
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


if __name__ == "__main__":
    compute_SW_KPattern_data()