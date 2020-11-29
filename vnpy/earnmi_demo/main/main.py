from datetime import datetime

from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineRunner import CoreEngineRunner
from earnmi.model.Dimension import Dimension
from earnmi.model.bar import LatestBarDB
from earnmi_demo.main.skdj_zz500_main import SKDJ_EngineModelV2

from earnmi.data.MarketImpl import MarketImpl
from earnmi.data.SWImpl import SWImpl

### 判断当前是什么时候，然后一直执行。
from earnmi.model.ProjectRunner import TradeRunner, OpStrategy, OpProject, ProjectRunner, OpDataBase
from earnmi.uitl.utils import utils
from vnpy.event import Event
from peewee import Database
import time
import sched

class _TradeRunnerThread:

    def __init__(self,name:str,runner:TradeRunner):
        self.schedule = sched.scheduler( time.time,time.sleep)
        self.runner = runner
        self.isOpen = False
        self.name = name

    def start(self,backgournd = False):
        import _thread
        thread = self
        def runner_inner():
            thread.schedule = sched.scheduler( time.time,time.sleep)
            thread.runner.onLoad()
            thread.now = datetime.now()
            thread.isOpen = thread.isOpenTime(thread.now)
            thread.schedule.enter(0, 0, thread.__run, ())
            thread.schedule.run()
        if backgournd:
            _thread.start_new_thread(runner_inner, ())
        else:
            runner_inner()

    def __run(self):
        oldTime = self.now
        self.now = datetime.now()
        isDayChanged  = not utils.is_same_day(oldTime,self.now)
        if isDayChanged:
            print(f"{[self.now]} {self.name} : dayChanged!!!!!!!!!")
            self.runner.onLoad()
            self.isOpen = self.isOpenTime(datetime.now())
            self.schedule.enter(1, 0, self.__run, ())
            return
        isOpenTime = self.isOpenTime(self.now)
        print(f"{self.now} {self.name} : isOpen={self.isOpen},isOpenTime={isOpenTime}")
        if(isOpenTime != self.isOpen):
            if isOpenTime:
                self.isOpen = True
                self.runner.onOpen()
            else:
                self.isOpen = False
                self.runner.onClose()
            self.schedule.enter(1, 0, self.__run, ())
            return
        if self.isOpen:
            ##正在开盘
            next_second = self.runner.onTrick()
            if(next_second is None):
                next_second = 60
            self.schedule.enter(next_second, 0, self.__run, ())
            return
        self.schedule.enter(15, 0, self.__run, ())

    def isOpenTime(self,time:datetime)->bool:
        if time.hour == 9:
            return time.hour >=29
        if time.hour== 10:
            return True
        if time.hour==11:
            return time.hour<=30
        return time.hour>=13 and time.hour<=15


class UpdateRealBarRunner(TradeRunner):

    def __init__(self,db:Database):
        self.db = LatestBarDB(db)

    def onLoad(self):
        print("UpdateRealBarRunner load!!!!!")
        pass

    """
    准备开盘。
    """
    def onOpen(self):
        print("更新数据:ZZ500DataSource实时数据")
        self.db.update(ZZ500DataSource.SZ500_JQ_CODE_LIST)

    def onTrick(self):
        print("更新数据:ZZ500DataSource实时数据")
        self.db.update(ZZ500DataSource.SZ500_JQ_CODE_LIST)
        return 55

    def onClose(self):
        print("更新数据:ZZ500DataSource实时数据")
        self.db.update(ZZ500DataSource.SZ500_JQ_CODE_LIST)


def InitSKDJ_zz500_Project_TradRunner(db:Database,isBuild:bool)->TradeRunner:
    _dirName = "models/runner_skdj_zz500"
    model = SKDJ_EngineModelV2()
    engine = None
    if isBuild:
        start = datetime(2015, 11, 1)
        end = datetime(2020, 10, 30)
        historySource = ZZ500DataSource(start, end)
        engine = CoreEngine.create(_dirName, model, historySource, min_size=200, useSVM=False)
    else:
        engine = CoreEngine.load(_dirName, model)

    print(f"模型加载完成！！！")

    class MyStrategy(OpStrategy):
        DIMEN = [107, 93, 92, 100, 64, 57, 99]
        def __init__(self):
            super().__init__()
            self.paramMap = {}
            self.paramMap[99] = {'buy_offset_pct': None, 'sell_offset_pct': None, 'sell_leve_pct_bottom': 2}
            self.paramMap[100] = {'buy_offset_pct': None, 'sell_offset_pct': 1, 'sell_leve_pct_bottom': 1}
            self.paramMap[94] = {'buy_offset_pct': None, 'sell_offset_pct': 1, 'sell_leve_pct_bottom': 1}
            self.paramMap[58] = {'buy_offset_pct': None, 'sell_offset_pct': None, 'sell_leve_pct_bottom': 1}

        def getParams(self, dimen_value: int):
            return self.paramMap.get(dimen_value)

        def isSupport(self, dimen: Dimension) -> bool:
            return not self.paramMap.get(dimen.value) is None

    project = OpProject(id=1, status="new", name="skdj_500", create_time=datetime(year=2020, month=11, day=26))
    opDB = OpDataBase(db)

    latestBarDB = LatestBarDB(db)

    if isBuild:
        opDB.clearAll()
    projectRunner =  ProjectRunner(project, opDB, engine)
    return projectRunner.loadZZ500NowRunner(latestBarDB,MyStrategy())



if __name__ == "__main__":
    from peewee import MySQLDatabase, Database, Database, Database

    # db = MySQLDatabase(**settings)
    dbSetting = {"database": "vnpy", "user": "root", "password": "123456", "host": "localhost", "port": 3306}
    # db = SqliteDatabase("opdata.db")
    db = MySQLDatabase(**dbSetting)



    real_bar_update_Thread = _TradeRunnerThread("实时bar更新器",UpdateRealBarRunner(db))
    sdkj_zz500_Thread = _TradeRunnerThread("skdj_ZZ500",InitSKDJ_zz500_Project_TradRunner(db,isBuild=False))

    real_bar_update_Thread.start(backgournd=True)
    sdkj_zz500_Thread.start()




