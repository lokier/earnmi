from typing import List

from vnpy.trader.constant import Exchange

from earnmi.chart.IndexManager import IndexManager
from vnpy.trader.object import BarData


def buidildBars(size:int)->List:
    list =[]
    for i in range(size):
        bar = BarData(
            symbol="test",
            exchange=Exchange.SSE,
            datetime=None,
            gateway_name="unkonw",
            open_price=i,
            high_price=i+0.5,
            low_price=i-0.5
        )
        list.append(bar)
    return list

bar1 = BarData(
    symbol="test",
    exchange=Exchange.SSE,
    datetime=None,
    gateway_name="unkonw",
    open_price=881,
    high_price=0,
    low_price=0
)

bar2 = BarData(
    symbol="test",
    exchange=Exchange.SSE,
    datetime=None,
    gateway_name="unkonw",
    open_price=882,
    high_price=0,
    low_price=0
)

bar3 = BarData(
    symbol="test",
    exchange=Exchange.SSE,
    datetime=None,
    gateway_name="unkonw",
    open_price=883,
    high_price=0,
    low_price=0
)

bar4 = BarData(
    symbol="test",
    exchange=Exchange.SSE,
    datetime=None,
    gateway_name="unkonw",
    open_price=884,
    high_price=0,
    low_price=0
)

indexes = IndexManager(100)
assert indexes.inited == False

bars55 = buidildBars(55)
indexes.update_bar(bars55)
assert indexes.count == 55
assert indexes.inited == False
assert indexes.open_array[-1] == 54
assert indexes.open_array[-55] == 0


bars42 = buidildBars(42)
indexes.update_bar(bars42)
assert indexes.count == 97
assert indexes.inited == False
assert indexes.open_array[-1] == 41
assert indexes.open_array[-42] == 0
assert indexes.open_array[-43] == 54


indexes.update_bar(bar1)
indexes.update_bar(bar2)
assert indexes.count == 99
assert indexes.inited == False
assert indexes.open_array[-1] == 882
assert indexes.open_array[-2] == 881
assert indexes.open_array[-3] == 41

indexes.update_bar(bar3)
assert indexes.count == 100
assert indexes.inited == True
assert indexes.open_array[-1] == 883
assert indexes.open_array[-2] == 882
assert indexes.open_array[-3] == 881
assert indexes.open_array[-4] == 41
assert indexes.open_array[0] == 0
assert indexes.open_array[54] == 54
assert indexes.open_array[55] == 0


indexes.update_bar(bar4)
assert indexes.count == 101
assert indexes.inited == True
assert indexes.open_array[-1] == 884
assert indexes.open_array[-2] == 883
assert indexes.open_array[-3] == 882
assert indexes.open_array[-4] == 881
assert indexes.open_array[-5] == 41
assert indexes.open_array[0] == 1
assert indexes.open_array[53] == 54
assert indexes.open_array[54] == 0

bars60 = buidildBars(60)
indexes = IndexManager(100)
indexes.update_bar(bars60)
indexes.update_bar(bars55)
assert indexes.count == 115
assert indexes.inited == True
assert indexes.open_array[-1] == 54
assert indexes.open_array[-55] == 0
assert indexes.open_array[-56] == 59

bars255 = buidildBars(255)
indexes = IndexManager(100)
indexes.update_bar(bars255)
assert indexes.count == 255
assert indexes.inited == True
assert indexes.open_array[-1] == 254

bars100 = buidildBars(100)
indexes = IndexManager(100)
indexes.update_bar(bars100)
assert indexes.count == 100
assert indexes.inited == True
assert indexes.open_array[-1] == 99

print("test success!!")

