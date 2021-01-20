from datetime import datetime

import requests
import numpy as np
import re

from earnmi.model.bar import LatestBar


class SinaUtil:

    @staticmethod
    def toSinCode(code: str):
        if code.startswith("sh") or code.startswith("sz"):
            return code
        offset = code.find(".")
        if offset > 0:
            code = code[:offset]
        assert code.isdigit()
        if code.startswith("6"):
            return f"sh{code}"
        else:
            return f"sz{code}"

    @staticmethod
    def fetch_latest_bar(codeList):
        batch_size = 100
        size = len(codeList)
        bar_list = []
        for i in range(0,size,batch_size):
            sub_code_list = codeList[i:i+batch_size]
            sub_bar_list = SinaUtil._fetchLatestBarFromSinaByBatch(sub_code_list)
            bar_list.extend(sub_bar_list)
        return bar_list


    @staticmethod
    def _fetchLatestBarFromSinaByBatch(codeList):
        codeSize = len(codeList)
        assert codeSize <=100
        sinaCodeList = []
        for i in range(0,codeSize):
            sinaCodeList.append(SinaUtil.toSinCode(codeList[i]))
            #sinaCodeList[i] = SinaUtil.toSinCode(codeList[i])

        urlParams = ','.join(sinaCodeList)
        url = f"http://hq.sinajs.cn/list={urlParams}"
        res = requests.get(url=url)
        text = res.text
        matchObj = re.findall('var hq_str_.*?="([\s\S]+?)";', text, re.M | re.I)

        latestBarList = []
        if matchObj:
            for index, item in enumerate(matchObj):
                tokens = item.split(",")
                if len(tokens) < 32:
                    continue
                dt = datetime.strptime(f"{tokens[30]} {tokens[31]}", "%Y-%m-%d %H:%M:%S")
                bar = LatestBar(
                    code=codeList[index],
                    datetime=dt
                )
                bar.name = tokens[0]
                bar.open_price = float(tokens[1])
                bar.close_price = float(tokens[3])
                bar.high_price = float(tokens[4])
                bar.low_price = float(tokens[5])
                bar.volume = float(tokens[8])
                latestBarList.append(bar)
        return latestBarList