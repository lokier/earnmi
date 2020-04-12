import string
from datetime import datetime, timedelta

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

season = '20130530'
date = datetime.strptime(season,"%Y%m%d")
str = date.strftime("%Y%m%d")

print(str)


