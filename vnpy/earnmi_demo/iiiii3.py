import json

from playhouse.shortcuts import dict_to_model, model_to_dict

from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from datetime import datetime, timedelta
import talib

from earnmi.model.OpOrder2 import OpOrderDataBase, OpOrder2, OpLog

code = "600155"
#code = '000300'
#801161.XSHG

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self,obj)

dt = datetime.now() - timedelta(minutes=1)
opLog1 = OpLog(time=dt,info="test1",type = 1)
opLog2 = OpLog(time=datetime.now(), info="test1",type = 1)

opList = [opLog1.to_dict(),opLog2.to_dict()]


j = json.dumps(opLog1.to_dict(),cls=DateEncoder)
print(j)  # {"id": "007", "name": "007", "age": 28, "sex": "male", "phone": "13000000000", "email": "123@qq.com"}

j = json.dumps(obj=opList,cls=DateEncoder)
print(j)  # {"id": "007", "name": "007", "age": 28, "sex": "male", "phone": "13000000000", "email": "123@qq.com"}

dict = json.loads(s=j)
print(dict)

# db = OpOrderDataBase("opdata.db")
# db.cleanAll()
# db.save(order)



