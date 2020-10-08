from datetime import datetime, timedelta
from functools import cmp_to_key
from typing import Sequence

import pandas as pd
import numpy as np
import sklearn
from sklearn import model_selection
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
import pickle


from earnmi.data.SWImpl import SWImpl
from earnmi.model.PredictData2 import PredictData
from earnmi.uitl.utils import utils
from vnpy.trader.object import BarData

"""

预测当前申万行业明天最有可能涨的前几个行业。
"""

class PredictModel:

    def __init__(self):
        self.data_x = None
        self.data_y_sell = None
        self.data_y_buy = None
        self.labels_y_sell = None
        self.labels_y_buy = None
        self.randomForest_for_sell = None
        self.randomForest_for_buy = None

    """
    预处理特征数据。
    """
    def __pre_process(self,df:pd.DataFrame):
        def set_0_or_1(x):
            if x >= 2:
                return 1
            return 0
        def percent_to_one(x):
            return int(x * 100) / 1000.0
        def toInt(x):
            v =  int(x + 0.5)
            if v > 10:
                v = 10
            if v < -10:
                v = -10
            return v
        d = df
        d['buy_price'] = d.buy_price.apply(percent_to_one)  # 归一化
        d['sell_price'] = d.sell_price.apply(percent_to_one)  # 归一化
        d['label_sell_price'] = d.label_sell_price.apply(toInt)
        d['label_buy_price'] = d.label_buy_price.apply(toInt)
        d.k = d.k / 100
        d.j = d.j / 100

        df = df.drop(columns=['code', 'kPattern', 'name'])
        data = df.values
        x, y = np.split(data, indices_or_sections=(4,), axis=1)  # x为数据，y为标签
        y_sell = y[:, 0:1].astype('int')  # 取第一列
        y_buy = y[:, 1:2].astype('int')  # 取第一列

        return x, y_sell.ravel(),y_buy.ravel()

    def setFeature(self, df:pd.DataFrame):
        self.data_x,self.data_y_sell,self.data_y_buy = self.__pre_process(df)
        self.labels_y_sell = np.sort(np.unique(self.data_y_sell))
        self.labels_y_buy = np.sort(np.unique(self.data_y_buy))


    def saveToFile(self,fileName:str):
        with open(fileName, 'wb') as fp:
            pickle.dump(self.data_x, fp,-1)
            pickle.dump(self.data_y_sell, fp,-1)
            pickle.dump(self.data_y_buy, fp,-1)
            pickle.dump(self.labels_y_sell, fp,-1)
            pickle.dump(self.labels_y_buy, fp,-1)

    def loadFromFile(self,fileName:str):
        with open(fileName, 'rb') as fp:
            self.data_x = pickle.load(fp)
            self.data_y_sell = pickle.load(fp)
            self.data_y_buy = pickle.load(fp)
            self.labels_y_sell = pickle.load(fp)
            self.labels_y_buy = pickle.load(fp)

    def getClassifier(self,isSell = True):
        if isSell:
            if self.randomForest_for_sell is None:
                self.randomForest_for_sell = RandomForestClassifier(n_estimators=100, max_depth=None, min_samples_split=50,
                                                           bootstrap=True)
                self.randomForest_for_sell.fit(self.data_x, self.data_y_sell)
            return self.randomForest_for_sell
        else:
            if self.randomForest_for_buy is None:
                self.randomForest_for_buy = RandomForestClassifier(n_estimators=100, max_depth=None, min_samples_split=50,
                                                           bootstrap=True)
                self.randomForest_for_buy.fit(self.data_x, self.data_y_buy)
            return self.randomForest_for_buy

    def predict(self,feature:pd.DataFrame) -> Sequence["PredictData"]:
        x, y_sell,y_buy = self.__pre_process(feature)
        classifier_sell = self.getClassifier(isSell = True)
        classifier_buy = self.getClassifier(isSell = False)

        predic_y_sell_proba = classifier_sell.predict_proba(x)
        predic_y_buy_proba = classifier_buy.predict_proba(x)

        size = len(x)
        predict_data_list = []
        for i in range(0, size):
            y_proba_list_sell = predic_y_sell_proba[i]  ##预测值
            y_proba_list_buy = predic_y_buy_proba[i]  ##预测值

            percent_sell,probal_sell,orgin_sell_percent,max_sell_proba = self.__compute_prdict_data(y_proba_list_sell, self.labels_y_sell, True)
            percent_buy,probal_buy,orgin_buy_percent,max_buy_proba = self.__compute_prdict_data(y_proba_list_buy, self.labels_y_buy, False)


            predictSell = PredictData(percent=percent_sell, probability=probal_sell,label=orgin_sell_percent,label_prob=max_sell_proba)
            predictBuy = PredictData(percent=percent_buy, probability=probal_buy,label=orgin_buy_percent,label_prob=max_buy_proba)

            level = 0

            if orgin_sell_percent > orgin_buy_percent:
                delta = orgin_sell_percent - orgin_buy_percent
                level += 0.4 * delta
            if orgin_buy_percent > 0:
                level += orgin_buy_percent

            predictSell.level = level
            predictSell.percent_real = y_sell[i]
            predictBuy.percent_real = y_buy[i]
            predictSell.buy = predictBuy
            predict_data_list.append(predictSell)

        return predict_data_list

    def __compute_prdict_data(self, y_proba_list:[], y_label:[], isSell=True):
        index = -1  ##查找最高的index
        max_proba = -100000
        for j in range(0, len(y_proba_list)):
            proba = y_proba_list[j]
            if proba > max_proba:
                max_proba = proba
                index = j
        assert index != -1
        total_probal = 0.0
        if isSell:
            for j in range(index, len(y_proba_list)):
                total_probal += y_proba_list[j]
        else:
            for j in range(0, index+1):
                total_probal += y_proba_list[j]

        probal_2 = None
        percent_2 = None
        if index > 0:
            probal_2 = y_proba_list[index - 1]
            percent_2 = y_label[index - 1]

        if index < len(y_label) - 1:
            if probal_2 is None or probal_2 < y_proba_list[index + 1]:
                probal_2 = y_proba_list[index + 1]
                percent_2 = y_label[index + 1]

        orgin_percent = y_label[index]
        percent = percent_2 * probal_2 / (max_proba + probal_2) + y_label[index] * max_proba / (
                    max_proba + probal_2)
        return percent,total_probal,orgin_percent,max_proba

    def printCrossScoreTest(self):
        x_train, x_test, y_train, y_test = model_selection.train_test_split(self.data_x, self.data_y_sell, train_size=0.7, test_size=0.3)
        y_train = y_train.ravel()
        y_test = y_test.ravel()

        clf1 = DecisionTreeClassifier(max_depth=None, min_samples_split=2, random_state=0)
        clf2 = RandomForestClassifier(n_estimators=50, max_depth=None, min_samples_split=50, bootstrap=True)
        clf3 = ExtraTreesClassifier(n_estimators=10, max_depth=None, min_samples_split=2, bootstrap=False)

        scores1 = cross_val_score(clf1, x_train, y_train)
        scores2 = cross_val_score(clf2, x_train, y_train)
        scores3 = cross_val_score(clf3, x_train, y_train)
        print('DecisionTreeClassifier交叉验证准确率为:' + str(scores1.mean()))
        print('RandomForestClassifier交叉验证准确率为:' + str(scores2.mean()))
        print('ExtraTreesClassifier交叉验证准确率为:' + str(scores3.mean()))

    def printPredictInfo(self,df:pd.DataFrame):
        predictList = self.predict(df.copy(deep=False))
        for predictData in predictList:
            print(f"预测值为:{predictData}")

        pass


