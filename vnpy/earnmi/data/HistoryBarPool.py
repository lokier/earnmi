from collections import Sequence
from datetime import datetime, timedelta
from ibapi.common import BarData
from vnpy.trader.constant import Exchange, Interval
from earnmi.data.import_data_from_jqdata import save_bar_data_from_jqdata
from vnpy.trader.database import database_manager




"""
  历史数据池
"""
class HistoryBarPool:

    __code:str = None
    __keepN:int= None     #至少保持的个数
    __minPoolSize:int = None
    __poolBegin:datetime = None
    __poolEnd:datetime = None
    __today:datetime = None
    __current_pool_data:Sequence = None
    __current_pool_index = -1

    def __init__(self, code: str):
        self.__init__(code,100)


    def __init__(self,code:str, keepN):
        self.__code = code
        self.__keepN = keepN
        self.__minPoolSize = keepN

    def initPool(self,begin:datetime,end:datetime):
        database_manager.clean(self.__code)
        save_bar_data_from_jqdata(self.__code, Interval.DAILY, start_date=begin, end_date=end)
        self.__poolBegin = begin
        self.__poolEnd = end

    def setToday(self,today:datetime):
        if(self.__poolBegin == None):
            raise RuntimeError("must call initPoll() first!")
        if(today.__gt__(self.__poolEnd) or today.__lt__(self.__poolBegin)):
            raise RuntimeError("today must be in range poll size")

        chagned = self.__today == None or (not( self.__is_same_day(today,self.__today)))
        if chagned :
             self.__today = today
             self.__prepareDataSet()

    def getData(self)-> Sequence:
        if(self.__current_pool_index >=0):
            begin =  self.__current_pool_index
            end =  self.__current_pool_index + self.__keepN
            return self.__current_pool_data[begin:end]

        return None

    def __findTodayIndexInPool(self) ->int:
        index = -1
        for i, bar in enumerate(self.__current_pool_data):
            if (self.__is_same_day(self.__today, bar.datetime)):
                index = i
                break
        return index

    def __prepareDataSet(self):
        #判断数据池里面有没有今天的数据，是否充分；
        self.__current_pool_index = -1
        if( not (self.__current_pool_data == None)):
            index = self.__findTodayIndexInPool();
            if(index + 1 >= self.__keepN):
                #skip ,already is the poll data
                self.__current_pool_index = index - self.__keepN + 1
                return;
        beforeBars = []
        currentDate = self.__today
        while(beforeBars.__len__() < self.__keepN):
            bars = self.__loadBefore(currentDate)
            if(bars == None or bars.__len__() ==0):
                return
            beforeBars = bars + beforeBars
            currentDate = bars[0].datetime - timedelta(days=-1)

        if(beforeBars.__len__() >self.__keepN):
            beforeBars = beforeBars[ -1  - self.__keepN:-1]

        self.__current_pool_index = 0

        #parpare pool
        afterBars = []
        currentDate = self.__today
        while(afterBars.__len__()<self.__minPoolSize):
            oldSize = afterBars.__len__()
            currentDate = currentDate + timedelta(days=1)
            afterBars.extend(self.__loadAfter(currentDate))
            if(afterBars.__len__() == oldSize):
                break
            currentDate = afterBars[:-1]

        beforeBars.extend(afterBars)
        self.__current_pool_data = beforeBars



    def __loadBefore(self,end:datetime)-> Sequence:
        start = end - timedelta(days=200)
        exchange = Exchange.SZSE
        if self.__code.startswith("6"):
            exchange = Exchange.SSE
        return database_manager.load_bar_data(self.__code, exchange, Interval.DAILY, start, end)

    def __loadAfter(self,start:datetime) ->Sequence:
        end = start +  timedelta(days=150)
        exchange = Exchange.SZSE
        if self.__code.startswith("6"):
            exchange = Exchange.SSE
        return database_manager.load_bar_data(self.__code, exchange, Interval.DAILY, start, end)

    def __is_same_day(self,d1:datetime,d2:datetime)->bool:
        return d1.day == d2.day and d1.month == d2.month and d1.year == d2.year