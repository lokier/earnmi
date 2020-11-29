from dataclasses import dataclass
from datetime import datetime,timedelta
from typing import List, Sequence

from peewee import Model, AutoField, CharField, IntegerField, DateTimeField, FloatField, TextField, BooleanField, \
    Database, SqliteDatabase, chunked

__all__ = [
    # Super-special typing primitives.
    'OpOrderStatus',
    'OpLogType',
    'OpLogLevel',
    'OpLog',
    'OpOrder',
    'OpProject',
    'OpDataBase', ###数据库
]

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
class OpLogLevel:
    VERBASE = 0   #不处理类型
    DEBUG = 100 #做多买入类型
    INFO = 200 #做空买入类型
    WARN = 300 #预测成功交割单(卖出）类型
    ERROR = 400 #预测失败交割单类型

@dataclass
class OpLog:
    project_id:int = None
    id:int = None
    order_id:int = None
    type:int = OpLogType.PLAIN   ## 查看 OpLogType
    level:int = OpLogLevel.VERBASE   ## 查看 OpLogLevel
    time:datetime = None
    price:float = None
    info:str = ""
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
    dimen:str = None
    status: int = OpOrderStatus.NEW
    duration: int = 0
    predict_suc: bool = None  ##是否预测成功，只在完成状态有效。
    update_time: datetime = None
    source: int = 0  ##来源：0 为回测数据，1为实盘数据
    desc:str = ""
    buy_price_real:float = None  ##实际买入
    sell_price_real:float = None ##实际卖出
    current_price:float = 0.0  ##当前价格

    current_trade_time = None  ##当前交易的时间

    def __post_init__(self):
        self.update_time = self.create_time




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
    project_id:int
    id:int = None
    update_time = None
    price:float = 0.0
    current_status:str = ""

"""
orm model
"""

class OpBaseModel(Model):

    def to_dict(self):
        return self.__data__

    @staticmethod
    def from_data(data):
        pass

    def to_data(self,db_data):
        pass



class OpProjectModel(OpBaseModel):
    table_name = 'op_project'
    id = AutoField(null=False)
    name = CharField(max_length=512,null=False)
    create_time = DateTimeField(index=True)
    update_time = DateTimeField(index=True)
    status = CharField(max_length=128)
    summary = CharField(max_length=2048,null=True)
    url = CharField(max_length=2048,null=True)

    @staticmethod
    def from_data(data: OpProject):
        db_data = OpProjectModel()
        db_data.id = data.id
        db_data.name = data.name
        db_data.create_time = data.create_time
        db_data.status = data.status
        db_data.url = data.url
        db_data.update_time = data.update_time
        return db_data

    def to_data(self):
        data = OpProject(
            id=self.id,
            status=self.status,
            create_time=self.create_time,
            name=self.name,
        )
        data.summary = self.summary
        data.url = self.url
        data.update_time = self.update_time
        return data

class OpOrderModel(OpBaseModel):
    table_name = 'op_order'
    id = AutoField()
    code = CharField(max_length=48,null=False)
    code_name = CharField(max_length=125,null=False)
    dimen = CharField(max_length=256,null=False,index=True)
    project_id = IntegerField(null=False)
    buy_price = FloatField()
    sell_price= FloatField()
    buy_price_real = FloatField(null=True)
    sell_price_real = FloatField(null=True)
    current_price = FloatField()
    create_time= DateTimeField()
    status = IntegerField()
    duration = IntegerField()
    predict_suc = BooleanField(null=True)
    update_time = DateTimeField()
    source = IntegerField()
    desc = CharField(max_length=2048,null=True)

    current_trade_time = DateTimeField(null=True)

    @staticmethod
    def from_data(data: OpOrder):
        db_data = OpOrderModel()
        db_data.id = data.id
        db_data.code = data.code
        db_data.dimen = data.dimen
        db_data.code_name = data.code_name
        db_data.project_id = data.project_id
        db_data.buy_price = data.buy_price
        db_data.sell_price = data.sell_price
        db_data.create_time = data.create_time
        db_data.status = data.status
        db_data.duration = data.duration
        db_data.predict_suc = data.predict_suc
        db_data.update_time = data.update_time
        db_data.source = data.source
        db_data.desc = data.desc
        db_data.buy_price_real = data.buy_price_real
        db_data.sell_price_real = data.sell_price_real
        db_data.current_price = data.current_price
        db_data.current_trade_time = data.current_trade_time

        return db_data

    def to_data(self):
        data = OpOrder(
            code=self.code,
            code_name=self.code_name,
            project_id=self.project_id,
            buy_price=self.buy_price,
            sell_price=self.sell_price,
            create_time=self.create_time,
        )
        data.id = self.id
        data.dimen = self.dimen
        data.status = self.status
        data.duration = self.duration
        data.predict_suc = self.predict_suc
        data.update_time = self.update_time
        data.source = self.source
        data.desc = self.desc
        data.buy_price_real = self.buy_price_real
        data.sell_price_real = self.sell_price_real
        data.current_price = self.current_price
        data.current_trade_time = self.current_trade_time

        return data




