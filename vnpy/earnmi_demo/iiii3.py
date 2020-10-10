from datetime import datetime

from earnmi.data.SWImpl import SWImpl
from earnmi.uitl.jqSdk import jqSdk

code = "601318"  # 在datetime(2019, 2, 27, 9, 48)，到达 high_price=68.57

jq = jqSdk.get()

end_day = datetime(year=2019, month=6, day=30, hour=23)
sw = SWImpl()
__sw_code_list = sw.getSW2List()
print(f"{type(__sw_code_list) is list} ")

new_list = []
count = 0
for code in __sw_code_list:
    size = len(sw.getSW2Stocks(code))
    if size >= 10:
        count = count + size
        new_list.append(code)

print(f"{len(new_list)},size={count}")

print(f"{new_list}")