class PredictModel2(PredictModel):

    def __init__(self):
        super().__init__()
        self.svm_for_sell = None
        self.svm_for_buy = None

    def getClassifier(self,isSell=True):
        if isSell:
            if self.svm_for_sell is None:
                self.svm_for_sell = RandomForestClassifier(n_estimators=100, max_depth=None,
                                                                    min_samples_split=50,
                                                                    bootstrap=True)
                self.svm_for_sell.fit(self.data_x, self.data_y_sell)
            return self.svm_for_sell
        else:
            if self.svm_for_buy is None:
                self.svm_for_buy = RandomForestClassifier(n_estimators=100, max_depth=None,
                                                                   min_samples_split=50,
                                                                   bootstrap=True)
                self.svm_for_buy.fit(self.data_x, self.data_y_buy)
            return self.svm_for_buy

    def printCrossScoreTest(self):
        train_data, test_data, train_label, test_label = model_selection.train_test_split(self.data_x, self.data_y_sell, train_size=0.7,
                                                                                          test_size=0.3)
        train_label = train_label.ravel()
        test_label = test_label.ravel()
        classifier = sklearn.svm.SVC(C=2, kernel='rbf', gamma=10, decision_function_shape='ovr', probability=True)  # ovr:一对多策略
        classifier.fit(train_data, train_label)  # ravel函数在降维时默认是行序优先
        print("训练集：", classifier.score(train_data, train_label))
        print("测试集：", classifier.score(test_data, test_label))



