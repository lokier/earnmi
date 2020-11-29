from dataclasses import dataclass
from datetime import datetime

import numpy as np
import talib

import time
import sched

from earnmi.model.op import OpOrder

op_code = "344"
op_time =datetime.now()
op_order = OpOrder(code=op_code, code_name="dxjvkld", project_id=13,
                           create_time=op_time
                           , buy_price=34.6, sell_price=45)

import copy
op_order2 = copy.copy(op_order)
op_order.code_name = "dxjvkld"
assert op_order == op_order2

op_order2.status=-1

assert op_order != op_order2


