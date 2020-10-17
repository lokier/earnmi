from dataclasses import dataclass

@dataclass
class ModelAbilityData(object):
    count = 0
    scoreSell = 0.0
    scoreBuy = 0.0

    #正偏差
    biasSellWin = 0.0
    biasBuyWin = 0.0

    #负偏差
    biasSellLoss = 0.0
    biasBuyLoss = 0.0

    pass

@dataclass
class PredictAbilityData(object):

    trainData:ModelAbilityData = None
    testData:ModelAbilityData = None

    def __post_init__(self):
        pass