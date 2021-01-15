from collections import Callable
from datetime import datetime

from earnmi.core.CallableEngine import CallableEngine
from earnmi.core.Context import Context


class App(Context):

    def __init__(self,dirPath:str):
        ##主线程环境
        self._dirPath = dirPath
        self.engine:CallableEngine = CallableEngine()

    def post(self, function: Callable, args={}):
        self.post_delay(0,function,args)

    def post_delay(self, second: int, function: Callable, args={}):
        """
        提交到主线程，并延迟second秒执行。
        """
        if not self.engine.is_running():
            raise  RuntimeError("App main thread is not running")
        self.engine.postDelay(second,function,args)

    def now(self) -> datetime:
        return self.engine.now();

    def is_backtest(self) -> bool:
        return self.is_backtest()

    def log_i(self, msg: str):
        raise RuntimeError("未实现")

    def log_d(self, msg: str):
        raise RuntimeError("未实现")

    def log_w(self, msg: str):
        raise RuntimeError("未实现")

    def log_e(self, msg: str):
        raise RuntimeError("未实现")
