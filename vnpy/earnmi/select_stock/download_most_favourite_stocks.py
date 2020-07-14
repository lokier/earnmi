##东方财富 重仓基金
## http://data.eastmoney.com/zlsj/
##http://data.eastmoney.com/zlsj/zlsj_list.aspx?type=ajax&st=2&sr=-1&p=3&ps=50&jsObj=fgOoOhby&stat=1&cmd=1&date=2020-03-31&rt=53156712
##http://data.eastmoney.com/zlsj/zlsj_list.aspx?type=ajax&st=2&sr=-1&p=41&ps=50&jsObj=qKcUkkCd&stat=1&cmd=1&date=2020-03-31&rt=53156716
##Request URL: http://data.eastmoney.com/zlsj/zlsj_list.aspx?type=ajax&st=2&sr=-1&p=2&ps=50&jsObj=cbMMVSlL&stat=1&cmd=1&date=2019-12-31&rt=53156983
##Request Method: GET
# data:[
# {SCode: "603256", SName: "宏和科技", RDate: "/Date(1585584000000)/", LXDM: "基金", LX: "1", Count: 1,…}
# CGChange: "减持"
# Count: 1
# LTZB: 0.98633257
# LX: "1"
# LXDM: "基金"
# RDate: "/Date(1585584000000)/"
# RateChange: -51.5589786216236
# SCode: "603256"
# SName: "宏和科技"
# ShareHDNum: 866000
# ShareHDNumChange: -921741
# TabRate: 0.09865573  持仓比例
# VPosition: 10097560
# }
# ]
import urllib.request
import json
import re as regex
from datetime import datetime, timedelta

import pandas as pd

def downloadAsDataFrame(season:str)-> pd.DataFrame:
    pagees = [1,2] # 页面,从1开始
    dataset = []
    for page in pagees:
        url = f"http://data.eastmoney.com/zlsj/zlsj_list.aspx?type=ajax&st=2&sr=-1&p={page}&ps=50&jsObj=qKcUkkCd&stat=1&cmd=1&date={season}&rt=53156716"
        print(f"request url:{url}")
        res = urllib.request.urlopen(url)
        jsonText = res.read().decode('gbk')
        print(f"Get url:{url}")
        matchObj = regex.search( "\\[.*\\]", jsonText, regex.M|regex.I)


        if matchObj:
            jsonData = json.loads(matchObj.group())

            for item in jsonData:
                list = [
                    item['SName'],
                    item['SCode'],
                    item['Count'],
                    item['CGChange'],
                    item['RateChange'],
                    item['ShareHDNum'],
                    item['ShareHDNumChange'],
                    item['TabRate'],
                    item['VPosition']
                ]
                dataset.append(list)


    cloumns = ["SName", "SCode", "Count", "CGChange", "RateChange", "ShareHDNum", "ShareHDNumChange", "TabRate", "VPosition"]
    wxl = pd.DataFrame(dataset, columns=cloumns)
    return wxl


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

## 开始时间2014-6-30

sessions = ["2019-12-31","2020-03-31"]


writer=pd.ExcelWriter('collect3.xlsx')

sessionTime = datetime(year=2014,month=6,day=30)
offset = 0
endTime = datetime.now()
while sessionTime <= endTime:
    season_str = sessionTime.strftime("%Y-%m-%d")
    downloadData = downloadAsDataFrame(season_str)
    print(f"download : {season_str},shape = {downloadData.shape}")
    print(f"data: {downloadData.head(1)}")

    downloadData.to_excel(writer,sheet_name=season_str)
    sessionTime = _getSeasonDatetime(sessionTime,1)

writer.save()
writer.close()