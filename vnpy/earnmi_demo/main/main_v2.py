from datetime import datetime

from earnmi.core.App import App
from earnmi.core.Runner import Runner
from earnmi.model.BarDataSource import ZZ500DataSource
from earnmi.model.CoreEngine import CoreEngine
from earnmi.model.CoreEngineRunner import CoreEngineRunner
from earnmi.model.DataSource import DatabaseSource
from earnmi.model.Dimension import Dimension
from earnmi.model.ZZ500_ProjectRunner import ZZ500_ProjectRunner
from earnmi.model.bar import LatestBarDB
from earnmi_demo.main.skdj_zz500_main import SKDJ_EngineModelV2

from earnmi.data.MarketImpl import Market2Impl
from earnmi.data.SWImpl import SWImpl

### 判断当前是什么时候，然后一直执行。
from earnmi.model.ProjectRunner import TradeRunner, OpStrategy, OpProject, ProjectRunner, OpDataBase
from earnmi.uitl.utils import utils
from vnpy.event import Event
from peewee import Database, SqliteDatabase
import time
import sched


def InitSKDJ_zz500_Project_TradRunner(dbSource:DatabaseSource,isBuild:bool)->Runner:
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
    return ZZ500_ProjectRunner(name="skdj_500",project = project,source=dbSource,strategy= MyStrategy(),engine=engine)


if __name__ == "__main__":

    class MyDatabaseSource(DatabaseSource):
        def createDatabase(self) -> Database:
            return SqliteDatabase("main_v2.db")
    db_source = MyDatabaseSource()
    app = App()
    app.getRunnerManager().add(InitSKDJ_zz500_Project_TradRunner(db_source,isBuild =False))
    app.run_backtest()






