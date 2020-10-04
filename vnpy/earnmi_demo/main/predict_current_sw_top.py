from datetime import datetime
from typing import Sequence

import pandas as pd
import numpy as np
import sklearn
from sklearn import model_selection
from sklearn.model_selection import cross_val_score
from sklearn.datasets import make_blobs
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
import pickle


from earnmi.data.SWImpl import SWImpl
from earnmi.model.PredictData import PredictData
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
        y_buy = y[:, 0:1].astype('int')  # 取第一列

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
        classifier = self.getClassifier()

        predic_y_proba = classifier.predict_proba(x)
        size = len(x)
        predict_data_list = []
        for i in range(0, size):
            y_proba_list = predic_y_proba[i]  ##预测值
            percent,total_probal = self.__compute_prdict_sell(y_proba_list,self.labels_y_sell,True)
            predictData = PredictData(percent=percent,probability=total_probal)
            predictData.precent_real = y_sell[i]
            predict_data_list.append(predictData)

        return predict_data_list

    def __compute_prdict_sell(self,y_proba_list:[],y_label:[],isSell=True):
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

        # percent = self.labels_y[index]
        percent = percent_2 * probal_2 / (max_proba + probal_2) + y_label[index] * max_proba / (
                    max_proba + probal_2)
        return percent,total_probal

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



if __name__ == "__main__":
    sw = SWImpl()
    start = datetime(2014, 5, 1)
    end = datetime(2020, 4, 17)
    patternList = [535, 359, 1239, 1415, 1072, 712, 1240, 888, 2823, 706, 1414, 1064]


    from earnmi_demo.strategy_demo.kbars.analysis_KPattern_skip1_predit2 import \
        Generate_Feature_KPattern_skip1_predit2

    ##建立特征模型
   # buildAndSaveModel(start,end,patternList)



    predictStart = datetime(2020, 4, 18)
    predictEnd = datetime.now()
    #patternList = [535]
    total_count = 0
    fail_count = 0
    total_count1= 0
    fail_count1 = 0
    total_count2 = 0
    fail_count2 = 0
    for kPattern in patternList:
        generateTrainData = Generate_Feature_KPattern_skip1_predit2(kPatters=[kPattern])
        sw.collect(predictStart, predictEnd, generateTrainData)


        filleName = f"models/predict_sw_top_k_{kPattern}.m"

        model = PredictModel()
        model.loadFromFile(filleName)

        model2 = PredictModel2()
        model2.loadFromFile(filleName)


        traceDatas = generateTrainData.traceDatas


        def compute_result(model,feature):

            predict = model.predict(feature)[0]

            close_price = traceData.occurBar.close_price
            predict_price = close_price * (1 + predict.percent / 100.0)

            buy_price = traceData.skipBar.close_price

            profile_pct = (predict_price - buy_price) / close_price

            deal = False
            sucess = False
            sell_day = -1
            if profile_pct > 0.01 and predict.probability > 0.7:
                deal = True
                for i in range(0, len(traceData.predictBars)):
                    bar: BarData = traceData.predictBars[i]
                    if predict_price < bar.high_price:
                        sell_day = i
                        break

                can_sell = sell_day != -1
                if can_sell:
                    sucess = True
                    #print(f"SUC  : profile_pct = {profile_pct},sell_day = {sell_day},prob={predict1.probability}")
                else:
                    profile_pct = (traceData.predictBars[-1].close_price - buy_price) / close_price
            return deal,sucess,sell_day,profile_pct,predict.probability

        for traceData in traceDatas:
            feature1 = generateTrainData.generateData([traceData])
            feature2 = generateTrainData.generateData([traceData])

            deal, sucess, sell_day, profile_pct,probability = compute_result(model,feature1)
            deal2, sucess2, sell_day2, profile_pct2,probability2 = compute_result(model2,feature2)

            if deal == True and deal2 == True:
                total_count +=1
                if sucess != True or sucess2 !=True:
                    fail_count +=1

                print(f"sucess:{sucess},profile_pct = {profile_pct},sell_day = {sell_day},prob={probability}")
                print(f"sucess:{sucess2},profile_pct = {profile_pct2},sell_day = {sell_day2},prob={probability2}\n")

            if deal == True:
                total_count1 +=1
                if sucess != True :
                    fail_count1 +=1
            if deal2 == True:
                total_count2 += 1
                if sucess2 != True:
                    fail_count2 += 1

    sucess_rate = 100 * ( 1 - (fail_count)/total_count)
    sucess_rate1 = 100 * ( 1 - (fail_count1)/total_count1)
    sucess_rate2 = 100 * ( 1 - (fail_count2)/total_count2)

    print(f"total count:{total_count}, sucess_rate:%.2f%%" % (sucess_rate))
    print(f"rf count:{total_count1}, sucess_rate:%.2f%%" % (sucess_rate1))
    print(f"svm count:{total_count2}, sucess_rate:%.2f%%" % (sucess_rate2))

    pass