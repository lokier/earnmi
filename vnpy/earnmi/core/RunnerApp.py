from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from earnmi.core.CallableEngine import CallableEngine
from earnmi.core.Runner import Runner, RunnerContext, RunnerInitor

__all__ = [
    # Super-special typing primitives.
    'RunnerApp',
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


@dataclass
class Run_Daily_Job:
    hour_minute_second:str
    function:Callable
    args:{}
    run_if_miss_time:bool

    def secheduleToayJob(self,engine:CallableEngine):
        """
        hour_minute_second:
        """
        hour,minute,second = parse_hour_minute_second(self.hour_minute_second)
        now = engine.now()
        job_time = datetime(year=now.year, month=now.month, day=now.day, hour=hour, minute=minute, second=second)
        delay_second = int((job_time.timestamp() - now.timestamp() + 0.45))
        if delay_second > 0:
            engine.postDelay(delay_second,self.function,self.args)
        elif not self.run_if_miss_time and delay_second < 0:
            ##错过今天的运行时间
            return
        else:
            engine.post(self.function,self.args)


class _RunnerWrapper(RunnerContext,RunnerInitor):

    def __init__(self,runner:Runner,engine:CallableEngine):
        super().__init__()
        assert runner.context is None
        self.engine = engine
        self.runner:Runner = runner
        self.runner.context = self
        self.run_daily_job_list:['Run_Daily_Job'] = []

    def now(self)->datetime:
        return self.engine.now()

    def is_backtest(self)->bool:
        return self.engine.is_backtest

    def run_delay(self,second:int, function:Callable,args = {}):
        self.engine.postDelay(second,function,args)

    def run_daily(self,hour_minute_seconde:str,function:Callable, args = {}, run_if_miss_time = True):
        job = Run_Daily_Job(hour_minute_second=hour_minute_seconde,function=function,args=args,run_if_miss_time=run_if_miss_time)
        self.run_daily_job_list.append(job)

    def secheduleToayJob(self,engine:CallableEngine):
        [ job.secheduleToayJob(engine) for job in self.run_daily_job_list]

class RunnerApp:

    def __init__(self):
        self.engine:CallableEngine = CallableEngine()
        self.engine.addDayChangedListener(self._onDayChanged)
        self.runner_list:['_RunnerWrapper'] = []
        self.running = False

    def onInerceptCallable(self,callbale:Callable,args:{}):
        #TODO 分配到线程池里开多线程执行。
        callbale(**args)

    def _onDayChanged(self,theEngine:CallableEngine):
        """
        天数变化：新的一天开始安排工作。
        """
        self._secheduleToayJob()


    def _onStartup(self):
        """
        启动,开始安排工作
        """
        [ runner_wrapper.runner.onStartup(runner_wrapper) for runner_wrapper in self.runner_list ]
        ##拦截引擎的callable方法调用
        self.engine.intercept_callbale_handler = self.onInerceptCallable

        self._secheduleToayJob()

    def _secheduleToayJob(self):
        """
         分配今天的任务
        """
        [ runner_wrapper.secheduleToayJob(self.engine) for runner_wrapper in self.runner_list ]


    def add(self,runner:Runner):
        if self.running:
            raise RuntimeError("can't add while is runing!")
        for runner_wrapper in self.runner_list:
            if runner_wrapper.runner.getName() == runner.getName():
                raise RuntimeError(f"runner.name [{runner.getName()}] 已经存在！")
        self.runner_list.append(_RunnerWrapper(runner,self.engine))

    def run(self):
        assert not self.running
        self.running = True
        self.engine.run()
        self.engine.post(self._onStartup)

    def run_backtest(self,start:datetime):
        assert not self.running
        self.running = True
        self.engine.run_backtest(start)
        self.engine.post(self._onStartup)



if __name__ == "__main__":

    hour,minute,second = parse_hour_minute_second("15:23:34")
    print(f"{hour}:{minute}:{second}")

    class MyRunner(Runner):

        def getName(self):
            return "MyRunner"

        def onStartup(self, initor: RunnerInitor):
            print(f"[{self.context.now()}-{self.getName()}]:onStartUp")

            initor.run_daily("15:23:34",self.onRunAt_15_23_34,args={},run_if_miss_time=False)

        def onRunAt_15_23_34(self):
            now = self.context.now();
            print(f"[{now}-{self.getName()}]:onRunAt_15_23_34")

    app = RunnerApp()
    app.add(MyRunner())

    start = datetime(year=2019, month=7, day=2, hour=14)
    app.run_backtest(start)

    app.engine.go(3600*24*10)
