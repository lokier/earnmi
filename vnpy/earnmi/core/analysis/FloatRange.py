from collections import defaultdict
from dataclasses import dataclass
from functools import cmp_to_key
from typing import Sequence

import numpy as np

__all__ = [
    # Super-special typing primitives.
    'FloatRange',
    'FloatDistribute',
    'FloatDistributeItem',
    'FloatParser',
]

class FloatRange:
    """

    """
    def __init__(self,min:float,max:float,split_size:int):
        """
        创建一个浮点值的区间块，split_size必须大于0的整数。
        """
        assert split_size > 0
        self.split_value = (max-min)/(float(split_size))
        self._range_list = [min+float(i)*self.split_value for i in range(0,split_size+1)]

    def items(self,reverse =False):
        """
        区间值
        """
        if reverse:
            return list(reversed(self._range_list))
        else:
            return list(self._range_list)

    def indexSize(self)->int:
        """
        区间编码值尺寸。
        """
        return len(self._range_list) + 1

    def encodeIndex(self,value:float)->int:
        """
        将某个浮点值，编码到某一个区间值。
        """
        if value is None:
            return None
        code = 0
        n = len(self._range_list)
        for i in range(n, 0, -1):
            if value >= self._range_list[i - 1]:
                code = i
                break
        return code

    def decodeIndex(self,index,negative_infinite=None,positive_infinite= None)->[]:
        """
        解码Index值，返回区间范围[lef,right)
        参数:
            negative_infinite：如果返回的区间含有负无穷大，则可以指定返回的负无穷大值，默认为min-1
            positive_infinite：如果返回的区间含有正无穷大，则可以指定返回的正无穷大值，默认为max+1
        """
        n = len(self._range_list)
        if index < 0 or index > n:
            raise RuntimeError("out of range encode")
        if index == 0:
            return  [negative_infinite, self._range_list[0]]
        if index < n:
            return [self._range_list[index - 1], self._range_list[index]]
        return [self._range_list[n - 1], positive_infinite]

    def __str__(self):
        return f"FloatRange:{self._range_list}"

    def calculate_distribute(self,values:Sequence['float']):
        return FloatDistribute(self,values)

@dataclass
class FloatDistributeItem(object):

    index:int   ##所属区间的编码值

    left:float  ##  区间[left,right)中的left值

    right:float  ##  区间[left,right)中right值

    probal: float = None  ##区间的分布概率值

    values:['float'] = None  #在该区间具体分布的区间值

    def __post_init__(self):
        self.values = []
        self.probal = 0

def __FloatRangeCompare__(d1, d2):
    return d1.probal - d2.probal

@dataclass
class _float_distbute_show_item:
    probal:float   ##概率值
    text:str       ## 区间文本值
    avg_value:float  ##平均值

