import os
import timeit
from datetime import datetime
from typing import Tuple, Sequence, Union

import sklearn
from sklearn.ensemble import RandomForestClassifier

from earnmi.chart.FloatEncoder import FloatEncoder, FloatRange
from earnmi.model.QuantData import QuantData
from vnpy.trader.object import BarData

from earnmi.data.SWImpl import SWImpl
from earnmi.model.CollectData import CollectData
from earnmi.model.CoreEngine import CoreEngine, BarDataSource, PredictModel
from earnmi.model.Dimension import Dimension, TYPE_3KAGO1, TYPE_2KAGO1
from earnmi.model.PredictData import PredictData
import pickle
import numpy as np
from earnmi.model.CoreStrategy import CoreStrategy




class SWDataSource(BarDataSource):
    def __init__(self,start:datetime,end:datetime ):
        self.index = 0
        self.sw = SWImpl()
        self.start = start
        self.end = end

    def onNextBars(self) -> Tuple[Sequence['BarData'], str]:
        # if self.index > 2:
        #     return None,None
        sw_code_list = self.sw.getSW2List()
        if self.index < len(sw_code_list):
            code = sw_code_list[self.index]
            self.index +=1
            return self.sw.getSW2Daily(code,self.start,self.end),code
        return None,None

class SVMPredictModel(PredictModel):

    def __init__(self,engine:CoreEngine,dimen:Dimension):
        self.engine = engine
        self.dimen = dimen
        self.orginSampleQuantData:QuantData = None
        self.sampleQuantData:QuantData = None
        self.classifierSell_1 = None
        self.classifierSell_2 = None
        self.classifierBuy_1 = None
        self.classifierBuy_2 = None
        self.labelListSell1:[] = None  ##标签值列表
        self.labelListSell2:[] = None  ##标签值列表
        self.labelListBuy1:[] = None  ##标签值列表
        self.labelListBuy2:[] = None  ##标签值列表

        self.trainSampleDataList = None  ##训练样本数据。


    """
    建造模型
    """
    def build(self,engine:CoreEngine, sampleData:Sequence['CollectData']):
        useSVM = True
        start = timeit.default_timer()
        self.orginSampleQuantData = engine.computeQuantData(sampleData)
        trainDataList = engine.getCoreStrategy().generateSampleData(engine, sampleData)
        size = len(trainDataList)
        engine.printLog(f"build PredictModel:dime={self.dimen}, sample size:{size} use SVM ={useSVM}",True)
        self.trainSampleDataList = trainDataList
        self.sampleQuantData = engine.computeQuantData(trainDataList)
        engine.printLog(f"   history quantdata: {self.orginSampleQuantData}")
        engine.printLog(f"   sample quantdata: {self.sampleQuantData}")


        ##建立特征值
        x, y_sell_1,y_buy_1,y_sell_2,y_buy_2 = engine.getCoreStrategy().generateFeature(engine, trainDataList)
        y_sell_1 = y_sell_1.astype(int)
        y_buy_1 = y_buy_1.astype(int)
        y_sell_2 = y_sell_2.astype(int)
        y_buy_2 = y_buy_2.astype(int)
        self.labelListSell1 = np.sort(np.unique(y_sell_1))
        self.labelListSell2 = np.sort(np.unique(y_sell_2))
        self.labelListBuy1 = np.sort(np.unique(y_buy_1))
        self.labelListBuy2 = np.sort(np.unique(y_buy_2))
        engine.printLog(f"   labelListSell1: {self.labelListSell1}")
        engine.printLog(f"   labelListSell2: {self.labelListSell2}")
        engine.printLog(f"   labelListBuy1: {self.labelListBuy1}")
        engine.printLog(f"   labelListBuy2: {self.labelListBuy2}")

        self.classifierSell_1 = self.__createClassifier(x,y_sell_1,useSVM=useSVM)
        self.classifierSell_2 = self.__createClassifier(x,y_sell_2,useSVM=useSVM)
        self.classifierBuy_1 = self.__createClassifier(x,y_buy_1,useSVM=useSVM)
        self.classifierBuy_2 = self.__createClassifier(x,y_buy_2,useSVM=useSVM)

        elapsed = (timeit.default_timer() - start)
        engine.printLog(f"build PredictModel finished! elapsed = %.3fs" % (elapsed),True)
        pass

    def __createClassifier(self,x,y,useSVM=True):
        classifier = None
        if useSVM:
            classifier = sklearn.svm.SVC(C=2, kernel='rbf', gamma=10, decision_function_shape='ovr', probability=True)  # ovr:一对多策略
            classifier.fit(x, y)
        else:
            classifier = RandomForestClassifier(n_estimators=100, max_depth=None,min_samples_split=50, bootstrap=True)
            classifier.fit(x, y)
        return classifier

    def buldRangeList(self,label_list:[],probal_list:[]):
        fillList = []
        for index in range(0, len(probal_list)):
            encode = label_list[index]
            floatRange = FloatRange(encode=encode, probal=probal_list[index])
            fillList.append(floatRange)
        return fillList

    def predict(self, data) -> Union[PredictData, Sequence['PredictData']]:
        single = False
        engine = self.engine
        if type(data) is CollectData:
            data = [data]
            single = True
        if type(data) is list:
            x, y_sell_1,y_buy_1,y_sell_2,y_buy_2 = engine.getCoreStrategy().generateFeature(engine, data)
            retList = []
            buyRange1_probal_list = self.classifierBuy_1.predict_proba(x)
            buyRange2_probal_list = self.classifierBuy_2.predict_proba(x)
            sellRange1_probal_list = self.classifierSell_1.predict_proba(x)
            sellRange2_probal_list = self.classifierSell_2.predict_proba(x)
            for i in range(0,len(data)):
                collectData = data[i]
                pData = PredictData(dimen=self.dimen, historyData=self.orginSampleQuantData,
                                    sampleData=self.sampleQuantData, collectData=collectData)
                floatSellRangeList1 = self.buldRangeList(self.labelListSell1,sellRange1_probal_list[i])
                floatBuyRangeList1 = self.buldRangeList(self.labelListBuy1,buyRange1_probal_list[i])
                floatSellRangeList2 = self.buldRangeList(self.labelListSell2,sellRange2_probal_list[i])
                floatBuyRangeList2 = self.buldRangeList(self.labelListBuy2,buyRange2_probal_list[i])

                pData.buyRange1 = FloatRange.sort(floatBuyRangeList1)
                pData.buyRange2 = FloatRange.sort(floatBuyRangeList2)
                pData.sellRange1 = FloatRange.sort(floatSellRangeList1)
                pData.sellRange2 = FloatRange.sort(floatSellRangeList2)
                retList.append(pData)
            if single:
                return retList[-1]
            else:
                return retList
        raise RuntimeError("unsupport data！！！")

    def selfTest(self) -> Tuple[float, float]:
        self.engine.printLog("start PredictModel.selfTest()")
        predictList: Sequence['PredictData'] = self.predict(self.trainSampleDataList)
        count = len(predictList);
        if count < 0:
            return
        sellOk = 0
        buyOk = 0
        for predict in predictList:
            sell_pct,buy_pct = self.engine.getCoreStrategy().getSellBuyPctPredict(predict)
            sell_ok = False
            buy_ok = False
            sell_encode = PredictModel.PctEncoder1.encode(sell_pct)
            buy_encode = PredictModel.PctEncoder1.encode(buy_pct)
            """
            命中前两个编码值，看做是预测成功
            """
            Match_INDEX_SIZE = 1
            for i in range(0,Match_INDEX_SIZE):
               sell_ok = sell_ok or sell_encode == predict.sellRange1[i].encode
               buy_ok = buy_ok or buy_encode == predict.buyRange1[i].encode

            sell_encode = PredictModel.PctEncoder2.encode(sell_pct)
            buy_encode = PredictModel.PctEncoder2.encode(buy_pct)
            for i in range(0, Match_INDEX_SIZE):
                sell_ok = sell_ok or sell_encode == predict.sellRange2[i].encode
                buy_ok = buy_ok or buy_encode == predict.buyRange2[i].encode

            if sell_ok:
                sellOk +=1
            if buy_ok:
                buyOk +=1
        sell_core = sellOk / count
        buy_core = buyOk / count
        self.engine.printLog("selfTest : sell_core=%.2f, buy_core=%.2f" % (sell_core * 100,buy_core * 100))
        return sell_core,buy_core

