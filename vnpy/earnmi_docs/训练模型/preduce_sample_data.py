from dataclasses import dataclass
from typing import Tuple, Sequence

import pandas as pd
from datetime import datetime
from earnmi.uitl.jqSdk import jqSdk
import jqdatasdk as jq
from datetime import datetime, timedelta

def encodeMarketValue(value:float)->int:
    value = value / 100000000
    __encode_list = [0,10,25,78,117,175,262,393,590,885,1327,1990,2985,4448,6672,10008]
    size = len(__encode_list)
    for i in range(1,size):
        if value <__encode_list[i]:
            return i - 1
    return size - 1

def encodeLabel(value:float)->int:
    value = value * 100
    is_mius = value < 0
    value = int(round(value / 5,0))
    if is_mius:
        return  - 1
    return 1






sample_pd = pd.read_csv('tran_data.csv',dtype=str,header = None)

from decimal import Decimal
resunlt_pd = pd.DataFrame(index=sample_pd.head(0))

for index,row in sample_pd.iterrows():
    mk = float(row[1])
    _mk = mk / 100000000
    if _mk < 100 or _mk > 5000:
        continue
    row[1] = encodeMarketValue(mk)
    row[2] = round(Decimal(row[2])*100,1)
    row[3] = round(Decimal(row[3])*100,1)
    row[4] = round(Decimal(row[4])*100,1)
    row[5] = round(Decimal(row[5]),1)
    row[6] = round(Decimal(row[6]),1)
    row[7] = round(Decimal(row[7]),1)
    row[8] = encodeLabel(float(row[8]))
    resunlt_pd =  resunlt_pd.append(row, ignore_index=True)

print(resunlt_pd.head(5))
print(resunlt_pd.shape)

resunlt_pd.to_csv('sample_data3.csv',encoding='utf-8',header=False,index=False)








