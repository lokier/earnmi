
from datetime import datetime
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from earnmi.core.Runner import Runner


class run_monly:
    pass

class RunnerWrapper:

    def __init__(self):
        runner:Runner = None
        run_monly = [] ##每月执行
        run_weekly= [] ##每周执行
        run_dayly= [] ##每天执行


class RunnerApp:

    def add(self,runner:Runner):
        pass

    def run(self):
        """
        实盘运行。
        pip install apscheduler
        使用APScheduler实现定时任务
        单一调度线程，各个Runner都有各自的后台线程运行环境，并且同一个时间不会有相同Runner执行。
        """
        scheduler = BackgroundScheduler()

        scheduler.start()

        pass


    def run_backtest(self,start:datetime,end:datetime):
        """
          执行回撤。
        """
        pass