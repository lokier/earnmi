from dataclasses import dataclass
from datetime import datetime

class OpOrderStatus:
    """
    Interval of bar data.
    """
    NEW = 0 ##"新建"
    HOLD = 1   ##"已经买入"
    FINISHED_EARN = 2  ## 盈利单
    FINISHED_LOSS = 3  ##亏损单
    INVALID = 4  ## "无效单"  ##即没买入也没卖出

@dataclass
class OpLog:
    pass

@dataclass
class OpOrder:
    code: str
    project_id:int
    buy_price: float  ##预测买入价
    sell_price: float
    create_time: datetime;  ##创建时间、发生时间

    id :int = None
    status: int = OpOrderStatus.NEW
    duration: int = 0
    predict_suc: bool = None  ##是否预测成功，只在完成状态有效。
    update_time: datetime = None
    source: int = 0  ##来源：0 为回测数据，1为实盘数据


    # buy_time: datetime = None   ##opLog可以获取到
    # sell_time: datetime = None
    # buy_actual_price: float = -1  # 实际买入价
    # sell_actual_price: float = -1

@dataclass
class OpOrderRealInfo:
    pass


@dataclass
class OpProject:
    id:int
    status:str
    name:str
    create_time:datetime;

    summary:str = ""
    update_time:datetime = None

    def __post_init__(self):
        self.update_time = self.create_time


    pass

"""
实时信息
"""
class OpOrederRealInfo:
    pass
