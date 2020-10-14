import os
import timeit
from datetime import datetime
from functools import cmp_to_key
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
        self.quantData:QuantData = None
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
        self.quantData = engine.queryQuantData(self.dimen)
        trainDataList = engine.getCoreStrategy().generateSampleData(engine, sampleData)
        size = len(trainDataList)
        engine.printLog(f"build PredictModel:dime={self.dimen}, sample size:{size} use SVM ={useSVM}",True)
        self.trainSampleDataList = trainDataList
        engine.printLog(f"   history quantdata: {self.quantData}")


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

    def predict(self, data: Union[CollectData, Sequence['CollectData']]) -> Union[PredictData, Sequence['PredictData']]:
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
                pData = PredictData(dimen=self.dimen, quantData=self.quantData, collectData=collectData)
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

    def predictResult(self, predict: PredictData) -> Union[bool, bool]:
        order = self.engine.getCoreStrategy().generatePredictOrder(predict)
        start_price = predict.collectData.occurBars[-2].close_price
        sell_pct = 100 * (order.suggestSellPrice - start_price) / start_price
        buy_pct = 100 * (order.suggetsBuyPrice - start_price) / start_price

        sell_ok = False
        buy_ok = False
        sell_encode = PredictModel.PctEncoder1.encode(sell_pct)
        buy_encode = PredictModel.PctEncoder1.encode(buy_pct)
        """
        命中前两个编码值，看做是预测成功
        """
        Match_INDEX_SIZE = 1
        for i in range(0, Match_INDEX_SIZE):
            sell_ok = sell_ok or sell_encode == predict.sellRange1[i].encode
            buy_ok = buy_ok or buy_encode == predict.buyRange1[i].encode

        sell_encode = PredictModel.PctEncoder2.encode(sell_pct)
        buy_encode = PredictModel.PctEncoder2.encode(buy_pct)
        for i in range(0, Match_INDEX_SIZE):
            sell_ok = sell_ok or sell_encode == predict.sellRange2[i].encode
            buy_ok = buy_ok or buy_encode == predict.buyRange2[i].encode
        return sell_ok,buy_ok

    def selfTest(self) -> Tuple[float, float]:
        self.engine.printLog("start PredictModel.selfTest()")
        predictList: Sequence['PredictData'] = self.predict(self.trainSampleDataList)
        count = len(predictList);
        if count < 0:
            return
        sellOk = 0
        buyOk = 0
        for predict in predictList:
            sell_ok, buy_ok = self.predictResult(predict)
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
    quantFloatEncoder = FloatEncoder([-7, -4.5, -3, -1.5, 0, 1.5, 3, 4.5, 7])

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

    def __getQuantFilePath(self):
        return f"{self.__file_dir}/quantData.bin"

    def __getCollectFilePath(self,dimen:Dimension):
        dirPath =  f"{self.__getCollectDirPath()}/{dimen.getKey()}"
        return dirPath



    def load(self, strategy:CoreStrategy):
        self.__strategy = strategy
        self.printLog("load() start...",True)
        with open(self.__getDimenisonFilePath(), 'rb') as fp:
            self.mAllDimension  = pickle.load(fp)
        with open(self.__getQuantFilePath(), 'rb') as fp:
            self.mQuantDataMap = pickle.load(fp)

        self.printLog(f"load() finished,总共加载{len(self.mAllDimension)}个维度数据",True)
        assert len(self.mQuantDataMap) == len(self.mAllDimension)

    def build(self, soruce: BarDataSource, strategy: CoreStrategy):
        self.printLog("build() start...", True)
        self.__strategy = strategy
        # collector.onCreate()
        bars, code = soruce.onNextBars()
        dataSet = {}
        totalCount = 0
        while not bars is None:
            finished, stop = CoreStrategy.collectBars(bars, code, strategy)
            self.printLog(f"collect code:{code}, finished:{len(finished)},stop:{len(stop)}")
            totalCount += len(finished)
            bars, code = soruce.onNextBars()
            for data in finished:
                ##收录
                listData: [] = dataSet.get(data.dimen)
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
        quantMap = {}
        for dimen, listData in dataSet.items():
            size = len(listData)
            if size < MIN_SIZE:
                continue
            quantData = self.computeQuantData(listData)
            quantMap[dimen] = quantData
            maxSize = max(maxSize, size)
            minSize = min(minSize, size)
            saveDimens.append(dimen)
            saveCollectCount += size
            filePath = self.__getCollectFilePath(dimen)
            with open(filePath, 'wb+') as fp:
                pickle.dump(listData, fp, -1)


        with open(self.__getDimenisonFilePath(), 'wb+') as fp:
            pickle.dump(saveDimens, fp, -1)

        with open(self.__getQuantFilePath(), 'wb+') as fp:
            pickle.dump(quantMap, fp, -1)

        self.printLog(
            f"build() finished, 总共保存{len(saveDimens)}/{len(dataSet)}个维度数据(>={MIN_SIZE})，共{saveCollectCount}个数据，其中最多{maxSize},最小{minSize}",
            True)
        self.load(strategy)

    def loadCollectData(self, dimen: Dimension) -> Sequence['CollectData']:
        filePath = self.__getCollectFilePath(dimen)
        collectData = None
        with open(filePath, 'rb') as fp:
            collectData = pickle.load(fp)
        return collectData

    def getCoreStrategy(self) ->CoreStrategy:
        return self.__strategy

    def computeQuantData(self, dataList: Sequence['CollectData']) -> QuantData:
        return self.__computeQuantData(CoreEngineImpl.quantFloatEncoder,CoreEngineImpl.quantFloatEncoder,dataList)

    """
        计算编码分区最佳的QuantData
        """
    def __findCenterPct(self,pct_list, min_pct,max_pct,best_pct,best_probal) -> Union[float, float]:
        if max_pct - min_pct < 0.01:
            return best_pct, best_probal

        pct = (max_pct + min_pct) / 2
        encoder = FloatEncoder([pct])
        flaotRangeList = self.__computeRangeFloatList(pct_list, encoder,False)
        probal = flaotRangeList[0].probal

        if abs(probal - 0.5) < abs(best_probal - 0.5):
            best_pct = pct
            best_probal = probal

        if probal > 0.5:
            ##说明pct值过大
            pct2,probal2 = self.__findCenterPct(pct_list,min_pct,pct,best_pct,best_probal)
        else:
            pct2,probal2 = self.__findCenterPct(pct_list,pct,max_pct,best_pct,best_probal)

        if abs(probal2 - 0.5) < abs(best_probal - 0.5):
            best_pct = pct2
            best_probal = probal2

        return best_pct,best_probal

    """
    计算编码分区最佳的QuantData
    """
    def __findBestFloatEncoder(self,pct_list:[],originEncoder:FloatEncoder)->Union[FloatEncoder,Sequence['FloatRange']]:
        SCALE = 5000
        min,max = originEncoder.parseEncode(int(originEncoder.mask()/2))
        min = int(min * SCALE)
        max = int(max * SCALE)
        step = int((max - min) / 100)

        bestProbal = 0
        bestEncoder = originEncoder
        bestRnageList = None
        for shift in range(min,max,step):
            d = shift / SCALE
            encoder = originEncoder.shift(d)
            flaotRangeList = self.__computeRangeFloatList(pct_list, encoder)
            probal = flaotRangeList[0].probal
            if probal > bestProbal:
                bestProbal = probal
                bestEncoder = encoder
                bestRnageList = flaotRangeList

        return bestEncoder,bestRnageList

    def __computeRangeFloatList(self,pct_list:[],encoder:FloatEncoder,sort = True)->Sequence['FloatRange']:
        rangeCount = {}
        totalCount = len(pct_list)
        for i in range(0, encoder.mask()):
            rangeCount[i] = 0
        for pct in pct_list:
            encode = encoder.encode(pct)
            rangeCount[encode] +=1

        rangeList = []
        for encode, count in rangeCount.items():
            probal = 0.0
            if totalCount > 0:
                probal = count / totalCount
            floatRange = FloatRange(encode=encode, probal=probal)
            rangeList.append(floatRange)
        if sort:
            return FloatRange.sort(rangeList)
        return rangeList

    def __computeQuantData(self,sellEncoder:FloatEncoder,buyEncoder:FloatEncoder,dataList: Sequence['CollectData']):

        sell_pct_list = []
        buy_pct_list = []
        totalCount = len(dataList)
        for data in dataList:
            bars: ['BarData'] = data.predictBars
            assert len(bars) > 0
            sell_pct, buy_pct = self.getCoreStrategy().getSellBuyPctLabel(data)
            sell_pct_list.append(sell_pct)
            buy_pct_list.append(buy_pct)
        sellEncoder,sellRangeFloat = self.__findBestFloatEncoder(sell_pct_list,sellEncoder)
        buyEncoder,buyRangeFloat = self.__findBestFloatEncoder(buy_pct_list,buyEncoder)

        sell_center_pct, best_probal1 = self.__findCenterPct(sell_pct_list,sellEncoder.splits[0],sellEncoder.splits[-1],0.0,0.0)
        buy_center_pct, best_probal2 = self.__findCenterPct(buy_pct_list,buyEncoder.splits[0],buyEncoder.splits[-1],0.0,0.0)
        return QuantData(count=totalCount,sellRange=sellRangeFloat,buyRange=buyRangeFloat,
                         sellCenterPct=sell_center_pct,
                         buyCenterPct=buy_center_pct,
                         sellSplits=sellEncoder.splits,buySplits=buyEncoder.splits)


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

    def printTopDimension(self,pow_rate_limit = 1.0):


        def com_quant(q1, q2):
            return q1.getPowerRate() - q2.getPowerRate()

        print(f"做多Top列表")
        dimeValues = []
        quant_list = []
        for dimen in dimens:
            quant = engine.queryQuantData(dimen)
            if quant.getPowerRate() >= pow_rate_limit:
                quant_list.append(quant)
                dimeValues.append(dimen.value)
        quant_list = sorted(quant_list, key=cmp_to_key(com_quant), reverse=True)
        for i in range(0,len(quant_list)):
            quant = quant_list[i]
            encoder = quant.getSellFloatEncoder()
            _min,_max = encoder.parseEncode(quant.sellRange[0].encode)
            print(f"[dime:{dimeValues[i]}]: count={quant.count},pow_rate=%.3f, probal=%.2f%%,centerPct=%.2f,sell:[{_min},{_max}]" % (quant.getPowerRate(), quant.getPowerProbal(True), quant.sellCenterPct))
        print(f"top dimeValues: {dimeValues}")

        print(f"做空Top列表")
        dimeValues = []
        quant_list = []
        for dimen in dimens:
            quant = engine.queryQuantData(dimen)
            if quant.getPowerRate() <= -pow_rate_limit:
                quant_list.append(quant)
                dimeValues.append(dimen.value)
        quant_list = sorted(quant_list, key=cmp_to_key(com_quant), reverse=False)
        for i in range(0,len(quant_list)):
            quant = quant_list[i]
            encoder = quant.getBuyFloatEncoder()
            _min, _max = encoder.parseEncode(quant.buyRange[0].encode)
            print(f"[dime:{dimeValues[i]}]: count={quant.count},pow_rate=%.3f, probal=%.2f%%,centerPct=%.2f,buy:[{_min},{_max}]" % (quant.getPowerRate(), quant.getPowerProbal(False), quant.buyCenterPct))
        print(f"top dimeValues: {dimeValues}")



if __name__ == "__main__":
    from earnmi.model.Strategy2kAlgo1 import Strategy2kAlgo1

    strategy = Strategy2kAlgo1()


    start = datetime(2014, 5, 1)
    end = datetime(2018, 5, 17)
    engine = CoreEngineImpl("files/impltest")
    #engine.enableLog = True

    #engine.build(SWDataSource(start,end),strategy)
    engine.load(strategy)
    dimens = engine.loadAllDimesion()
    print(f"dimension：{dimens}")

    dist_list = []
    engine.printTopDimension()

    dimen = dimens[4]
    model = engine.loadPredictModel(dimen)
    model.selfTest()


    pass
