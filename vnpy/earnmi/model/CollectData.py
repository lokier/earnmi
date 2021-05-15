from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Union, Sequence

from earnmi.data.BarSoruce import BarSource
from earnmi.model.bar import BarData


@dataclass
class CollectData(object):
    """
    维度值
    """
    dimen_value:int

    """
    已知的bars
    """
    occur_bars:['BarData']

    """
    未知情况的bar值，需要预测和分析的
    """
    unkown_bars:['BarData'] = None

    """
    额外数据
    """
    extra:{} = None


    def isValid(self) -> bool:
        """
          是否有效状态
         """
        return self.valid

    def setValid(self, isValid: bool):
        if self.isFinished():
            raise RuntimeError("can't set valid if is Finished")
        self.valid = isValid

    """
    是否完成状态。（finished状态，表示unkonw_bars已经收集完整）
    """
    def isFinished(self) -> bool:
        return self.finished

    def setFinished(self):
        self.finished = True

    def __post_init__(self):
        self.unkown_bars = []
        self.extra={}
        self.valid = True
        self.finished = False


class CollectHandler:

    @abstractmethod
    def onTraceBar(self, bar: BarData) -> Union[CollectData,None]:
        """
        遍历bar，如果有CollectData事件产生，返回CollectData
        """
        raise RuntimeError("未实现")

    @abstractmethod
    def onCollecting(self,data:CollectData,bar:BarData):
        raise RuntimeError("未实现")

    def onTraceStart(self,symbol:str):
        pass

    def onTraceEnd(self,symbol:str):
        pass

    def onCollected(self, data: CollectData):
        """
        收集完成，注意：data不一定finished。
        """
        pass

    @staticmethod
    def visit(handler,source_or_bars:Union[BarSource, Sequence['BarData']],finished_list = None,un_finished_list = None):
        """
        遍历该处理器。
        参数:
            source_or_bars: bar数据来源，可以时一个BarSouce，也可以时一个BarList
            finished_list: 保存收集完成状态的数据
            un_finished_list:保存未收集完成状态的数据
        """
        _the_type = type(source_or_bars)
        if _the_type == BarSource:
            handler.__visit_soruce(source_or_bars,finished_list,un_finished_list)
        elif _the_type == list:
            handler.__visit_bars(source_or_bars,finished_list,un_finished_list)
        else:
            raise RuntimeError("unsupport type of : " + _the_type)


    def __visit_soruce(self,source:BarSource,finished_list = None,un_finished_list = None):
        for symbol, bars in source.items():
            self.__visit_bars(bars,finished_list,un_finished_list,symbol)

    def __visit_bars(self,bars:[BarData],finished_list = None,un_finished_list = None,symbol:str = None):
        if symbol is None:
            symbol = bars[0].symbol
        self.onTraceStart(symbol)
        collecting_list = []
        for bar in bars:
            toDeleteList = []
            newObject = self.onTraceBar(bar)
            for collectData in collecting_list:
                self.onCollecting(collectData, bar)
                if collectData.isFinished():
                    toDeleteList.append(collectData)
                    if collectData.isValid():
                        if not finished_list is None:
                            finished_list.append(collectData)
                        self.onCollected(collectData)
                elif not collectData.isValid():
                    toDeleteList.append(collectData)
            for collectData in toDeleteList:
                collecting_list.remove(collectData)
            if newObject is None:
                continue
            collecting_list.append(newObject)

        ###将要结束，剩下的作为未完成的finished
        for cData in collecting_list:
            if cData.isValid():
                self.onCollected(cData)
                if not un_finished_list is None:
                    un_finished_list.append(cData)
        self.onTraceEnd(symbol)



if __name__ == "__main__":
    import pickle
    from earnmi.model.CoreEngineImpl import CoreEngineImpl
    from earnmi.data.SWImpl import SWImpl


    def saveCollectData(bars:[]):

        fileName  = "files/testSaveCollectData.bin"
        with open(fileName, 'wb') as fp:
            pickle.dump(bars, fp,-1)

    def loadCollectData():
        bars = None
        fileName  = "files/testSaveCollectData.bin"
        with open(fileName, 'rb') as fp:
                bars = pickle.load(fp)
        return bars


    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)

    sw = SWImpl()

    code = sw.getSW2List()[3];
    bars = sw.getSW2Daily(code,start,end)
    #saveCollectData(bars)
    bars2 = loadCollectData()

    assert  bars == bars2
    assert  len(bars) == len(bars2) and len(bars2)!= 0
