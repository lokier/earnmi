import os
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
import pickle


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

    COLLECT_DATA_FILE_NAME = "colllect"
    __file_dir: str
    __collector:CoreCollector = None

    def __init__(self, dirPath: str):
        self.__file_dir = dirPath
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        collectDir = self.__getCollectDirPath()
        if not os.path.exists(collectDir):
            os.makedirs(collectDir)

    def __getDimenisonFilePath(self):
        return f"{self.__file_dir}/dimension.bin"

    def __getCollectDirPath(self):
        return  f"{self.__file_dir}/colllect"


    def __getCollectFilePath(self,dimen:Dimension):
        dirPath =  f"{self.__getCollectDirPath()}/{dimen.getKey()}"
        return dirPath

    def build(self,soruce:BarDataSource,collector:CoreCollector):
        print("[CoreEngine]: build start...")
        self.__collector = collector
        collector.onCreate()
        bars,code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        while not bars is None:
           finished,stop = self.__collect__internel(bars,code,collector)
           print(f"[CoreEngine]: collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
           totalCount += len(finished)
           bars, code = soruce.onNextBars()
           for data in finished:
               ##收录
               listData:[] = dataSet.get(data.dimen)
               if listData is None:
                   listData = []
                   dataSet[data.dimen] = listData
               listData.append(data)
        dimes = dataSet.keys()
        print(f"[CoreEngine]: 总共收集到{totalCount}数据，维度个数:{len(dimes)}")

        print(f"[CoreEngine]: 开始保存数据")
        MIN_SIZE = 300
        saveDimens = []
        saveCollectCount = 0
        maxSize = 0
        minSize = 9999999999
        for dimen,listData in dataSet.items():
            size = len(listData)
            if size  < MIN_SIZE:
                continue
            maxSize = max(maxSize,size)
            minSize = min(minSize,size)
            saveDimens.append(dimen)
            saveCollectCount += size
            filePath = self.__getCollectFilePath(dimen)
            with open(filePath, 'wb+') as fp:
                pickle.dump(listData, fp, -1)

        with open(self.__getDimenisonFilePath(), 'wb+') as fp:
            pickle.dump(saveDimens, fp, -1)
        print(f"[CoreEngine]: 总共保存{len(saveDimens)}个维度数据(>={MIN_SIZE})，共{saveCollectCount}个数据，其中最多{maxSize},最小{minSize}")

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
    engine = CoreEngineImpl("files/impltest")
    engine.build(SWDataSource(start,end),Collector3KAgo1())

    pass
