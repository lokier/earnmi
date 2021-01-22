import datetime
from abc import abstractmethod
from pathlib import Path
from typing import Callable

from earnmi.core.MainEventEngine import MainEventEngine


class Context:

    def __init__(self, engine:MainEventEngine):
        ##主线程环境
        self.engine: MainEventEngine = engine

    def post(self, function: Callable, args={}):
        """
        提交到主线程执行。
        """
        self.post_delay(0, function, args)

    def post_delay(self, second: int, function: Callable, args={}):
        """
        提交到主线程，并延迟second秒执行。
        """
        if not self.engine.is_running():
            raise RuntimeError("App main thread is not running")
        self.engine.postDelay(second, function, args)


    def now(self) -> datetime:
        """
        获取当前时间。(实盘环境的对应的是当前时间，回撤环境对应的回撤时间）。
        """
        return self.engine.now();

    def is_backtest(self) -> bool:
        """
        是否在回测环境下运行。
        """
        return self.is_backtest()

    def is_mainThread(self) -> bool:
        """
        是否在主线程环境
        """
        return self.engine.inCallableThread()

    def log_i(self, msg: str):
        print(f"[{self.engine.now()}|{self.is_mainThread()}]: {msg}")

    def log_d(self, msg: str):
        print(f"[{self.engine.now()}|{self.is_mainThread()}]: {msg}")

    def log_w(self, msg: str):
        print(f"[{self.engine.now()}|{self.is_mainThread()}]: {msg}")

    def log_e(self, msg: str):
        print(f"[{self.engine.now()}|{self.is_mainThread()}]: {msg}")

    @abstractmethod
    def getDirPath(self, dirName,create_if_no_exist =True)->Path:
        """
        获取文件目录
        """
        raise RuntimeError("未实现")

    @abstractmethod
    def getFilePath(self, dirName:str,fileName:str)->Path:
        """
        获取文件目录
        """
        raise RuntimeError("未实现")

    # def getRunnerManager(self)->RunnerManager:
    #     raise RuntimeError("未实现")

class ContextWrapper(Context):

    def __init__(self, context:Context):
        ##主线程环境
        self._context = context

    def post(self, function: Callable, args={}):
        """
        提交到主线程执行。
        """
        self._context.post_delay(0, function, args)

    def post_delay(self, second: int, function: Callable, args={}):
        """
        提交到主线程，并延迟second秒执行。
        """
        if not self.engine.is_running():
            raise RuntimeError("App main thread is not running")
        self._context.engine.postDelay(second, function, args)


    def now(self) -> datetime:
        """
        获取当前时间。(实盘环境的对应的是当前时间，回撤环境对应的回撤时间）。
        """
        return self._context.engine.now();

    def is_backtest(self) -> bool:
        """
        是否在回测环境下运行。
        """
        return self._context.is_backtest()

    def is_mainThread(self) -> bool:
        """
        是否在主线程环境
        """
        return self._context.engine.inCallableThread()

    def log_i(self, msg: str):
        self._context.log_i(msg)

    def log_d(self, msg: str):
        self._context.log_d(msg)

    def log_w(self, msg: str):
        self._context.log_w(msg)

    def log_e(self, msg: str):
        self._context.log_e(msg)

    @abstractmethod
    def getDirPath(self, dirName,create_if_no_exist =True):
        return self._context.getDirPath(dirName,create_if_no_exist)

    @abstractmethod
    def getFilePath(self, dirName:str,fileName:str):
        return self._context.getFilePath(dirName,fileName)



    # def getRunnerManager(self)->RunnerManager:
    #     return self._context.getRunnerManager()


