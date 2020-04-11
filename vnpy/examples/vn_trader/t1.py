import sys
from datetime import datetime, timedelta
import jqdatasdk as jq
import numpy as np
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

#
#
# if(not jq.is_auth()):
#     jq.auth('13530336157','Qwer4321') #ID是申请时所填写的手机号；Password为聚宽官网登录密码，新申请用户默认为手机号后6位
#
# if(not jq.is_auth()):
#     print('jq is not auth,exist')
#     exit()
# print('jq is auth')

code = '600519'
code_vn= code+".SSE"
code_jq= code+'.XSHG'
database_manager.clean(code_jq)
database_manager.clean(code_vn+".XSHG")
database_manager.clean(code_jq+".SSE")
