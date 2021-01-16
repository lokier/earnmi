from collections import Callable
from datetime import datetime

from earnmi.core.MainEventEngine import MainEventEngine
from earnmi.core.Context import Context


class App(Context):

    def __init__(self,dirPath:str):
        super().__init__(MainEventEngine())
        self._dirPath = dirPath




