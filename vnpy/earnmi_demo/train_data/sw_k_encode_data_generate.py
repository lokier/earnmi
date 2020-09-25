
"""
申万行业指数：训练数据生成
"""
import urllib.request
import json
import re as regex
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from earnmi.chart.KPattern import KPattern
from earnmi.data.SWImpl import SWImpl
from earnmi.chart.Indicator import Indicator
from earnmi_demo.strategy_demo.holdbars.analysisKPattern import CountItem


def generateSWTrainData(start:datetime,end:datetime)-> pd.DataFrame:
    sw = SWImpl()
    lists = sw.getSW2List()
    dataSet = {}
    total_count = 0
    cloumns_name = ["code", "name", "kPattern", "k", "d", "dif", "dea", "open_price", "sell_price","buy_price","high_price","low_price"]
    cloumns = ["code", "name", "kPattern", "k", "d", "dif", "dea", "open_price", "sell_price","buy_price","high_price","low_price"]

    datas = []

    for code in lists:
        # for code in lists:
        barList = sw.getSW2Daily(code, start, end)
        indicator = Indicator(40)
        preBar = None
        for bar in barList:
            ##先识别形态
            kEncodeValue = KPattern.encode3KAgo1(indicator)
            if kEncodeValue is None:
                indicator.update_bar(bar)
                preBar = bar
                continue
            total_count += 1
            dataItem: CountItem = None
            if dataSet.__contains__(kEncodeValue):
                dataItem = dataSet[kEncodeValue]
            else:
                dataItem = CountItem()
                dataSet[kEncodeValue] = dataItem
            ##第二天的收益
            pct = ((bar.high_price + bar.close_price) / 2 - preBar.close_price) / preBar.close_price
            ##收录当前形态
            # dataItem.values.append(value)
            dataItem.count_total += 1
            dataItem.pct_total += pct
            if pct > 0.000001:
                dataItem.count_earn += 1
                dataItem.pct_earn += pct
            indicator.update_bar(bar)
            preBar = bar

        ##打印当前形态
    occur_count = 0
    print(f"总共分析{total_count}个形态，识别出{len(dataSet)}个形态，有意义的形态有：")
    max_succ_rate = 0
    min_succ_rate = 100
    for key, dataItem in dataSet.items():
        success_rate = 100 * dataItem.count_earn / dataItem.count_total
        if dataItem.count_total < 500:
            continue
        if abs(int(success_rate - 50)) < 10:
            continue

        earn_pct = 100 * dataItem.pct_earn / dataItem.count_earn
        if success_rate < 50:
            earn_pct = 100 * (dataItem.pct_total - dataItem.pct_earn) / (dataItem.count_total - dataItem.count_earn)
        avg_pct = 100 * dataItem.pct_total / dataItem.count_total
        occur_count += dataItem.count_total
        occur_rate = 100 * dataItem.count_total / total_count
        max_succ_rate = max(success_rate, max_succ_rate)
        min_succ_rate = min(success_rate, min_succ_rate)
        print(f"{key}： total={dataItem.count_total},suc=%.2f%%,occur_rate=%.2f%%,earn_pct:%.2f%%,avg_pct:%.2f%%)" % (
        success_rate, occur_rate, earn_pct, avg_pct))

    total_occur_rate = 100 * occur_count / total_count
    print(f"总共：occur_rate=%.2f%%, min_succ_rate=%.2f%%, max_succ_rate=%.2f%%" % (
    total_occur_rate, min_succ_rate, max_succ_rate))
    return wxl


if __name__ == "__main__":
    ## 开始时间2014-6-30
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)

    writer=pd.ExcelWriter('sw_train_data_sample.xlsx')
    sampld_data_df = generateSWTrainData(start,end)
    sampld_data_df.to_excel(writer,sheet_name="sample")

    writer.save()
    writer.close()