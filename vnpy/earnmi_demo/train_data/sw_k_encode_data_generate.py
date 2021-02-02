
"""
申万行业指数：训练数据生成
"""
import urllib.request
import json
import re as regex
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from earnmi.chart.KPattern2 import KPattern
from earnmi.data.SWImpl import SWImpl
from earnmi.chart.Indicator import Indicator


def generateSWTrainData(kPatterns:[],start:datetime,end:datetime)-> pd.DataFrame:
    sw = SWImpl()
    lists = sw.getSW2List()
    cloumns = ["code", "name", "kPattern", "k", "d", "dif", "dea", "macd","open", "short","long"]
    datas = []
    kPatternMap = {}
    for kPatternValues in kPatterns:
        kPatternMap[kPatternValues] = True

    macd_list = []

    for code in lists:
        # for code in lists:
        name = sw.getSw2Name(code)
        barList = sw.getSW2Daily(code, start, end)
        indicator = Indicator(34)
        preBar = None
        for bar in barList:
            ##先识别形态
            kEncodeValue = None
            if indicator.inited:
                tmpKEncodeValue = KPattern.encode3KAgo1(indicator)
                if kPatternMap.__contains__(tmpKEncodeValue):
                    kEncodeValue = tmpKEncodeValue
            if kEncodeValue is None:
                indicator.update_bar(bar)
                preBar = bar
                continue
            ##昨天的kdj
            k,d,j = indicator.kdj(array=False)
            dif,dea,macd = indicator.macd(fast_period=12, slow_period=26, signal_period=9,array=False)

            ##第二天的收益
            short_pct = 100 * ((bar.high_price + bar.close_price) / 2 - preBar.close_price) / preBar.close_price
            long_pct = 100 * ((bar.low_price + bar.close_price) / 2 - preBar.close_price) / preBar.close_price
            open_pct = 100 * (bar.open_price - preBar.close_price) / preBar.close_price

            item = []
            item.append(code)
            item.append(name)
            item.append(kEncodeValue)
            item.append(k)
            item.append(d)
            item.append(dif)
            item.append(dea)
            item.append(macd)
            #下个k线数据
            item.append(open_pct)
            item.append(short_pct)
            item.append(long_pct)
            datas.append(item)

            macd_list.append(macd)

            indicator.update_bar(bar)
            preBar = bar
    macd_list = np.array(macd_list)
    print(f"total size : {len(datas)},mean ={macd_list.mean()},max={macd_list.max()},min={macd_list.min()}")
    wxl = pd.DataFrame(datas, columns=cloumns)
    return wxl


if __name__ == "__main__":
    ## 开始时间2014-6-30
    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    kPattrns = [33214, 33134, 33297, 39858, 33296, 39775, 33135, 26736, 39857, 39777, 33133, 46418, 39776, 33215, 33216, 39856, 39694, 26573, 33213, 39696, 33377, 33295, 26735, 39938, 46337, 33217, 46338, 39695, 26734, 26574, 33053]
    kPattrns = [33214]
    writer=pd.ExcelWriter('files/sw_train_data_sample_33214.xlsx')
    sampld_data_df = generateSWTrainData(kPattrns,start,end)
    sampld_data_df.to_excel(writer,sheet_name="sample",index=False)

    writer.save()
    writer.close()