from collections import Callable
from datetime import datetime

from earnmi.core.MainEventEngine import MainEventEngine
from earnmi.core.Context import Context
from earnmi.core.RunnerManager import RunnerManager
from earnmi.data.BarDriver import BarDriver, BarDriverManager


class App(Context):

    def __init__(self,dirPath:str):
        super().__init__(MainEventEngine())
        self._dirPath = dirPath
        self.runnerManager:RunnerManager = RunnerManager(self)
        self.bar_driver_manager = BarDriverManager()




    def run(self):
        assert not self.engine.is_running()
        self.running = True
        self.engine.run()

    def run_backtest(self,start:datetime):
        assert not self.engine.is_running()
        self.running = True
        self.engine.run_backtest(start)


