import logging
import os
from datetime import datetime
from pathlib import Path

from earnmi.core.MainEventEngine import MainEventEngine
from earnmi.core.Context import Context
from earnmi.core.RunnerManager import RunnerManager
from earnmi.data.BarManager import BarManager
from earnmi.uitl.LogUtil import LogUtil

__all__ = [
    # Super-special typing primitives.
    'RunnerManager',
]


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
        log_path = self._appDirPath.joinpath("earnmi_app.log")
        self._logger = App.__create_Filelogger(log_path,"earnmi_app");
        print(f"app dir: {self._appDirPath}")

    def getBarManager(self)->BarManager:
        return self.bar_manager

    def getRunnerManager(self)->RunnerManager:
        return self.runner_manager

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

    def log_i(self,tag, msg: str):
        self._logger.info(f"[{self.engine.now()}|{self.is_mainThread()}|{tag}]: {msg}")

    def log_d(self,tag, msg: str):
        self._logger.debug(f"[{self.engine.now()}|{self.is_mainThread()}|{tag}]: {msg}")

    def log_w(self,tag, msg: str):
        self._logger.warn(f"[{self.engine.now()}|{self.is_mainThread()}|{tag}]: {msg}")

    def log_e(self,tag, msg: str):
        self._logger.error(f"[{self.engine.now()}|{self.is_mainThread()}|{tag}]: {msg}")

    @staticmethod
    def __create_Filelogger(log_path, logging_name):
        '''
        配置log
        :param log_path: 输出log路径
        :param logging_name: 记录中name，可随意
        :return:
        '''
        '''
        logger是日志对象，handler是流处理器，console是控制台输出（没有console也可以，将不会在控制台输出，会在日志文件中输出）
        '''
        # 获取logger对象,取名
        logger = logging.getLogger(logging_name)
        # 输出DEBUG及以上级别的信息，针对所有输出的第一层过滤
        logger.setLevel(level=logging.DEBUG)
        # 获取文件日志句柄并设置日志级别，第二层过滤
        handler = logging.FileHandler(log_path, encoding='UTF-8')
        handler.setLevel(logging.DEBUG)
        # 生成并设置文件日志格式
        formatter = logging.Formatter('%(levelname)s:%(message)s')
        handler.setFormatter(formatter)
        # console相当于控制台输出，handler文件输出。获取流句柄并设置日志级别，第二层过滤
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        # 为logger对象添加句柄
        logger.addHandler(handler)
        logger.addHandler(console)

        return logger


