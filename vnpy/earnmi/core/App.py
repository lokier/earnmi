from collections import Callable
from datetime import datetime

from earnmi.core.CallableEngine import CallableEngine
from earnmi.core.Context import Context


class App(Context):

    def __init__(self,dirPath:str):
        super().__init__(CallableEngine())
        self._dirPath = dirPath




