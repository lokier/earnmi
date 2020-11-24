from dataclasses import dataclass
from datetime import datetime,timedelta
from typing import List, Sequence

from peewee import Model, AutoField, CharField, IntegerField, DateTimeField, FloatField, TextField, BooleanField, \
    Database, SqliteDatabase, chunked


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

    id = AutoField()
    name = CharField(max_length=512,null=False)
    create_time = DateTimeField(index=True)
    update_time = DateTimeField(index=True)
    status = CharField(max_length=128)
    summary = CharField(max_length=10240,null=True)
    url = CharField(max_length=10240,null=True)


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


class OpDataBase:

    def __init__(self,db:Database):
        class OpProjectModelWrapper(OpProjectModel):
            class Meta:
                database = db
                table_name = OpProjectModel.table_name
        self.db = db
        self.projectModel = OpProjectModelWrapper
        db.connect()
        db.create_tables([OpProjectModelWrapper])

    def save_project(self,datas: List["OpProject"]):
        ds = [self.projectModel.from_data(i) for i in datas]
        dicts = [i.to_dict() for i in ds]
        with self.db.atomic():
            for c in chunked(dicts, 50):
                self.projectModel.insert_many(c).on_conflict_replace().execute()

    def clear_project(self):
        self.projectModel.delete().execute()

    def delete_project(self,id:int):
        self.projectModel.delete().where(self.projectModel.id == id).execute()

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

if __name__ == "__main__":

    db_file = SqliteDatabase("op_data.db")
    db = OpDataBase(db_file);
    now = datetime.now()

    def test_project():
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
        db.save_project([project])
        assert db.count_project() == 1
        db.save_project([project])
        db.save_project([project])
        db.save_project([project])
        assert db.count_project() == 1
        assert db.load_project(23) == None
        load_project = db.load_project(12)
        assert not load_project is None
        assert load_project.name == project.name

        project.id =13
        db.save_project([project])
        project.id =14
        db.save_project([project])
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


    test_project();














