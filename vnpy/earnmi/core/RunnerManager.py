from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from earnmi.core.MainEventEngine import MainEventEngine
from earnmi.core.Context import Context, ContextWrapper
from earnmi.core.Runner import Runner, RunnerContext, RunnerScheduler

__all__ = [
    # Super-special typing primitives.
    'RunnerManager',
]


def parse_hour_minute_second(text:str):
    digit_list = text.split(":")
    assert len(digit_list) == 3
    hour = int(digit_list[0])
    minute = int(digit_list[1])
    sencond = int(digit_list[2])
    assert  0<= hour and hour < 24
    assert  0<= minute and minute < 60
    assert  0<= sencond and sencond < 60
    return hour,minute,sencond


def parse_week_desc(text:str):
    ##格式支持三种： "1", "2-5", "1,3,6"
    digit_list = text.split("-")
    if len(digit_list) == 2:
        #格式: "2-5"
        begin = int(digit_list[0])
        end = int (digit_list[1])
        assert  begin>=1
        assert  end <=7
        return list(range(begin,end + 1))
    digit_list = text.split(",")

    number_list = []
    for digit_text in digit_list:
        try:
            num = int(digit_text)
            assert 1<=num and num <= 7
            number_list.append(num)
        except Exception:
            pass
    if len(number_list) < 1:
        raise RuntimeError(f"parse_week_desc error: {text}")

    return number_list

def parse_day_desc(text:str):
    ##格式支持三种： "1", "2-5", "1,3,6"
    digit_list = text.split("-")
    if len(digit_list) == 2:
        #格式: "2-5"
        begin = int(digit_list[0])
        end = int (digit_list[1])
        assert  begin>=1
        assert  end <=31
        return list(range(begin,end + 1))
    digit_list = text.split(",")

    number_list = []
    for digit_text in digit_list:
        try:
            num = int(digit_text)
            assert 1<=num and num <= 31
            number_list.append(num)
        except Exception:
            pass
    if len(number_list) < 1:
        raise RuntimeError(f"parse_day_desc error: {text}")

    return number_list

def __secheduleToayJob__(engine:MainEventEngine, hour_minute_second:str, now:datetime, function:Callable, args:{}, run_if_miss_time:bool):
    hour, minute, second = parse_hour_minute_second(hour_minute_second)
    job_time = datetime(year=now.year, month=now.month, day=now.day, hour=hour, minute=minute, second=second)
    delay_second = int((job_time.timestamp() - now.timestamp() + 0.45))

    ##错过今天的运行时间
    if delay_second < 0 and not run_if_miss_time :
        return
    engine.postDelay(delay_second, function, args)


@dataclass
class Run_Monthly_Job:
    day_desc:str
    hour_minute_second:str
    function:Callable
    args:{}
    run_if_miss_time:bool

    def secheduleToayJob(self, engine:MainEventEngine):
        day_list = parse_day_desc(self.day_desc)
        now = engine.now()
        the_day = now.day
        is_match = day_list.__contains__(the_day)
        if is_match:
            __secheduleToayJob__(engine, self.hour_minute_second, now, self.function, self.args, self.run_if_miss_time)

@dataclass
class Run_Weekly_Job:
    week_desc:str
    hour_minute_second:str
    function:Callable
    args:{}
    run_if_miss_time:bool

    def secheduleToayJob(self, engine:MainEventEngine):
        week_list = parse_week_desc(self.week_desc)
        now = engine.now()
        the_week = now.weekday()  ##  0-6
        the_week+=1
        is_match = week_list.__contains__(the_week)
        if is_match:
            __secheduleToayJob__(engine, self.hour_minute_second, now, self.function, self.args, self.run_if_miss_time)


@dataclass
class Run_Daily_Job:
    hour_minute_second:str
    function:Callable
    args:{}
    run_if_miss_time:bool

    def secheduleToayJob(self, engine:MainEventEngine):
        """
        hour_minute_second:
        """
        now = engine.now()
        __secheduleToayJob__(engine,self.hour_minute_second,now,self.function,self.args,self.run_if_miss_time)


class _RunnerSession(RunnerContext, RunnerScheduler):

    def __init__(self, runner:Runner, ower_context:Context):
        ContextWrapper.__init__(self,ower_context)
        assert runner.context is None
        self.engine = ower_context.engine
        self.runner:Runner = runner
        self.runner.context = self
        self.reset()

    def reset(self):
        self.run_daily_job_list: ['Run_Daily_Job'] = []
        self.run_weekly_job_list: ['Run_Weekly_Job'] = []
        self.run_montly_job_list: ['Run_Monthly_Job'] = []

    def now(self)->datetime:
        return self.engine.now()

    def is_backtest(self)->bool:
        return self.engine.is_backtest


    def log_i(self, msg: str):
        self._context._logger.info(f"[{self.engine.now()}|{self.is_mainThread()}|{self.runner.getName()}]: {msg}")

    def log_d(self, msg: str):
        self._context._logger.debug(f"[{self.engine.now()}|{self.is_mainThread()}|{self.runner.getName()}]: {msg}")

    def log_w(self, msg: str):
        self._context._logger.warn(f"[{self.engine.now()}|{self.is_mainThread()}|{self.runner.getName()}]: {msg}")

    def log_e(self, msg: str):
        self._context._logger.error(f"[{self.engine.now()}|{self.is_mainThread()}|{self.runner.getName()}]: {msg}")

    def run_delay(self,second:int, function:Callable,args = {}):
        self.engine.postDelay(second,function,args)

    def run_daily(self,hour_minute_seconde:str,function:Callable, args = {}, run_if_miss_time = False):
        job = Run_Daily_Job(hour_minute_second=hour_minute_seconde,
                            function=function,args=args,run_if_miss_time=run_if_miss_time)
        self.run_daily_job_list.append(job)

    def run_weekly(self,week_desc:str,hour_minute_second:str,function:Callable, args = {}, run_if_miss_time = False):

        job = Run_Weekly_Job(week_desc=week_desc,hour_minute_second=hour_minute_second,
                             function=function,args=args,run_if_miss_time=run_if_miss_time)
        self.run_weekly_job_list.append(job)

    def run_monthly(self,day_desc:str,hour_minute_second:str,function:Callable, args = {}, run_if_miss_time = False):
        job = Run_Monthly_Job(day_desc=day_desc, hour_minute_second=hour_minute_second,
                             function=function, args=args, run_if_miss_time=run_if_miss_time)
        self.run_montly_job_list.append(job)

    def secheduleToayJob(self, engine:MainEventEngine):
        [ job.secheduleToayJob(engine) for job in self.run_daily_job_list]  ##规划daily任务
        [ job.secheduleToayJob(engine) for job in self.run_weekly_job_list] ##规划weekly任务
        [ job.secheduleToayJob(engine) for job in self.run_montly_job_list] ##规划Monthly任务

