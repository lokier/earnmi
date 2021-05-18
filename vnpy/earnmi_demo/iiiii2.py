import pickle
from dataclasses import asdict, fields, make_dataclass,is_dataclass
from datetime import datetime

from earnmi.core.App import App
from earnmi.data.BarV5 import BarV5, BarV2
from earnmi.data.driver.StockIndexDriver import StockIndexDriver
from earnmi.data.driver.Sw2Driver import SW2Driver
from earnmi.uitl.jqSdk import jqSdk
from vnpy.trader.constant import Interval
import typing

code = "601318" #在datetime(2019, 2, 27, 9, 48)，到达 high_price=68.57

dayly_bar = BarV2(
            symbol="first_bar.symbol",
            _driver="barV2",
            datetime=datetime.now(),
            interval=Interval.DAILY,
            # volume=volume,
            # open_price=open_price,
            # high_price=high_price,
            # low_price=low_price,
            # close_price=close_price,
            # open_interest=1.0,
        )

dayly_bar.wijd = 123;

field_types = {field.name: field.type for field in fields(dayly_bar)}



print(field_types)

print(asdict(dayly_bar.extra))

Position = make_dataclass('Position', ['name', 'lat', 'lon'])
dictValue = {'name':'dcxf','lat':34.3,'lon':12.3}
pos = Position(**dictValue)
pos.ws = 23
print(f"pos:{pos.ws}")

barV2 = BarV2(symbol='344',datetime=datetime.now(),interval=Interval.DAILY)

bytesData = barV2.getExtraBlob()

barV2.loadExtraBlob(bytesData)

extra = BarV2.Extra()
print(f"BarV3.Extra():{extra.__dict__}")
extra = BarV2.Extra(**dictValue)
extra.newf = 34
print(f"BarV3.Extra(**dictValue):{extra.__dict__}")

nd=pickle.dumps(extra.__dict__)
print(f"BarV3.Extra(**dictValue) 序列化:{nd}")
print(f" 反序列化:{pickle.loads(bytes(nd))}")



print(f"dayly_bar.wijd:{dayly_bar.wijd}")
#print(f"dayly_bar.zzzz:{dayly_bar.zzz}")



