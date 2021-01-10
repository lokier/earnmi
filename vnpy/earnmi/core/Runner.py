
"""
运行程序。可以注册定时任务，时间触发器。
"""
from abc import abstractmethod
from datetime import datetime

class RunnerInitor:
    """
    参考:https://www.joinquant.com/help/api/help#api:%E8%BF%90%E8%A1%8C%E6%97%B6%E9%97%B4
     # 定时运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
    # 开盘前运行，按月运行
    run_monthly(before_market_open, monthday = 1, time = 'before_open', reference_security='000906.XSHG')
    # 开盘时运行
    run_monthly(market_open, monthday = 1, time = 'open', reference_security='000906.XSHG')
    # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000906.XSHG')

    """
    def run_monthly(self,function):
        """
        每月执行。
        """
        pass

    def run_weekly(self,function):
        """
        每周执行。
        """
        pass

    def run_daily(self,function,run_if_miss_time = True):
        """
        每天执行。

        run_if_miss_time 如果当前启动时，错过时间点时的处理方式。
        为True时，表示依旧处理。
        为False是，表示不处理。
        """
        pass



class RunnerContext:

    def run_delay(self,function,second:int, session:str=None, cancel_confict = True):
        """
        延迟second秒之后执行。 只对今天有效。
        session: 如果不为none时，如果遇到当前还等待执行的session。
        1） cancel_confict为True，则会取消本次session的提交。
        2）cancel_confict 为False，则会替换上一次的session，继续延迟额外second秒时间。
        """
        pass

    def now(self)->datetime:
        """
        获取当前时间。(实盘环境的对应当前时间）。
        """
        pass

    def is_backtest(self)->bool:
        """
        是否回测环境。
        """
        return False

    def log(self,msg:str):
        """
        打印日志。
        """
        pass


class Runner:

    def __init__(self):
        context:RunnerContext = None

    @abstractmethod
    def getName(self):
        """
          返回程序的名字。必须唯一。
        """
        pass



    @abstractmethod
    def onStartup(self,initor:RunnerInitor):
        """
        程序启动。
        """
        pass