class OpLogModel(OpBaseModel):
    table_name = 'op_log'
    id = AutoField()
    order_id = IntegerField(null=True)
    project_id = IntegerField(null=False)
    type = IntegerField(null=True)
    level = IntegerField(null=False,default=0)
    time = DateTimeField()
    price = FloatField(null=True)
    info = CharField(max_length=2048,null=True)
    extraJasonText = CharField(max_length=2048,null=True)

    @staticmethod
    def from_data(data: OpLog):
        db_data = OpLogModel()
        db_data.id = data.id
        db_data.order_id = data.order_id
        db_data.project_id = data.project_id
        db_data.type = data.type
        db_data.level = data.level
        db_data.time = data.time
        db_data.price = data.price
        db_data.info = data.info
        db_data.extraJasonText = data.extraJasonText
        return db_data

    def to_data(self):
        data = OpLog(
            order_id=self.order_id,
        )
        data.id = self.id
        data.project_id = self.project_id
        data.type = self.type
        data.level = self.level
        data.time = self.time
        data.price = self.price
        data.info = self.info
        data.extraJasonText = self.extraJasonText
        return data


class OpDataBase:

    def __init__(self,db:Database):
        class OpProjectModelWrapper(OpProjectModel):
            class Meta:
                database = db
                table_name = OpProjectModel.table_name
        class OpOrderModelWrapper(OpOrderModel):
            class Meta:
                database = db
                table_name = OpOrderModel.table_name
        class OpLogModelWrapper(OpLogModel):
            class Meta:
                database = db
                table_name = OpLogModel.table_name

        self.db = db
        self.projectModel = OpProjectModelWrapper
        self.logModel = OpLogModelWrapper
        self.orderModel = OpOrderModelWrapper
        if db.is_closed():
            db.connect()
        self.table_list = [OpProjectModelWrapper,OpLogModelWrapper,OpOrderModelWrapper]
        db.create_tables(self.table_list)

    def clearAll(self):
        self.db.drop_tables(self.table_list)
        self.db.create_tables(self.table_list)

    def save_projects(self, datas: List["OpProject"]):
        ds = [self.projectModel.from_data(i) for i in datas]
        dicts = [i.to_dict() for i in ds]
        with self.db.atomic():
            for c in chunked(dicts, 50):
                self.projectModel.insert_many(c).on_conflict_replace().execute()



    def clear_log(self):
        self.logModel.delete().execute()

    def delete_project(self,id:int):
        self.projectModel.delete().where(self.projectModel.id == id).execute()
        self.orderModel.delete().where(self.orderModel.project_id == id).execute()
        self.logModel.delete().where(self.logModel.project_id == id).execute()


    def count_project(self):
        return self.projectModel.select().count()

    def load_project(self,id)->OpProject:
        s = (
            self.projectModel.select()
                .where(self.projectModel.id == id)
        )
        if s:
            data = [db_bar.to_data() for db_bar in s]
            if len(data) > 0:
                assert len(data) == 1
                return data[0]
        return None

    def load_projects(self,offset:int,count:int) -> Sequence["OpProject"]:
        s = (
            self.projectModel.select()
                .offset(offset)
                #.order_by(self.dao.create_time.desc(), self.dao.update_time.desc())
                .limit(count)
        )
        data = [db_bar.to_data() for db_bar in s]
        return data

    def load_logs(self,project_id, order_id)-> Sequence["OpLog"]:
        s = (
            self.logModel.select()
                .where(
                (self.logModel.project_id == project_id)
                &
                (self.logModel.order_id == order_id)
            )
        )
        data = [db_bar.to_data() for db_bar in s]
        return data




    def save_log(self, log:OpLog):
        self.save_logs([log])

    def save_logs(self, datas: List["OpLog"]):
        ds = [self.logModel.from_data(i) for i in datas]
        dicts = [i.to_dict() for i in ds]
        with self.db.atomic():
            for c in chunked(dicts, 50):
                self.logModel.insert_many(c).on_conflict_replace().execute()

    def load_order_by_time(self, project_id:int,code:str, create_time:datetime)->OpOrder:
        s = (
            self.orderModel.select()
                .where(
                (self.orderModel.project_id == project_id)
                &
                (self.orderModel.code == code)
                &
                (self.orderModel.create_time == create_time)
            )
        )
        if s:
            data = [db_bar.to_data() for db_bar in s]
            if len(data) > 0:
                assert len(data) == 1
                return data[0]
        return None

    def load_order_all(self,project_id:int)-> Sequence["OpOrder"]:
        s = (
            self.orderModel.select()
                .where(self.orderModel.project_id == project_id)
        )
        data = [db_bar.to_data() for db_bar in s]
        return data


    def save_order(self, op_order):
        ds = [self.orderModel.from_data(i) for i in [op_order]]
        dicts = [i.to_dict() for i in ds]
        with self.db.atomic():
            for c in chunked(dicts, 50):
                self.orderModel.insert_many(c).on_conflict_replace().execute()


