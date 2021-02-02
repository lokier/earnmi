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
        self.min = min
        self.max = max
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
            negative_infinite：如果返回的区间含有负无穷大，则可以指定返回的负无穷大值，默认为min-区间间隔值
            positive_infinite：如果返回的区间含有正无穷大，则可以指定返回的正无穷大值，默认为max+区间间隔值
        """
        n = len(self._range_list)
        if index < 0 or index > n:
            raise RuntimeError("out of range encode")
        if index == 0:
            negative_infinite =  self._range_list[0] - self.split_value if negative_infinite is None else negative_infinite
            return  [negative_infinite, self._range_list[0]]
        if index < n:
            return [self._range_list[index - 1], self._range_list[index]]
        positive_infinite = self._range_list[n - 1] + self.split_value if positive_infinite is None else positive_infinite
        return [self._range_list[n - 1], positive_infinite]

    def __str__(self):
        return f"FloatRange:{self._range_list}"

    def calculate_distribute(self,values:Sequence['float']):
        return FloatDistribute(values,self)

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
    def __init__(self,values:['float'],range:FloatRange = None):
        values = np.array(values)
        if range is None:
            low = values.min()
            hight = values.max()
            split_size = 15
            range = FloatRange(low,hight,split_size)
        assert len(values) > 0
        self._frange = range
        self._values = values
        self._distribute_item:Sequence['FloatDistributeItem'] = self._cal_items(range,values)


    def items(self,reverse = True)->['FloatDistributeItem']:
        """
        获取分布情况。默认按大到小排序
        参数:
            reverse: Ture，按分布大小降序排列，false，按分布大小升序排列，None: 按区间顺序排列

        """
        if reverse is None:
            def __the_cmp(a1,a2):
                return a1.index - a2.index
            return sorted(self._distribute_item,key=cmp_to_key(__the_cmp), reverse=False)

        if not reverse:
            ##降序排列
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
                show_item = _float_distbute_show_item(probal=r.probal, text=f"[{_min}:{_max})",avg_value=(left+right) / 2)
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
        info = ""
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

    def showLineChart(self,title="None"):
        show_item_list = self._cal_show_items(True, None, None, None)
        def __my_compare(a1, a2):
            return a1.avg_value - a2.avg_value

        _item_list = sorted(show_item_list, key=cmp_to_key(__my_compare), reverse=False)
        import matplotlib.pyplot as plt
        # 这两行代码解决 plt 中文显示的问题
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        #data = [[item.avg_value,item.probal*100] for item in _item_list]
        y = [item.probal * 100 for item in _item_list]
        x = [item.avg_value for item in _item_list]
        plt.xlim(xmin=self._frange.min, xmax=self._frange.max)

        plt.plot(x,y)
        plt.scatter(x, y)
        plt.ylabel('分布概率%')
        plt.xlabel('涨幅情况%')

        plt.title(title)
        plt.show()



    def _cal_items(self, frange: FloatRange, value_list: ['float']) -> []:
        totalCount = len(value_list)
        distrubute_map = {}
        ###初始化
        # for index in range(0,frange.indexSize()):
        #     left, right = frange.decodeIndex(index)
        #     item = FloatDistributeItem(index=index, left=left, right=right)
        #     distrubute_map[index] = item
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
            count = len(item.values)
            item.probal = count * 1.0 / totalCount

        ##assert len(item_list) == frange.indexSize()
        return sorted(item_list, key=cmp_to_key(__FloatRangeCompare__), reverse=True)

class FloatParser:

    def __init__(self,low:float,high:float):
        """
        设置涨幅上、下限。
        """
        self.low = low
        self.high = high
        assert low < high
        # if abs(low) < 1 or abs(high) < 1:
        #     raise RuntimeError("涨跌幅上限必须大于1的值，否则会丢失浮点精度")

    def calc_op_score(self,values:[],delta_value:float = None)->float:
        """
        计算该涨幅情况具备可操作得分值。得分值越高越具备可操作性。
        """
        if delta_value is None:
            delta_value = (self.high - self.low) / 12
        ret_value = self.find_best_range(values,delta_value)

        ##取前3个，去点最靠近0的那个分布
        closest_0_index = 0
        size = min(len(ret_value),3)
        for i in range(1,size):
            if abs(ret_value[closest_0_index][0]) > abs(ret_value[i][0]):
                closest_0_index = i
                pass
        score = 0.0
        for i in range(0, size):
            if i!= closest_0_index and ret_value[i][0] > 0:
                score += ret_value[i][0]*ret_value[i][1]

        return score

    def find_best_range(self,values:[],delta_value:float):
        """
        找出涨幅值中区间范围差值为delta_value(即right-legt = delta_value)的间最优的几个区间值
        返回:
            [[区间(left,righ)平均值，分布值]....]
            即[[(left1+right1)/2, probal1][(left2+right2)/,proboal2]]
        """
        low = self.low
        hight = self.high
        range_size = 15   ##粒度为15
        split = delta_value / float(range_size)
        split_size = int((hight-low) / split)
        frange = FloatRange(low,hight,split_size)

        dist = frange.calculate_distribute(values);
        dist_items = dist.items(reverse=None)

        ret_list = []
        while True:
            best_probal = 0
            best_range_value = 0
            best_start=0
            best_end = 0
            for i in range(0,len(dist_items)):
                _start = max(0, i - range_size)
                _end = i
                _probal_total = 0
                for j in range(_start, _end + 1):
                    _probal_total+= dist_items[j].probal
                if _probal_total > best_probal:
                    best_probal = _probal_total
                    best_range_value = (dist_items[_start].left + dist_items[_end].right) / 2
                    best_start = _start
                    best_end = _end
            if best_probal <= 0:
                break
            #print(f"{[best_range_value,best_probal]}")
            ret_list.append([best_range_value,best_probal])
            ##去除当前最好的区域
            for j in range(best_start, best_end + 1):
                dist_items[j].probal = -100

        # for i in range(0, len(dist_items)):
        #     if dist_items[i].probal == -100:
        #         dist_items[i].probal = 0
        #
        # dist.showBarChart()
        return ret_list


    def showLineChart(self, values:[],title="None"):
        """
        生成条形图
        """
        frange = FloatRange(self.low,self.high,50)
        dist = frange.calculate_distribute(values)
        dist.showLineChart(title)


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

    assert float_range.decodeIndex(0) == [-8.0,-7.0]
    assert float_range.decodeIndex(0,negative_infinite=-10) == [-10,-7.0]
    assert float_range.decodeIndex(0,negative_infinite=None) == [-8.0,-7.0]
    assert float_range.decodeIndex(1) == [-7.0,-6.0]
    assert float_range.decodeIndex(2) == [-6.0,-5.0]
    assert float_range.decodeIndex(3) == [-5.0,-4.0]
    assert float_range.decodeIndex(4) == [-4.0,-3.0]
    assert float_range.decodeIndex(14) == [6.0,7.0]
    assert float_range.decodeIndex(15) == [7.0,8.0]
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
    #dist.showPipChart()
    #dist.showBarChart()


    values = np.random.uniform(low=-10, high=10, size=500)  ##随机生成涨幅情况
    fPrarser = FloatParser(-10,10)
    fPrarser.showBarChart(values)

    # result = fPrarser.find_best_range(values,2.0)
    # print(f"{result}")




