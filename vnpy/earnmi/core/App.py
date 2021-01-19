import os
from datetime import datetime
from pathlib import Path

from earnmi.core.MainEventEngine import MainEventEngine
from earnmi.core.Context import Context
from earnmi.core.RunnerManager import RunnerManager
from earnmi.data.BarManager import BarManager


class App(Context):

    def __init__(self,appDirPath:str = None):
        super().__init__(MainEventEngine())
        if appDirPath is None:
            home_path = Path.home()
            self._appDirPath:Path = home_path.joinpath("earnmi_app_dir")
        else:
            self._appDirPath:Path = Path(appDirPath)
        if not self._appDirPath.exists():
            self._appDirPath.mkdir()
        self.runner_manager:RunnerManager = RunnerManager(self)
        self.bar_manager = BarManager(self)
        print(f"app dir: {self._appDirPath}")


    def getDirPath(self, dirName,create_if_no_exist =True):
        dirPath = self._appDirPath.joinpath(dirName)
        if create_if_no_exist and not dirPath.exists():
             dirPath.mkdir()
        return dirPath

    def getFilePath(self, dirName: str, fileName: str):
        return self.getDirPath(dirName,True).joinpath(fileName)


    def run(self):
        assert not self.engine.is_running()
        self.running = True
        self.engine.run()

    def run_backtest(self,start:datetime):
        assert not self.engine.is_running()
        self.running = True
        self.engine.run_backtest(start)



