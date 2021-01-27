#实盘运行框架

<span id='lifecircle'/>
###Runner生命周期
![](imges/Runner生命周期.jpg)

注意:
+ onStop暂未实现
+ onStop和onError在强制杀死进程的情况是不会执行的，所以保存Runner的运行状态不应该放在这两个方法。

<span id='scheduler'/>
#####计划任务安排：
   通过Runner的RunnerScheduler对象，可以安排计划任务
* run_monthly: 每月执行
* run_weekly: 每周执行
* run_daily:每天执行。

<span id='status_save'/>
#####Runner的状态保存
待补充





