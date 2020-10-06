from dataclasses import dataclass

"""
 预测值数据
"""
@dataclass
class PredictData(object):
    percent:float  #涨幅
    probability:float #概率
    label:int  ##预测的标签值
    label_prob:float ##标签值概率
    level = 0 ##等级

    percent_real:float = None ##实际值，如果有的话

    def getLogInfo(self):
        sell = self
        buy = self.buy
        return f"percent:level={self.level},[{sell.percent}({sell.label}),{buy.percent}({buy.label})],prob:[{sell.probability}({sell.label_prob}),{buy.probability}({buy.label_prob})]"
