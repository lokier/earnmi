from dataclasses import dataclass
from datetime import datetime

import numpy as np
import talib

import time
import sched

from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.model.bar import LatestBar
from earnmi.model.op import OpOrder
from earnmi.uitl.jqSdk import jqSdk

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif']=['SimHei'] #显示中文标签
#plt.rcParams['axes.unicode_minus']=False   #这两行需要手动设置
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)


#[[min:1.00)=0.00%,[1.00:3.00)=72.29%,[3.00:5.00)=21.56%,[5.00:8.00)=6.13%,[8.00:12.00)=0.02%,[12.00:15.00)=0.00%,[15.00:max)=0.00%,]
"""
天数[1,3)的pct均值为：0.3766889008876466
           天数[3,5)的pct均值为：4.460444868507723
           天数[5,8)的pct均值为：8.187512883858655
           天数[8,12)的pct均值为：7.994340290060141
"""
#
labels = ['min~1.00','1.00~3.00','3.00~5.00','5.00~8.00','8.00~12.00']
sizes = [0.0,72.29,21.56,6.13,0.02]

# labels = ['娱乐','育儿','饮食','房贷','交通','其它']
# sizes = [2,5,12,70,2,9]
# explode = (0,0,0,0.1,0)
plt.pie(sizes,labels=labels,autopct='%1.1f%%',shadow=False,startangle=150)
plt.title("饼图示例-8月份家庭支出")
plt.show()

