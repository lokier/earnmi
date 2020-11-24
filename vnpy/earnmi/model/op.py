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

class OpLogType:
    PLAIN = 0   #不处理类型
    BUY_LONG = 1 #做多买入类型
    BUY_SHORT = 2 #做空买入类型
    CROSS_SUCCESS = 3 #预测成功交割单(卖出）类型
    CROSS_FAIL = 4 #预测失败交割单类型
    ABANDON = 5 #废弃单类型

@dataclass
class OpLog:
    project_id:int
    order_id:int = None
    type:int = -1   ## 查看 OpLogType
    level:int = 0   ##0: verbse  100:debug  200：info   300:warn:  400 :error
    info:str = ""
    time:datetime = None
    price = 0.0
    extraJasonText:str = None
    def __post_init__(self):
        self.time = datetime.now()

@dataclass
class OpOrder:
    code: str
    code_name:str
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
    desc:str = ""




@dataclass
class OpOrderRealInfo:
    order_id:int
    price:float = 0.0
    update_time:datetime = None
    current_stats:str = ""



@dataclass
class OpProject:
    id:int
    status:str
    name:str
    create_time:datetime

    summary:str = ""
    url:str = ""
    update_time:datetime = None

    def __post_init__(self):
        self.update_time = self.create_time


    pass

"""
实时信息
"""
@dataclass
class OpOrederRealInfo:
    order_id:int
    id:int = None
    update_time = None
    price:float = 0.0
    current_status:str = ""