class RunnerManager:

    def __init__(self,context:Context):
        self.context = context
        self.engine:MainEventEngine = context.engine
        self.runner_list:['_RunnerSession'] = []
        self.engine.register(MainEventEngine.EVNET_START,self._onStart)
        self.engine.register(MainEventEngine.EVNET_END,self._onStop)


    def onInerceptCallable(self,callbale:Callable,args:{}):
        #TODO 分配到线程池里开多线程执行。
        return callbale(**args)


    def _onStart(self,event:str,engine:MainEventEngine):
        """
        启动,开始安排工作
        """
        self.engine.register(MainEventEngine.EVNET_DAY_CHANED,self._onDayChanged)
        for runner_session in self.runner_list:
            runner_session.reset()
            runner_session.runner.onStart(runner_session)
        ##拦截引擎的callable方法调用
        self.engine.intercept_callbale_handler = self.onInerceptCallable
        self._secheduleToayJob()

    def _onStop(self,event:str,engine:MainEventEngine):
        self.engine.unregister(MainEventEngine.EVNET_DAY_CHANED,self._onDayChanged)
        for runner_session in self.runner_list:
            runner_session.runner.onStop()
            runner_session.reset()
        self.engine.intercept_callbale_handler = None

    def _onDayChanged(self, event: str, theEngine: MainEventEngine):
        """
        天数变化：新的一天开始安排工作。
        """
        self._secheduleToayJob()

    def _secheduleToayJob(self):
        """
         分配今天的任务
        """
        [ runner_wrapper.secheduleToayJob(self.engine) for runner_wrapper in self.runner_list ]


    def add(self,runner:Runner):
        if self.engine.is_running():
            raise RuntimeError("can't add while is main engine runing!")
        for runner_wrapper in self.runner_list:
            if runner_wrapper.runner.getName() == runner.getName():
                raise RuntimeError(f"runner.name [{runner.getName()}] 已经存在！")
        self.runner_list.append(_RunnerSession(runner, self.context))





if __name__ == "__main__":

    hour,minute,second = parse_hour_minute_second("15:23:34")
    print(f" parse_week_desc(2-2）：  {parse_week_desc('2-2')}")
    print(f" parse_week_desc(3-6）：  {parse_week_desc('3-6')}")
    print(f" parse_week_desc(2）：  {parse_week_desc('2')}")
    print(f" parse_week_desc(4,3,5,2）：  {parse_week_desc('4,3,5,2')}")
    print(f" parse_week_desc(4,）：  {parse_week_desc('4,')}")

    ##格式支持三种： "1", "2-5", "1,3,6"

    class MyRunner(Runner):

        def getName(self):
            return "MyRunner"

        def onStart(self, scheduler: RunnerScheduler):
            self.log("onStartUp")

            scheduler.run_weekly("3,4,6","5:4:6",self.on_RunAt_Weekly_5_4_6,args={},run_if_miss_time=True)
            scheduler.run_daily("15:23:34",self.onRunAt_15_23_34,args={},run_if_miss_time=False)
            scheduler.run_monthly("7,4,10,9,14","1:11:11",self.on_RunAt_Monthly_1_11_11,args={},run_if_miss_time=False)

        def onRunAt_15_23_34(self):
            self.log("onRunAt_15_23_34")

        def on_RunAt_Weekly_5_4_6(self):
            now = self.context.now();
            self.log(f"on_RunAt_Weekly_5_4_6, 星期{now.weekday()+1}")
            self.context.post_delay(40,self.on_RunAt_Weekly_5_4_6_delay_at_40s)

        def on_RunAt_Weekly_5_4_6_delay_at_40s(self):
            self.log("on_RunAt_Weekly_5_4_6_delay_at_40s")

        def on_RunAt_Monthly_1_11_11(self):
            self.log("on_RunAt_Monthly_1_11_11")


    from earnmi.core.App import App
    app = App()
    runnerManager = RunnerManager(app)
    runnerManager.add(MyRunner())

    start = datetime(year=2021, month=1, day=2, hour=14)
    app.run_backtest(start)
    app.engine.go(3600*24*10)
