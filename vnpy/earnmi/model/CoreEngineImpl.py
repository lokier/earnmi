from datetime import datetime
from typing import Tuple, Sequence

from earnmi.chart.Indicator import Indicator
from earnmi.chart.KPattern import KPattern
from earnmi.model.QuantData import QuantData
from vnpy.trader.object import BarData

from earnmi.data.SWImpl import SWImpl
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngine import CoreEngine, BarDataSource, CoreCollector
from earnmi.model.Dimension import Dimension, TYPE_3KAGO1
from earnmi.model.PredictData import PredictData
import numpy as np


class SWDataSource(BarDataSource):



    def __init__(self,start:datetime,end:datetime ):
        self.index = 0
        self.sw = SWImpl()
        self.start = start
        self.end = end

    def onNextBars(self) -> Tuple[Sequence['BarData'], str]:
        sw_code_list = self.sw.getSW2List()
        if self.index < len(sw_code_list):
            code = sw_code_list[self.index]
            self.index +=1
            return self.sw.getSW2Daily(code,self.start,self.end),code
        return None,None


class CoreEngineImpl(CoreEngine):

    __file_dir: str
    __collector:CoreCollector = None

    def __init__(self, filePath: str):
        self.__file_dir = filePath

    def build(self,soruce:BarDataSource,collector:CoreCollector):
        print("[CoreEngine]: build start...")
        self.__collector = collector
        collector.onCreate()
        lists,code = soruce.onNextBars()
        while not lists is None:
           finished,stop = self.__collect__internel(lists,code,collector)
           print(f"[CoreEngine]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
           lists, code = soruce.onNextBars()
        collector.onDestroy()
        pass

    def collect(self, bars: ['BarData']) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector = self.__collector
        collector.onCreate()
        code = bars[0].symbol
        finished,stop = self.__collect__internel(bars,code,collector)
        collector.onDestroy()
        return finished,stop

    def __collect__internel(self, barList: ['BarData'],symbol:str,collector:CoreCollector) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector.onStart(symbol)
        traceItems = []
        finishedData = []
        stopData = []
        for bar in barList:
            toDeleteList = []
            for traceObject in traceItems:
                isFinished = collector.onTrace(traceObject, bar)
                if isFinished:
                    toDeleteList.append(traceObject)
                    finishedData.append(traceObject)
            for traceItem in toDeleteList:
                traceItems.remove(traceItem)
            traceObject = collector.collect(bar)
            if traceObject is None:
                continue
            traceItems.append(traceObject)

        ###将要结束，未追踪完的traceData
        for traceObject in traceItems:
            stopData.append(traceObject)
        collector.onEnd(symbol)
        return finishedData,stopData

    def loadAllDimesion(self, type: int) -> Sequence['Dimension']:
        pass

    def queryQuantData(self, dimen: Dimension) -> QuantData:
        pass

    def predict(self, data: Tuple[CollectData, Sequence['CollectData']]) -> Tuple[PredictData, Sequence['PredictData']]:
        pass


if __name__ == "__main__":
    class Collector3KAgo1(CoreCollector):

        def __init__(self):
            self.lasted3Bar = np.array([None,None,None])

        def onStart(self, code: str) -> bool:
            self.indicator = Indicator(40)
            self.code = code
            return True

        def collect(self, bar: BarData) -> CollectData:
            self.indicator.update_bar(bar)
            self.lasted3Bar[:-1] = self.lasted3Bar[1:]
            self.lasted3Bar[-1] = bar

            kPatternValue = KPattern.encode3KAgo1(self.indicator)
            if not kPatternValue is None :
                dimen = Dimension(type=TYPE_3KAGO1,value=kPatternValue)
                collectData = CollectData(dimen=dimen)
                collectData.occurBars.append(self.lasted3Bar[0])
                collectData.occurBars.append(self.lasted3Bar[1])
                collectData.occurBars.append(self.lasted3Bar[2])
                return collectData
            return None

        def onTrace(self, data: CollectData, newBar: BarData) -> bool:
            data.predictBars.append(newBar)
            size = len(data.predictBars)
            return size >= 2


    start = datetime(2014, 5, 1)
    end = datetime(2020, 8, 17)
    engine = CoreEngineImpl("files")
    engine.build(SWDataSource(start,end),Collector3KAgo1())

    pass
