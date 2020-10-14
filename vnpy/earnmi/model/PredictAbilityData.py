from dataclasses import dataclass


@dataclass
class PredictAbilityData(object):

    count_train:int = 0
    count_test:int =0

    sell_score_train:float = 0
    buy_score_train:float = 0

    sell_score_test:float = 0
    buy_score_test:float = 0