class CoreEngineImpl(CoreEngine):

    COLLECT_DATA_FILE_NAME = "colllect"
    ##量化数据的涨幅分布区域。

    def __init__(self, dirPath: str):
        self.mAllDimension:['Dimension'] = None
        self.mQuantDataMap:{}= None
        self.__file_dir = dirPath
        self.__strategy = None
        self.enableLog = False

        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        collectDir = self.__getCollectDirPath()
        if not os.path.exists(collectDir):
            os.makedirs(collectDir)

    def printLog(self,info:str,forcePrint = False):
        if self.enableLog or forcePrint:
            print(f"[CoreEngineImpl]: {info}")

    def __getDimenisonFilePath(self):
        return f"{self.__file_dir}/dimension.bin"

    def __getCollectDirPath(self):
        return  f"{self.__file_dir}/colllect"


    def __getCollectFilePath(self,dimen:Dimension):
        dirPath =  f"{self.__getCollectDirPath()}/{dimen.getKey()}"
        return dirPath



    def load(self, strategy:CoreStrategy):
        self.__strategy = strategy
        self.printLog("load() start...",True)
        with open(self.__getDimenisonFilePath(), 'rb') as fp:
            self.mAllDimension  = pickle.load(fp)
        quantMap = {}
        totalCount = 0
        for dimen in self.mAllDimension:
            colectDatas = self.loadCollectData(dimen)
            quantData = self.computeQuantData(colectDatas)
            quantMap[dimen] = quantData
            totalCount += quantData.count
        self.mQuantDataMap = quantMap
        self.printLog(f"load() finished,总共加载{len(self.mAllDimension)}个维度数据,共{totalCount}个数据",True)

        assert len(quantMap) == len(self.mAllDimension)

    def loadCollectData(self, dimen: Dimension) -> Sequence['CollectData']:
        filePath = self.__getCollectFilePath(dimen)
        collectData = None
        with open(filePath, 'rb') as fp:
            collectData = pickle.load(fp)
        return collectData

    def getCoreStrategy(self) ->CoreStrategy:
        return self.__strategy

    def computeQuantData(self, dataList: Sequence['CollectData']) -> QuantData:
        sellRangeCount = {}
        buyRangeCount = {}
        totalCount = len(dataList)
        for i in range(0, CoreEngineImpl.quantFloatEncoder.mask()):
            sellRangeCount[i] = 0
            buyRangeCount[i] = 0
        for data in dataList:
            bars: ['BarData'] = data.predictBars
            assert len(bars) > 0
            sell_pct, buy_pct = self.getCoreStrategy().getSellBuyPctLabel(data)
            sell_encode = CoreEngineImpl.quantFloatEncoder.encode(sell_pct)
            buy_encode = CoreEngineImpl.quantFloatEncoder.encode(buy_pct)
            sellRangeCount[sell_encode] += 1
            buyRangeCount[buy_encode] += 1
        sellRangeFloat = []
        for encode,count in sellRangeCount.items():
            probal = 0.0
            if totalCount>0:
                probal = count / totalCount
            floatRange = FloatRange(encode=encode,probal=probal)
            sellRangeFloat.append(floatRange)

        buyRangeFloat = []
        for encode,count in buyRangeCount.items():
            probal = 0.0
            if totalCount>0:
                probal = count / totalCount
            floatRange = FloatRange(encode=encode,probal=probal)
            buyRangeFloat.append(floatRange)

        sellRangeFloat = FloatRange.sort(sellRangeFloat)
        buyRangeFloat = FloatRange.sort(buyRangeFloat)
        return QuantData(count=totalCount,sellRange=sellRangeFloat,buyRange=buyRangeFloat)

    def build(self, soruce:BarDataSource, strategy:CoreStrategy):
        self.printLog("build() start...",True)
        self.__strategy = strategy
        #collector.onCreate()
        bars,code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        while not bars is None:
           finished,stop = CoreStrategy.collectBars(bars, code, strategy)
           self.printLog(f"collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
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
        self.printLog(f"总共收集到{totalCount}数据，维度个数:{len(dimes)}")

        self.printLog(f"开始保存数据")
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
        self.printLog(f"build() finished, 总共保存{len(saveDimens)}个维度数据(>={MIN_SIZE})，共{saveCollectCount}个数据，其中最多{maxSize},最小{minSize}",True)
        self.load(strategy)

    def collect(self, bars: ['BarData']) -> Tuple[Sequence['CollectData'], Sequence['CollectData']]:
        collector = self.__strategy
        #collector.onCreate()
        code = bars[0].symbol
        finished, stop = CoreStrategy.collectBars(bars, code, collector)
        return finished,stop

    def loadAllDimesion(self) -> Sequence['Dimension']:
        return self.mAllDimension

    def queryQuantData(self, dimen: Dimension) -> QuantData:
        return self.mQuantDataMap.get(dimen)

    def loadPredictModel(self, dimen: Dimension) -> PredictModel:
        try:
            collectDataList = self.loadCollectData(dimen)
            if collectDataList is None:
                return None
            model = SVMPredictModel(self,dimen)
            model.build(self,collectDataList)
            return model
        except FileNotFoundError:
            return None
        except BaseException:
            return None

    def toStr(self,data:QuantData) ->str:

        info = f"count:{data.count}"
        info+=",sell:["
        for fRange in data.sellRange:
            item:FloatRange = fRange
            min,max = CoreEngineImpl.quantFloatEncoder.parseEncode(item.encode)
            info+=f"{min}:{max}=%.2f%%, " % (100 * item.probal)
        info += "],buy:["
        for fRange in data.buyRange:
            item: FloatRange = fRange
            min, max = CoreEngineImpl.quantFloatEncoder.parseEncode(item.encode)
            info += f"{min}:{max}=%.2f%%, " % (100 * item.probal)
        info +="]"
        return info

if __name__ == "__main__":
    from earnmi.model.Strategy2kAlgo1 import Strategy2kAlgo1

    strategy = Strategy2kAlgo1()


    start = datetime(2014, 5, 1)
    end = datetime(2018, 5, 17)
    engine = CoreEngineImpl("files/impltest")
    engine.enableLog = True

    #engine.build(SWDataSource(start,end),strategy)
    engine.load(strategy)
    dimens = engine.loadAllDimesion()
    print(f"dimension：{dimens}")

    for dimen in dimens:
        quant = engine.queryQuantData(dimen)
        print(f"quant：{engine.toStr(quant)}")

    ## 一个预测案例
    dimen = dimens[4]
    model = engine.loadPredictModel(dimen)
    model.selfTest()


    pass
