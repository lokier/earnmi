from functools import cmp_to_key

import numpy as np
import talib
import numpy as np  # 数组相关的库
import matplotlib.pyplot as plt  # 绘图库
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange


class _Item:
    def __init__(self,v,pct_list):
        self.value = v
        self.pct_list = pct_list

    def __eq__(self, o: object) -> bool:
        return self.value.__eq__(o.value)

    def __hash__(self) -> int:
        return self.value.__hash__()

def _item_cmp(o1,o2):
    return o1.value - o2.value

class FactoryAnalysis:

    def __init__(self,name:str):
        self.name = name
        self.itemList = []

    """
    factory_value：因子值
    pct_result： 因子值对应的pct在各个天的涨幅情况。
    """
    def put(self,factor_value:float,pct_list:np.ndarray):
       self.itemList.append(_Item(factor_value,pct_list))

    """
    分析因子数据的最后百分占比情况，因子对应的在各个天数维度的涨幅情况。
    lastRadio: 分析最后百分比。
    """
    def printLast(self,lastRadio = 0.1):
        totalSize = len(self.itemList)
        itemList = sorted(self.itemList,key=cmp_to_key(_item_cmp),reverse=False)
        startIndex = int(totalSize * lastRadio)
        subList =itemList[totalSize - startIndex:]
        size = len(subList)
        ##开始打印各个参数的情况。
        pctRangeSize = len(subList[0].pct_list)

        factor_value = np.full(size,None)  ###因子值
        for i in range(0, size):
            item: _Item = subList[i]
            factor_value[i] = item.value

        print(f"name:{self.name} , 总数:{totalSize},取最后{lastRadio*100}%%数据共{size}个, maxFactor:%.2f,minFactor:%.2f" % (
            factor_value.max(),factor_value.min()))
        ###统计因子值在不同天数的维度情况
        dif_encoder = FloatEncoder([-1, 1])
        for day in range(0,pctRangeSize):
            item_desc = f"第{day+1}天的pct涨幅"
            pct_values = []
            for i in range(0,size):
                item:_Item = subList[i]
                pct = item.pct_list[day]
                pct_values.append(pct)
            pct_values = np.array(pct_values)
            print(f"  {item_desc}:{FactoryAnalysis.keep_3_float(pct_values.mean())},pct值分布:{FloatRange.toStr(dif_encoder.computeValueDisbustion(pct_values), dif_encoder)}")

    def __get_avg_pct(self,pct_range,pct_list:np.ndarray):
        startIndex = pct_range[0]
        endIndex = pct_range[1]
        return pct_list[startIndex:endIndex].mean()

    def keep_3_float(value: float) -> float:
        return int(value * 1000) / 1000

    def __to_list(self,pctSize):
       if pctSize == 1:
           return [[0,1]]
       if pctSize == 2:
           return [[0,2]]
       if pctSize == 3:
           return [[0,1],[1,2],[2,3],[0,3]]
       if pctSize == 4:
           return [[0,2],[2,4],[0,4]]
       if pctSize == 5:
           return [[0,3],[3,5],[0,5]]
       else:
           index1 = int(pctSize/3)
           index12 =int(2*pctSize/3)
           return [[0, index1],[index1, index12],[index12, pctSize],[0,pctSize]]
