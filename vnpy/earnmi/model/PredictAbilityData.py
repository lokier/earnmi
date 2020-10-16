from dataclasses import dataclass

@dataclass
class ModelAbilityData(object):
    score_sell = 0.0
    score_buy = 0.0

    #方差
    var_sell = 0.0
    var_buy = 0.0

    #协查
    bias_sell = 0.0
    bias_buy = 0.0


    pass

@dataclass
class PredictAbilityData(object):

    count_train:int = 0
    count_test:int =0

    sell_score_train:float = 0
    buy_score_train:float = 0

    sell_score_test:float = 0
    buy_score_test:float = 0

    def __post_init__(self):
        pass