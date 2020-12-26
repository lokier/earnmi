
##数据库设计

###OP_PROJECT

###OpLog：操作日志

name|类型|备注
:--|:--|:--
id|int|
project_id|int|
order_id|int|
type|int|查看OpLogType.PLAIN
level|int|查看OpLogLevel
time|datetime |
price|float|
info|str|
extraJasonText|str

+ OpLogType:
    + PLAIN = 0   #不处理类型
    + BUY_LONG = 1 #做多买入类型
    + BUY_SHORT = 2 #做空买入类型
    + CROSS_SUCCESS = 3 #预测成功交割单(卖出）类型
    + CROSS_FAIL = 4 #预测失败交割单类型
    + ABANDON = 5 #废弃单类型
+ OpLogLevel:
    + VERBASE = 0   #不处理类型
    + DEBUG = 100 #做多买入类型
    + INFO = 200 #做空买入类型
    + WARN = 300 #预测成功交割单(卖出）类型
    + ERROR = 400 #预测失败交割单类型

###OpOrder:操作单

name|类型|备注
:--|:--|:--
code|str|
code_name|str|
project_id|int|
buy_price|float|预测买入价
sell_price|float
create_time|datetime|创建时间、发生时间
id|int|
dimen|str|
status|int|查看OpOrderStatus
duration|int|
predict_suc|bool|是否预测成功，只在完成状态有效。
update_time|datetime|
source|int|来源：0 为回测数据，1为实盘数据
desc|str|
buy_price_real|float| 实际买入
sell_price_real|float|实际卖出

OpOrderStatus:
+ NEW = 0 ##"新建"
+ HOLD = 1   ##"已经买入"
+ FINISHED_EARN = 2  ## 盈利单
+ FINISHED_LOSS = 3  ##亏损单
+ INVALID = 4  ## "无效单"  ##即没买入也没卖出

###OpProject: 操作工程

name|类型|备注
:--|:--|:--
id|int|
status|str|
name|str|
create_time|datetime|
summary|str|
url|str|
update_time|datetime|


####OpStatistic: 操作数据统计
type|int| 主键，0:最近1个月，1：最近3个月，2:最近6个月，3：最近1年
project_id|int|
predict_suc_count|int|预测成功总数
count|int|产出操作单的总数
dealCount|int|产出交易的个数
earnCount|int|盈利总数
predict_suc_deal_count|int|预测成功总数（不含无效单)
totalPct|float|盈利情况
totalEarnPct|float|盈利情况(不含亏损单)
maxEarnPct|float|最大盈利单
maxLossPct|float|最大亏损单
start_time|datetime|统计开始时间

如何计算