def buildAndSaveModel(start:datetime,end:datetime,patternList=[]):
    sw = SWImpl()

    from earnmi_demo.strategy_demo.kbars.analysis_KPattern_skip1_predit2 import \
        Generate_Feature_KPattern_skip1_predit2

    for kPattern in patternList:
        generateTrainData = Generate_Feature_KPattern_skip1_predit2(kPatters=[kPattern])
        sw.collect(start, end, generateTrainData)
        featureData = generateTrainData.getPandasData()

        filleName = f"models/predict_sw_top_k_{kPattern}.m"

        print(f"k线形态[{kPattern}]的模型能力:")
        model = PredictModel()
        model.setFeature(featureData)
        model.printCrossScoreTest()
        model.saveToFile(filleName)

def printPerdictDetail(predictStart:datetime,predictEnd:datetime,patternList=[]):
    def compute_result(model, feature):

        predict_sell = model.predict(feature)[0]
        predict_buy = predict_sell.buy

        close_price = traceData.occurBar.close_price
        predict_price = close_price * (1 + predict_sell.percent / 100.0)

        buy_price = traceData.skipBar.close_price

        profile_pct = (predict_price - buy_price) / close_price

        deal = False
        sucess = False
        sell_day = -1
        if predict_price > close_price and predict_sell.label > predict_buy.label:
            deal = True
            # if predict_sell.label < 1:
            #     deal = False

        if deal == True:
            for i in range(0, len(traceData.predictBars)):
                bar: BarData = traceData.predictBars[i]
                if predict_price < bar.high_price:
                    sell_day = i
                    break
            can_sell = sell_day != -1
            if can_sell:
                sucess = True
                # print(f"SUC  : profile_pct = {profile_pct},sell_day = {sell_day},prob={predict1.probability}")
            else:
                profile_pct = (traceData.predictBars[-1].close_price - buy_price) / close_price
        return deal, sucess, sell_day, profile_pct, predict_sell.probability, predict_sell

    class CountItem(object):
        kPattern = 0
        rf_success_count = 0
        rf_size = 0
        svm_size = 0
        svm_success_count = 0
        rf_earn_pct = 0.0
        svm_earn_pct = 0.0

    # patternList = [535]
    total_count = 0
    fail_count = 0

    generateTrainData = Generate_Feature_KPattern_skip1_predit2(kPatters=patternList)
    sw.collect(predictStart, predictEnd, generateTrainData)

    countList = []
    for kPattern in patternList:
        filleName = f"models/predict_sw_top_k_{kPattern}.m"
        model = PredictModel()
        model.loadFromFile(filleName)
        model2 = PredictModel2()
        model2.loadFromFile(filleName)
        traceDatas = generateTrainData.traceDatas

        countItem = CountItem()
        countItem.kPattern = kPattern
        for traceData in traceDatas:
            if traceData.kPatternValue != kPattern:
                continue
            feature1 = generateTrainData.generateData([traceData])
            feature2 = generateTrainData.generateData([traceData])
            deal, sucess, sell_day, profile_pct, probability,predict = compute_result(model, feature1)
            deal2, sucess2, sell_day2, profile_pct2, probability2,predict2 = compute_result(model2, feature2)

            if deal == True or deal2 == True:
                total_count += 1
                if sucess != True or sucess2 != True:
                    fail_count += 1

            if deal == True:
                countItem.rf_size +=1
                countItem.rf_earn_pct += profile_pct
                if sucess == True:
                    countItem.rf_success_count += 1
                sell = predict
                buy = predict.buy
                print(f"  percent:[{sell.percent}({sell.label})({sell.percent_real}),{buy.percent}({buy.label})({buy.percent_real})],prob:[{sell.probability}({sell.label_prob}),{buy.probability}({buy.label_prob})]")
                print(f"rf sucess:{sucess},profile_pct = {profile_pct},sell_day = {sell_day},prob={probability}\n")

            if deal2 == True:
                countItem.svm_size += 1
                countItem.svm_earn_pct += profile_pct2

                if sucess2 == True:
                    countItem.svm_success_count += 1
                sell = predict2
                buy = predict2.buy
                print(
                    f"  percent:[{sell.percent}({sell.label})({sell.percent_real}),{buy.percent}({buy.label})({buy.percent_real})],prob:[{sell.probability}({sell.label_prob}),{buy.probability}({buy.label_prob})]")

                print(f"svm sucess:{sucess2},profile_pct = {profile_pct2},sell_day = {sell_day2},prob={probability2}\n")

        if countItem.rf_size > 0 or countItem.svm_size > 0:
            countList.append(countItem)

    sucess_rate = 100 * (1 - (fail_count) / total_count)

    print(f"total count:{total_count}, sucess_rate:%.2f%%" % (sucess_rate))

    infos1 = "  "
    infos2 = "  "

    count1 = 0
    sucess1 = 0
    count2 = 0
    sucess2 = 0
    for countItem in countList:
        count1 += countItem.rf_size
        sucess1 += countItem.rf_success_count
        count2 += countItem.svm_size
        sucess2 += countItem.svm_success_count
        if countItem.rf_size > 0:
             pct = 100 * countItem.rf_earn_pct / countItem.rf_size
             __suc_rate = 100 * countItem.rf_success_count / countItem.rf_size
             if __suc_rate > 0:
                infos1 += f"[{countItem.kPattern}:{countItem.rf_size}= %.2f%%,pct=%.2f%%]" % (__suc_rate,pct)
        if countItem.svm_size > 0:
            pct = 100 * countItem.svm_earn_pct / countItem.svm_size
            __suc_rate = 100 * countItem.svm_success_count / countItem.svm_size
            if __suc_rate > 0:
                infos2 += f"[{countItem.kPattern}:{countItem.svm_size}= %.2f%%,pct=%.2f%%]" % (__suc_rate,pct)

    print(f"rf count:{count1}, sucess_rate:%.2f%%" % (100 * sucess1 / count1))
    print(f"{infos1}")
    print(f"svm count:{count2}, sucess_rate:%.2f%%" % (100 * sucess2 / count2))
    print(f"{infos2}")


