from dataclasses import dataclass
from typing import Tuple, Sequence

import pandas as pd
from datetime import datetime
from earnmi.uitl.jqSdk import jqSdk
import jqdatasdk as jq
from datetime import datetime, timedelta

def encodeMarketValue(value:float)->int:
    __encode_list = [0,10,25,78,117,175,262,393,590,885,1327,1990,2985,4448,6672,10008]
    size = len(__encode_list)
    for i in range(1,size):
        if value <__encode_list[i]:
            return i - 1
    return size - 1;

sample_pd = pd.read_csv('tran_data.csv',dtype=str,header = None)

from decimal import Decimal

for index,row in sample_pd.iterrows():
    row[1] = encodeMarketValue(float(row[1]))
    row[2] = round(Decimal(row[2])*100,1)
    row[3] = round(Decimal(row[3])*100,1)
    row[4] = round(Decimal(row[4])*100,1)
    row[5] = round(Decimal(row[5]),1)
    row[6] = round(Decimal(row[6]),1)
    row[7] = round(Decimal(row[7]),1)
    row[8] = round(Decimal(row[8])*100,0)

print(sample_pd.head(5))

sample_pd.to_csv('sample_data.csv',encoding='utf-8',header=False,index=False)








