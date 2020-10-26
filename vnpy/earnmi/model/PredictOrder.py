from dataclasses import dataclass
from enum import Enum
from earnmi.model.Dimension import Dimension
from earnmi.uitl.utils import utils


class PredictOrderStatus(Enum):
    READY = "ready"  #准备交易
    HOLD = "hold"   #持筹码
    FAIL = "fail"   #预测成功单
    SUC = "suc"   #预测失败单
    ABANDON = "abandon"  #没有操作的废弃单

@dataclass
class PredictOrder(object):
    """
        维度值
    """
    dimen: Dimension

    code:str

    name:str

    """
    1为买入做多单：
    2为买入做空单：
    """
    type:int = None

    status:PredictOrderStatus = PredictOrderStatus.READY

    """
    多空力量比例
    """
    power_rate:float = 0.0

    #最佳卖出价
    suggestSellPrice:float = 0.0

    #最佳买入价
    suggestBuyPrice:float = 0.0

    """
    """
    buyPrice:float = None


    sellPrice:float =None

    durationDay = 0

    def getStr(self):
        current_price = "未知"
        return f"dimen:{self.dimen.value},code:{self.code},建议卖出价:{utils.keep_3_float(self.suggestSellPrice)},止损价:{utils.keep_3_float(self.suggestBuyPrice)}," \
               f"经历天数:{self.durationDay}"

    def __post_init__(self):
        pass