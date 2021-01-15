import datetime
from abc import abstractmethod
from typing import Callable


class Context:

    @abstractmethod
    def post(self, function: Callable, args={}):
        """
        延迟second秒之后执行。
        """
        pass

    @abstractmethod
    def post_delay(self, second: int, function: Callable, args={}):
        """
        提交到主线程，并延迟second秒执行。
        """
        pass

    @abstractmethod
    def now(self) -> datetime:
        """
        获取当前时间。(实盘环境的对应的是当前时间，回撤环境对应的回撤时间）。
        """
        pass

    @abstractmethod
    def is_backtest(self) -> bool:
        """
        是否在回测环境下运行。
        """
        pass

    @abstractmethod
    def log_i(self, msg: str):
        """
        打印信息日志
        """
        pass

    @abstractmethod
    def log_d(self, msg: str):
        """
         打印调试日志
        """
        pass

    @abstractmethod
    def log_w(self, msg: str):
        """
        打印警告日志
        """
        pass

    @abstractmethod
    def log_e(self, msg: str):
        """
        打印错误日志
        """
        pass







