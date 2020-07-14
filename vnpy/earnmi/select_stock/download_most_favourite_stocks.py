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
import pandas as pd

def downloadAsDataFrame(season:str)-> pd.DataFrame:
    str = season  # 季度
    pagees = [1,2] # 页面,从1开始
    dataset = []
    for page in pagees:
        url = f"http://data.eastmoney.com/zlsj/zlsj_list.aspx?type=ajax&st=2&sr=-1&p={page}&ps=50&jsObj=qKcUkkCd&stat=1&cmd=1&date={str}&rt=53156716"
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


session_str = "2019-12-31"

sessions = ["2019-12-31","2020-03-31"]

writer=pd.ExcelWriter('4444.xlsx')
for session_str in sessions:
    dataFrame = downloadAsDataFrame(session_str)
    dataFrame.to_excel(writer,sheet_name=session_str)
writer.save()