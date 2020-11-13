from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from earnmi.model.Dimension import Dimension
from earnmi.model.OpOrder import OpOrder
from earnmi.model.PredictData import PredictData
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

    create_time:datetime;

    update_time:datetime =None

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
    predict: PredictData = None

    sellPrice:float =None

    isWinCheatBuy = False  ##盈利欺骗买入

    durationDay = 0  ##生成经过的交易日

    opTips:str = None ##当天操作日志

    """
    今天操作状态：
    
    
    """
    trace_status = 0

    def updateOpOrder(self,opOrder:OpOrder):
        opOrder.duration = self.durationDay
        opOrder.update_time = self.update_time
        if not self.sellPrice is None:
            opOrder.sell_price = self.sellPrice
        if not self.buyPrice is None:
            opOrder.buy_price = self.buyPrice
        assert not self.update_time is None
        opOrder.update_time = self.update_time
        opOrder.finished = self.status != PredictOrderStatus.READY and self.status!= PredictOrderStatus.HOLD


    def getStr(self):
        return f"dimen:{self.dimen.value},code:{self.code},建议卖出价:{utils.keep_3_float(self.suggestSellPrice)},买入价:{utils.keep_3_float(self.suggestBuyPrice)}," \
               f"经历天数:{self.durationDay},创建时间:{self.create_time}"

    def __post_init__(self):
        pass