from dataclasses import dataclass
from typing import Tuple

import pandas as pd
from datetime import datetime
from earnmi.uitl.jqSdk import jqSdk
import jqdatasdk as jq

@dataclass
class TrainItem:
    code:str = None  #代码
    market_value:float = 0 #市值
    range1:float =0  #前3个月的涨幅
    range2:float =0  #前3个月的涨幅
    range3:float =0  #前3个月的涨幅

    #range_max:float = 0.0 #此季度最大涨幅
    #range_min:float = 0.0#此季度最大跌幅
    account_rates = [] # 前三季度持仓占比


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

train_dataList = []

for sheet_name in sheet_names:
    print(f"read sheet: {sheet_name}")
    df_data =  excel_reader.parse(sheet_name)
    item_dict = {}
    end_date = datetime.strptime(sheet_name, '%Y-%m-%d')
    end_date = datetime(year=end_date.year,month=end_date.month,day=end_date.day,hour=end_date.hour)
    for index, row in df_data.iterrows():
        code = row['SCode']
        account_rate = row['TabRate'] ##获取当前季度的占比
        market_acccount = row['VPosition']
        market_value = market_acccount * 100 / account_rate  # 市值

        old_item = history_item_dict.get(code)
        item = TrainItem()

        if not old_item is None:
            item.account_rates = old_item.account_rates
        item.code = code
        item.market_value = market_value
        item.account_rates.append(account_rate)

        account_rate_size = len(item.account_rates)
        if account_rate_size > 3:
            del item.account_rates[0]
        if account_rate_size == 3:
            ##获取当前3个月的涨幅
            ranges = _get_bar_range(jq, code, end_date)
            if not ranges is None:
                item.range1 = ranges[0]
                item.range2 = ranges[1]
                item.range3 = ranges[2]
                train_dataList.append(item)
                print(f"find:{item}")

        item_dict[code] =item

    print(f"end sheet: size = {len(item_dict)}")
    history_item_dict = item_dict


