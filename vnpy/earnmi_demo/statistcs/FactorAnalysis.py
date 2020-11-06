import numpy as np
import talib
import numpy as np  # 数组相关的库
import matplotlib.pyplot as plt  # 绘图库
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange


class _FactoryItem:
    def __init__(self):
        self.value_list = []
        self.pct_list = []

class FactoryParser:

    def __init__(self,name:str):
        name = str;
        self.factorMap = {}

    """
    factory_elemen_name : 因子元素名称
    factory_value：因子值
    pct_result： 因子值对应的pctList结果,代表后续每天的涨幅情况。
    """
    def put(self,factor_value:float,pct_list:float):
       pass

    """
    分析因子数据的最后百分占比情况
    lastRadio: 分析最后百分比。
    """
    def printLast(self, pct_range:[],lastRadio = None):
        pass