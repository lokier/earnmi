from dataclasses import dataclass

import numpy as np
import talib


@dataclass()
class X_FEATURE:
    x_feature: []  ##X特征值
    def __eq__(self, o: object) -> bool:
        return self.x_feature.__eq__(o.x_feature)
    def __hash__(self) -> int:
        h = 1
        for x in self.x_feature:
            h = h * x
        return hash(h)


x1 = X_FEATURE(x_feature=[1,2,3,4,5])
x2 = X_FEATURE(x_feature=[1,2,3,4,3])
x3 = X_FEATURE(x_feature=[1,2,3,4,5])
x4 = X_FEATURE(x_feature=[1,2,3,4,3])
x5 = X_FEATURE(x_feature=[1,2,3,4,5])

xMap = {}
xMap[x1] = True
xMap[x2] = True
xMap[x3] = True
xMap[x4] = True
xMap[x5] = True
print(f"xMap.size = {len(xMap)}")

assert not xMap.get(x5) is None
assert xMap.get(X_FEATURE(x_feature=[1,1,3,4,5])) is None
assert len(xMap)==2


params = {
    'wwf':[1,None,5],
    'zx':['sd',None,'dd']
}
"""
params = {
    'wwf':[1,None,5],
    'zx':['sd',None,'dd']
}
{'wwf': 1, 'zx': 'sd'}
{'wwf': 1, 'zx': None}
{'wwf': 1, 'zx': 'dd'}
{'wwf': None, 'zx': 'sd'}
{'wwf': None, 'zx': None}
{'wwf': None, 'zx': 'dd'}
{'wwf': 5, 'zx': 'sd'}
{'wwf': 5, 'zx': None}
{'wwf': 5, 'zx': 'dd'}
"""
def __convertMapList(list:[], originParams:{}, param:{},keyList:[],index):
    size = len(keyList)
    if index >= size:
        list.append(param.copy())
        return
    key = keyList[index]
    values = originParams[key]
    for value in values:
        param[key] = value
        __convertMapList(list,originParams,param,keyList,index+1)

paramList = []
__convertMapList(paramList,params,{},list(params.keys()),0)
for p in paramList:
    print(f"{p}")

print(f"\n\n\n\n")


