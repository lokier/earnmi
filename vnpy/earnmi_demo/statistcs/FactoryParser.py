import numpy as np
import talib
import numpy as np  # 数组相关的库
import matplotlib.pyplot as plt  # 绘图库
from earnmi.chart.FloatEncoder import FloatEncoder,FloatRange2


class _FactoryItem:
    def __init__(self):
        self.value_list = []
        self.pct_list = []

class FactoryParser:

    def __init__(self):
        self.factorMap = {}

    """
    factory_elemen_name : 因子元素名称
    factory_value：因子值
    pct_result： 因子值对应的pct结果。
    """
    def put(self,factory_elemen_name:str,factory_value:float,pct:float):
        factory_item = self.factorMap.get(factory_elemen_name)
        if factory_item is None:
            factory_item = _FactoryItem()
            self.factorMap[factory_elemen_name] = factory_item
        factory_item.value_list.append(factory_value)
        factory_item.pct_list.append(pct)

    """
     计算分布情况。
    """
    def printRange(self):
        for factory_elemen_name, factory_item in self.factorMap.items():
            value_list = np.array(factory_item.value_list)
            pct_list = np.array(factory_item.pct_list)
            size = len(value_list)
            _min, _max = [value_list.min(), value_list.max()]
            print(f"name:{factory_elemen_name} , size:{size}, maxFactory:%.2f,minFactory:%.2f,avgPct:%.2f" % (_max, _min, pct_list.mean()))
            N = 6
            spli_list = []
            for i in range(0, N + 1):
                spli_list.append(_min + i * (_max - _min) / N)
            dif_encoder = FloatEncoder(spli_list)
            print( f"      值分布:{FloatRange2.toStr(dif_encoder.computeValueDisbustion(value_list), dif_encoder)}")

    """
        计算相关性情况。
        注意，为了避免同一个值对应不同的值，所以这里做个去重的操作，就是相同key值范围对应的value都会取平均值。
    """
    def printCORREL(self,factory_split_n=5000):
        for factory_elemen_name, factory_item in self.factorMap.items():
            value_list = np.array(factory_item.value_list)
            pct_list = np.array(factory_item.pct_list)
            size = len(value_list)
            _min, _max = [value_list.min(), value_list.max()]
            print(f"name:{factory_elemen_name} , size:{size}, maxFactory:%.2f,minFactory:%.2f,avgPct:%.2f" % (_max, _min, pct_list.mean()))
            N = factory_split_n
            spli_list = []
            for i in range(0, N + 1):
                spli_list.append(_min + i * (_max - _min) / N)
            dif_encoder = FloatEncoder(spli_list,minValue=_max,maxValue=_max)
            ##继续按因子值分割，避免过大
            rangeMap = {}
            for i in range(0,size):
                f_value = value_list[i]
                pct = pct_list[i]
                key = dif_encoder.encode(f_value)
                item = rangeMap.get(key)
                if item is None:
                    item = _FactoryItem()
                    rangeMap[key] = item
                item.value_list.append(f_value)
                item.pct_list.append(pct)
            final_value_list = []
            fianl_pct_list = []
            for key,item in rangeMap.items():
                avg_v = float(np.array(item.value_list).mean())
                avg_pct = float(np.array(item.pct_list).mean())
                final_value_list.append(avg_v)
                fianl_pct_list.append(avg_pct)

            CORRELLen = len(final_value_list)
            r1 = talib.CORREL(np.array(final_value_list), np.array(fianl_pct_list), timeperiod=CORRELLen)
            print( f"      相关性:%.4f    相关性ListSize:{CORRELLen}"  % (r1[-1]))


    def savePng(self,minValue=16.6655555,maxValue = None):
        for factory_elemen_name, factory_item in self.factorMap.items():
            value_list = factory_item.value_list
            pct_list = factory_item.pct_list
            size = len(value_list)
            if not minValue is None or not  maxValue is None:
                filter_v_list = []
                fitler_pct_list = []
                for i in range(0,size):
                    v = value_list[i]
                    if not minValue is None and v < minValue:
                        continue
                    if not maxValue is None and v > maxValue:
                        continue
                    filter_v_list.append(v)
                    fitler_pct_list.append(pct_list[i])
                value_list = np.array(filter_v_list)
                pct_list = np.array(fitler_pct_list)
                size = len(value_list)
            else:
                value_list = np.array(value_list)
                pct_list = np.array(pct_list)
            _min, _max = [value_list.min(), value_list.max()]

            dif_encoder = FloatEncoder([-1,1])
            print(f"name:{factory_elemen_name} , size:{size}, maxFactory:%.2f,minFactory:%.2f,avgPct:%.2f" % (_max, _min, pct_list.mean()))
            print( f"      pct值分布:{FloatRange2.toStr(dif_encoder.computeValueDisbustion(pct_list), dif_encoder)}")

            # plt.scatter(value_list, pct_list, alpha=0.15,marker='.')  #
            # plt.show()