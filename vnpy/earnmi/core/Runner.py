
"""
运行程序。可以注册定时任务，时间触发器。
"""
from abc import abstractmethod
from datetime import datetime
from typing import Callable
__all__ = [
    # Super-special typing primitives.
    'RunnerScheduler',
    'RunnerContext',
    'Runner',

]

from earnmi.core.Context import Context, ContextWrapper


class RunnerScheduler:
    """
    计划任务
    """
    @abstractmethod
    def run_monthly(self,day_desc:str,hour_minute_second:str,function:Callable, args = {}, run_if_miss_time = False):
        """
        每月执行。
        day_desc:  范围1-31, 格式支持三种： "1", "2-5", "1,3,6"
        hour_minute_second : 格式： "10:15:23"
        run_if_miss_time 如果今天启动时，错过时间点时的处理方式。  为True时，表示依旧处理。 为False是，表示不处理。
        """
        pass

    @abstractmethod
    def run_weekly(self,week_desc:str,hour_minute_second:str,function:Callable, args = {}, run_if_miss_time = False):
        """
        每周执行。
        week_desc:  1-7表示：星期一到星期日, 格式支持三种： "1", "2-5", "1,3,6"
        hour_minute_second : 格式： "10:15:23"
        run_if_miss_time 如果今天启动时，错过时间点时的处理方式。  为True时，表示依旧处理。 为False是，表示不处理。
        """
        pass

    @abstractmethod
    def run_daily(self,hour_minute_second:str,function:Callable, args = {}, run_if_miss_time = False):
        """
        每天执行。
        hour_minute_second : 格式： "10:15:23"
        run_if_miss_time 如果今天启动时，错过时间点时的处理方式。  为True时，表示依旧处理。 为False是，表示不处理。
        """
        pass



class RunnerContext(ContextWrapper):

   pass


class Runner:

    def __init__(self):
        self.context:RunnerContext = None

    def now(self):
        self.context.now()

    def log(self,msg:str):
        self.context.log_i(msg)

    @abstractmethod
    def getName(self):
        """
          返回程序的名字。必须唯一。
        """
        pass

    @abstractmethod
    def onStart(self, scheduler:RunnerScheduler):
        """
        程序启动。 在单一线程里执行。
        启动后使用scheuler去规划后续的日常任务。
        """
        pass

    def onStop(self):
        """
        程序停车。 在单一线程里执行。
        启动后使用scheuler去规划后续的日常任务。
        """
        pass


class StockRunner(Runner):
    """
    股票运行程序。
    """
