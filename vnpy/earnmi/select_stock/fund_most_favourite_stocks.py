#%%

# 基金重仓库，条件：
# 基金持仓数排名前：n个，过滤条件：上市超过两年，并且市值在一定范围内 W；
# http://fund.jrj.com.cn/action/fhs/list.jspa?thisReportDate=20191231&tdName=fundNum&sc=desc
#
import  urllib.request

import re as regex
import numpy as np
from datetime import datetime, timedelta
from earnmi.uitl.jqSdk import jqSdk

"""
  查询基金每个季度最喜欢的（重仓）的股票
"""
def _queryFunStock(n:int,season:str,minMarketCap:float, maxMarketCap:float)-> list:
    """
    查询基金前n个基金重仓股，基金占比流通股市值百分比要超过：1%
    season 季度值，比如：20191231，20190930,20190630,20190331
    minMarketCap 最小流通市值（单位万元）
    maxMarketCap 最大流通市值（单位万元）
    """

    url = url = r'http://fund.jrj.com.cn/action/fhs/list.jspa?thisReportDate=%s&tdName=fundNum&sc=desc' % (season)
    res = urllib.request.urlopen(url)
    html = res.read().decode('gbk')

    matchObj = regex.findall(r'JSON_DATA.push\(\["\d+","(\d+)",.*?,.*?,.*?,.*?,.*?,"([\d\.]+?)","([\d\.]+?)".*?\]\);',
                             html, regex.M | regex.I)

    result_list = []
    seasonDate = datetime.strptime(season, "%Y%m%d")

    if (matchObj is not None):
        for index, item in enumerate(matchObj):
            fundMarketcap = float(item[1])  # 基金占用流通市值
            fundMarketRate = float(item[2])  # 基金占用流通市值的比例%
            if (fundMarketcap > 1000 and fundMarketRate > 1):
                marketCap = fundMarketcap / float(item[2]) * 100
                if (minMarketCap <= marketCap and marketCap <= maxMarketCap):
                    code = item[0]
                    onMarketDate = jqSdk.getOnMarketDate(code) #获取上市日期
                    dayBela = seasonDate.date() - onMarketDate
                    if(dayBela.days > 365*2): #上市超过两年
                        result_list.append(item[0])
                if (len(result_list) >= n):
                    break
    #codeList = np.array(result_list)
    return result_list

def _getSeasonDatetime(date:datetime,offset:int)->datetime:
    """
    返回date 返回对应日期的季度日期。即每年的：12月31日，09月30日,06月30日,03月31日
    offset 为0时，返回当前的季度日期
           为<0时，返回上一个季度日期，
           为>0时，返回下一个季度日期，
    """
    if(abs(offset) <= 1):
        currentSeason = datetime(date.year, date.month, 15)
        if(offset < 0):
            currentSeason = currentSeason - timedelta(days=88)
        elif(offset>0):
            currentSeason = currentSeason + timedelta(days=88)
        if(currentSeason.month<=3):
            currentSeason = datetime(currentSeason.year, 3, 31)
        elif (currentSeason.month<=6):
            currentSeason = datetime(currentSeason.year, 6, 30)
        elif (currentSeason.month<=9):
            currentSeason = datetime(currentSeason.year, 9, 30)
        else:
            currentSeason = datetime(currentSeason.year, 12, 31)
        return currentSeason
    elif(offset > 0):
        date = _getSeasonDatetime(date,1)
        return _getSeasonDatetime(date,offset -1)
    else:
        date = _getSeasonDatetime(date, -1)
        return _getSeasonDatetime(date,offset + 1)

def queyFundateFavourite(start_date:datetime,end_date:datetime) ->dict:
    """"
    查询每个季度基金最喜欢（重仓）的股票
    """
    minMarketCap = float(500000)
    maxMarketCap = float(20000000)

    season_end_date = _getSeasonDatetime(end_date,0)
    dataSet = {}
    while (start_date <= season_end_date):
        season_date = _getSeasonDatetime(start_date,0)
        season_str = season_date.strftime("%Y%m%d")
        code_list = _queryFunStock(50,season_str,minMarketCap,maxMarketCap)
        dataSet[season_str] = code_list
        start_date = _getSeasonDatetime(start_date,1)
    return dataSet


"""
  查询基金每个季度最喜欢的（重仓）的股票
"""
start_day = datetime.strptime("2015-11-29","%Y-%m-%d")
end_day = datetime.strptime("2019-11-29","%Y-%m-%d")

data = queyFundateFavourite(start_day,end_day)

print(data)
# minMarketCap = float(500000)
# maxMarketCap = float(20000000)
# codeList = _queryFunStock(50,'20190331',minMarketCap,maxMarketCap)
# print(codeList)