class FloatDistribute:

    """
    浮点值分布情况。
    """
    def __init__(self,range:FloatRange,values:['float']):
        self._frange = range
        self._values = values
        self._distribute_item:Sequence['FloatDistributeItem'] = self._cal_items(range,values)


    def items(self,reverse = True)->['FloatDistributeItem']:
        """
        获取分布情况。默认按大到小排序
        """
        if not reverse:
            return list(reversed(self._distribute_item))
        else:
            return list(self._distribute_item)

    def _cal_show_items(self,reverse = True,negative_infinite='MIN',positive_infinite= 'MAX',limit_show_count = 5):
        item_list = self.items(reverse)
        limit_size = len(item_list)
        if not limit_show_count is None:
            limit_size = min(limit_show_count -1, limit_size)
        other_probal = None
        show_item_list = []
        for i in range(0, len(item_list)):
            r: FloatDistributeItem = item_list[i]
            if i < limit_size:
                _min, _max = r.left, r.right
                left,right = r.left,r.right
                if _min is None:
                    _min = negative_infinite
                    left = r.right - self._frange.split_value
                else:
                    _min = f"%.2f" % _min
                if _max is None:
                    _max = positive_infinite
                    right = r.left + self._frange.split_value
                else:
                    _max = f"%.2f" % _max
                show_item = _float_distbute_show_item(probal=r.probal, text=f"[{_min}:{_max})",avg_value=left+right / 2)
                show_item_list.append(show_item)
            else:
                if other_probal is None:
                    other_probal = 0.0
                other_probal += r.probal
        if not other_probal is None:
            show_item = _float_distbute_show_item(probal=other_probal, text="other",avg_value=None)
            show_item_list.append(show_item)
        return show_item_list

    def toStr(self,reverse = True,negative_infinite='MIN',positive_infinite= 'MAX',limit_show_count = 5)->str:
        """
        分布情况
        """
        show_item_list = self._cal_show_items(reverse,negative_infinite,positive_infinite,limit_show_count)
        info = f"size={len(self._values) }"
        for item in show_item_list:
            info += f",{item.text}=%.2f%%" % (100 * item.probal)
        return info


    def showPipChart(self,title = "None",reverse = True,negative_infinite='MIN',positive_infinite= 'MAX',limit_show_count = 5):
        """
        生成饼图
        """
        import matplotlib.pyplot as plt
        import numpy as np
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 显示中文标签
        # plt.rcParams['axes.unicode_minus']=False   #这两行需要手动设置
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        show_item_list = self._cal_show_items(reverse,negative_infinite,positive_infinite,limit_show_count)
        labels = [ item.text for item in show_item_list]
        sizes = [ item.probal for item in show_item_list]
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=False, startangle=150)
        plt.title(title)
        plt.show()
        pass


    def _cal_items(self, frange: FloatRange, value_list: ['float']) -> []:
        totalCount = len(value_list)
        distrubute_map = {}
        for value in value_list:
            index = frange.encodeIndex(value)
            item: FloatDistributeItem = distrubute_map.get(index)
            if item is None:
                left, right = frange.decodeIndex(index)
                item = FloatDistributeItem(index=index, left=left, right=right)
                distrubute_map[index] = item
            item.values.append(value)
        item_list = distrubute_map.values()
        for item in item_list:
            if totalCount > 0:
                count = len(item.values)
                item.probal = count / totalCount
        return sorted(item_list, key=cmp_to_key(__FloatRangeCompare__), reverse=True)

class FloatParser:

    def __init__(self,values:['float']):
        pass

    def find_best(self,):
        """
        返回区间最集中的范围。
        """
        pass

if __name__ == "__main__":

    float_range = FloatRange(-7,7,14)
    #print(f"decode_size:{float_range.indexSize()},{float_range.items()}")

    assert float_range.encodeIndex(-7.0) == 1
    assert float_range.encodeIndex(-7.01) == 0
    assert float_range.encodeIndex(14) == 15
    assert float_range.encodeIndex(-3.0) == 5
    assert float_range.encodeIndex(-0.5) == 7
    assert float_range.encodeIndex(2.5) == 10
    assert float_range.encodeIndex(7) == 15
    assert float_range.encodeIndex(6.99999) == 14

    assert float_range.decodeIndex(0) == [None,-7.0]
    assert float_range.decodeIndex(0,negative_infinite=-10) == [-10,-7.0]
    assert float_range.decodeIndex(0,negative_infinite=None) == [None,-7.0]
    assert float_range.decodeIndex(1) == [-7.0,-6.0]
    assert float_range.decodeIndex(2) == [-6.0,-5.0]
    assert float_range.decodeIndex(3) == [-5.0,-4.0]
    assert float_range.decodeIndex(4) == [-4.0,-3.0]
    assert float_range.decodeIndex(14) == [6.0,7.0]
    assert float_range.decodeIndex(15) == [7.0,None]
    assert float_range.decodeIndex(15,positive_infinite=10) == [7.0,10]

    float_range = FloatRange(-10,10,20)  #生成浮点值范围区间对象
    values = np.random.uniform(low=-10.0, high=10.0, size=100)  ##随机生成涨幅情况
    dist = float_range.calculate_distribute(values)

    print(f"dist:{dist.toStr()}")


    # item_list = dist.items()
    # print(f"dist:{dist.toStr()}")
    # print(f"dist 0:{item_list[0].values}")
    # print(f"dist 1:{item_list[1].values}")
    #
    dist.showPipChart()

