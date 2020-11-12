from earnmi.chart.Indicator import Indicator
from earnmi.data.MarketImpl import MarketImpl
from datetime import datetime, timedelta
import talib

from earnmi.model.OpOrder import OpOrderDataBase,OpOrder

code = "600155"
#code = '000300'
#801161.XSHG

dt = datetime.now() - timedelta(minutes=1)
order = OpOrder(code='test',sell_price='34',buy_price='sf',create_time=dt)

db = OpOrderDataBase("opdata.db")

db.cleanAll()
assert db.loadAtDay('test',datetime.now()) is None
assert db.count() == 0
db.save(order)
assert db.count() == 1

orederAtNow = db.loadAtDay('test',datetime.now())
assert  not orederAtNow is None
assert  orederAtNow.code =='test'

dataList = db.load(dt,dt)
order1 = dataList[0]

order2 =  db.loadById(order1.id)
assert not order2 is None
assert order1 == order2
assert  order.code == order1.code