def printTop5(patternList=[]):
    end = utils.to_end_date(datetime.now() - timedelta(days=1))  ##昨天数据集
    start = end - timedelta(days=60)

    #sw = SWImpl()
    generateTrainData = Generate_Feature_KPattern_skip1_predit2(kPatters=patternList)

    code = sw.getSW2List()[0]
    bars = sw.getSW2Daily(code,start,end)
    yestoday = bars[-1].datetime
    yestoday2 = bars[-2].datetime



    class TopData(object):
        kCode = 0
        predict:PredictData = None
        code = ""
        name =""


    sw.collect(start, end,generateTrainData)
    yestoday_top = []
    yestoday2_top = []

    print(f"count:{len(generateTrainData.predictTraceDatas)},上个交易日:{yestoday}")
    for ___traceData in generateTrainData.predictTraceDatas:
       traceData:Skip1_Predict2_TraceData = ___traceData

       topData = TopData()
       topData.code = traceData.code
       topData.name = sw.getSw2Name(topData.code)


       if len(traceData.predictBars) > 0:
           yestoday2_top.append(topData)
           assert utils.is_same_day(traceData.predictBars[-1].datetime,yestoday)
       else:
           yestoday_top.append(topData)
       kPattern = traceData.kPatternValue
       filleName = f"models/predict_sw_top_k_{kPattern}.m"
       model = PredictModel()
       model.loadFromFile(filleName)

       feature = generateTrainData.generateData([traceData])

       predict =  model.predict(feature)[0]
       topData.kCode = kPattern
       topData.predict = predict
       occurBar = traceData.occurBar
       close_price = occurBar.close_price
       topData.start_price = close_price
       #topData.sell_price = close_price * (1 + predict.percent / 100.0)
       #topData.buy_price = close_price * (1 + predict.buy.percent / 100.0)


    def compareTopBar(d1:TopData,d2:TopData):
        if d1.predict.level != d2.predict.level:
            return d1.predict.level - d2.predict.level
        delta = d1.predict.percent - d2.predict.percent
        if delta!= 0:
            return delta
        if d1.predict.probability < d2.predict.probability:
            return -1
        else:
            return 1

    yestoday_top = sorted(yestoday_top,key=cmp_to_key(compareTopBar),reverse=True)
    yestoday2_top = sorted(yestoday2_top,key=cmp_to_key(compareTopBar),reverse=True)

    def printTopData(topData,isDouble= False):
        if topData is None:
            return
        pct = topData.predict.percent - topData.predict.buy.percent
        double_info = ""
        if isDouble:
            double_info = "****************"
        print(f"[code:{topData.code},name:{topData.name},kCode:{topData.kCode}"
              f",[sell:%.2f%%,buy:%.2f%%,pct=%.2f%%]] {double_info}" % (topData.predict.percent, topData.predict.buy.percent, pct))
    print(f"昨天top数据")
    for topData in yestoday_top:
       yestory_data = None
       for topData2 in yestoday2_top:
           if topData.code == topData2.code:
               yestory_data = topData2
               break

       printTopData(topData)
       printTopData(yestory_data,True)
       print(f"       {topData.predict.getLogInfo()}")

    print(f"前天top数据")
    for topData in yestoday2_top:
        printTopData(topData)
        print(f"       {topData.predict.getLogInfo()}")


if __name__ == "__main__":
    sw = SWImpl()
    start = datetime(2014, 5, 1)
    end = datetime(2019, 5, 1)

    patternList = [884, 709, 886, 1061, 710, 1062, 1063, 1238, 885, 535, 708, 929, 1060, 887, 1237, 1239, 711, 1236, 8630, 8629, 883,
     534, 531, 1059, 533, 1413, 532, 707, 753]
    #patternList = [884, 709, 886, 1061, 710, 1062]
    patternList = [886, 1061, 710, 885, 1060, 711, 1236, 1059]

    from earnmi_demo.strategy_demo.kbars.analysis_KPattern_skip1_predit2 import \
    Generate_Feature_KPattern_skip1_predit2, Skip1_Predict2_TraceData

    ##建立特征模型
    buildAndSaveModel(start,end,patternList)

    ##预测详情
    predictStart = datetime(2019, 5, 2)
    predictEnd = datetime(2020, 9, 20)
    #printPerdictDetail(predictStart,predictEnd,patternList)
    #printBuyAndSellPower(predictStart,predictEnd,patternList)

    #printTop5(patternList);
    pass