if __name__ == "__main__":

    db_file = SqliteDatabase("op_data.db")
    db = OpDataBase(db_file);
    now = datetime.now()

    def test():
        dt = now - timedelta(minutes=1)
        project = OpProject(
            id=12,
            status="unkonw",
            create_time=dt,
            name="测试",
        )
        project.summary = "summary1"
        project.url = "url"
        db.clear_project()
        assert db.count_project() == 0
        db.save_projects([project])
        assert db.count_project() == 1
        db.save_projects([project])
        db.save_projects([project])
        db.save_projects([project])
        assert db.count_project() == 1
        assert db.load_project(23) == None
        load_project = db.load_project(12)
        assert not load_project is None
        assert load_project.name == project.name

        project.id =13
        db.save_projects([project])
        project.id =14
        db.save_projects([project])
        assert db.count_project() == 3
        pList = db.load_projects(0, 1)
        assert len(pList) == 1
        pList = db.load_projects(0, 2)
        assert len(pList) == 2
        pList = db.load_projects(0, 6)
        assert len(pList) == 3
        pList = db.load_projects(2, 6)
        assert len(pList) == 1
        pList = db.load_projects(3, 6)
        assert len(pList) == 0
        db.delete_project(14)
        db.delete_project(13)

        assert db.count_project() == 1

        op_code = "343422"
        op_time = dt
        op_order_load = db.load_order_by_time(13,op_code, op_time)
        assert op_order_load is None

        op_order = OpOrder(code=op_code, code_name="dxjvkld", project_id=13,
                           create_time=op_time
                           , buy_price=34.6, sell_price=45)
        op_order.dimen = f"opName"
        op_order.status = "新的"
        op_order.duration = 3
        op_order.current_trade_time = datetime.now()
        db.save_order(op_order)
        op_order_load = db.load_order_by_time(13,op_code, op_time)

        assert not op_order_load is None
        assert op_order_load.dimen == op_order.dimen
        assert op_order_load.code == op_code
        assert op_order_load.create_time == op_time
        assert op_order_load.duration == op_order.duration
        assert op_order_load.current_trade_time == op_order.current_trade_time


        db.clear_log()
        oplog1 = OpLog(project_id=3,order_id=4,info="1")
        oplog2 = OpLog(project_id=3,order_id=3,info="2")
        oplog3 = OpLog(project_id=4,order_id=4,info="3")
        oplog4 = OpLog(project_id=3,order_id=6,info="4")
        oplog5 = OpLog(project_id=3,order_id=3,info="5")
        db.save_logs([oplog1,oplog2,oplog3,oplog4,oplog5])

        logs = db.load_logs(3,3)
        assert len(logs) ==2





    test();














