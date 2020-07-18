from dataclasses import dataclass
from typing import Tuple, Sequence

import pandas as pd
from datetime import datetime
from earnmi.uitl.jqSdk import jqSdk
import jqdatasdk as jq

@dataclass
class TrainItem:
    code:str  #代码
    market_value:float = 0 #市值
    range1:float =0  #前3个月的涨幅
    range2:float =0  #前3个月的涨幅
    range3:float =0  #前3个月的涨幅
    account_rates:Sequence[float] = None # 前三季度持仓占比
    #range_max:float = 0.0 #此季度最大涨幅
    #range_min:float = 0.0#此季度最大跌幅
    def __post_init__(self):
        """"""
        self.account_rates = []

def _get_bar_range(jq:jq,code:str,season_date:datetime):
    df = jq.get_bars(jq.normalize_code(code), 4, unit='1M', fields=['date', 'open', 'high', 'low', 'close', 'volume'],
                     include_now=True, end_dt=season_date)
    if df is None:
        return None
    size = df.shape[0]
    if size != 4:
        return None
    ranges = []
    for i in range(1,4):
        v = (df.at[i,'close'] - df.at[i-1,'close']) / df.at[i-1,'close']
        ranges.append(v)
    return ranges[0],ranges[1],ranges[2]


excel_reader=pd.ExcelFile('collect3.xlsx')  # 指定文件

sheet_names = excel_reader.sheet_names  # 读取文件的所有表单名，得到列表

history_item_dict = {}
jq = jqSdk.get()

#types = [str,  str,  int, float,  float, float,float, float, int]
# types = {'SCode': str, "SName": str, "Count": int, 'CGChange': float, 'RateChange': float, 'ShareHDNum': float,
#          'ShareHDNumChange': float, 'TabRate': float, 'VPosition': int}

for sheet_name in sheet_names:
    print(f"read sheet: {sheet_name}")
    df_data = excel_reader.parse(sheet_name, dtype=str)
    item_dict = {}
    end_date = datetime.strptime(sheet_name, '%Y-%m-%d')
    end_date = datetime(year=end_date.year,month=end_date.month,day=end_date.day,hour=end_date.hour)

    train_dataList = []
    for index, row in df_data.iterrows():
        code = row['SCode']
        account_rate = float(row['TabRate']) ##获取当前季度的占比
        market_acccount = float(row['VPosition'])
        market_value = market_acccount * 100 / account_rate  # 市值

        old_item = history_item_dict.get(code)
        item = TrainItem(code=code)

        if not old_item is None:
            item.account_rates = old_item.account_rates
        item.code = code
        item.market_value = market_value
        item.account_rates.append(account_rate)

        account_rate_size = len(item.account_rates)
        if account_rate_size > 3:
            assert account_rate_size == 4
            del item.account_rates[0]
            account_rate_size = 3
        if account_rate_size == 3:
            ##获取当前3个月的涨幅
            ranges = _get_bar_range(jq, code, end_date)
            if not ranges is None:
                item.range1 = ranges[0]
                item.range2 = ranges[1]
                item.range3 = ranges[2]

                ##可以作为一个样本数据。
                cell_data = []
                cell_data.append(item.code)
                cell_data.append(item.market_value)
                cell_data.append(item.range1)
                cell_data.append(item.range2)
                cell_data.append(item.range3)
                cell_data.append(item.account_rates[0])
                cell_data.append(item.account_rates[1])
                cell_data.append(item.account_rates[2])
                train_dataList.append(cell_data)

                #print(f"find:{item}")


        item_dict[code] =item
    print(f"end sheet: size = {len(item_dict)}")
    history_item_dict = item_dict
    cloumns = ["cde", "mv", "r1", "r2", "r3", "ar1", "ar2", "ar3"]
    out_batch_data = pd.DataFrame(train_dataList, columns=cloumns)
    out_batch_data.to_csv('tran_data.csv',mode='a',encoding='utf-8',header=False,index=False)



