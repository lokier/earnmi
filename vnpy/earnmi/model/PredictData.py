from dataclasses import dataclass

"""
 预测值数据
"""
@dataclass
class PredictData(object):
    percent_sell:float  #涨幅
    probability:float #概率

    precent_real:float = None ##实际值，如果有的话

    pass