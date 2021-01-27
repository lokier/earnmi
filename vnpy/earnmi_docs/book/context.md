#实盘运行框架


<span id="app"/>
###App与Context
Context是所有框架的运行环境对象，提供了运行时需要的一些基本支持，如:
+ 主线程执行引擎对象MainEventEngine
+ 程序目录路径，创建该程序目录路径下的子目录等。
+ 日志输出

App实现了Context,App的运行实体，并集成了一些框架的管理类，如RunnerManager

```python
app = App(".")
start = datetime(year=2021, month=1, day=2, hour=14)
app.run_backtest(start)     #回测执行
app.engine.go(3600*24*10)   #回测执行时间10天
```
   
<span id="MainEventEvent"/>
###主线程操作
主线程操作有三种，即Post事件，post方法，post定时。而主线程执行操作是由MainEventEngine引擎实现的，context只是对其方法的一个封装。

post类型|Context方法|MainEventEngine方法
--|--|--
post事件|post()、<br/>post_delay()<br/>、post_at()|postDelay()
post方法|post_event()|post_event()
post定时|post_timer()|postTimer()

<span id="post_event"/>
#####1) post event
以监听主线程引擎的天数变化事件MainEventEngine.EVNET_DAY_CHANED为例，如下：
1、定义处理event的callble方法:

```python
def onDayChangedEvent(event:str,engine:MainEventEngine):
    print(f"[{engine.now()}]: onDayChanged =>{event}")
    return False  ##表示后面不再接受该event
```
    注意:callble方法返回false时，表示后面不再接受该event事件，就等于注销callble处理该event事件。
    
2、注册和注销callbale方法:

```python
engine.register(MainEventEngine.EVNET_DAY_CHANED,onDayChangedEvent)
engine.unregister(MainEventEngine.EVNET_DAY_CHANED,onDayChangedEvent)
```

3、系统Event事件汇总

event|data|说明
--|--|--
MainEventEngine.EVNET_DAY_CHANED | engine|天数变化
MainEventEngine.EVNET_START | engine|主线程开始执行
MainEventEngine.EVNET_END | engine|主线程正常结束执行
MainEventEngine.EVNET_EXCEPTION | exception|主引擎运行异常结束执行

<span id="post_callable"/>
#####2) post callable
post操作有三种方式，post、post_delay、post_at

```python
app = App()
app.run()
def run_in_ui_thread(context:Context):
    app.log_i("run_in_ui_thread() start!") 
app.post(lambda : run_in_ui_thread(app))  ##马上提交到主线程执行
app.post_delay(10,lambda : run_in_ui_thread(app)) ##延迟提交到主线程执行
app.post_at("14:55:30",lambda : run_in_ui_thread(app)) ##指定今天时间提交到主线程执行

或者:
app.post(run_in_ui_thread,{'context':app}) ##马上提交到主线程执行
app.post_delay(10,run_in_ui_thread,{'context':app}) ##延迟提交到主线程执行
app.post_at("14:55:30",run_in_ui_thread,{'context':app} ##指定今天时间提交到主线程执行

```

<span id="post_timer"/>
#####3) post timer 定时

```python
count = 0
def do_3_time():
    global count
    count+=1
    return count <3
job = context.post_timer(10,do_3_time)
```
定时每隔10s执行do_3_time()，只执行三次do_3_time函数，超过三次do_3_time()函数将返回False，表示取消定时操作。

另外一种方式是通过返回的job对象的cancel方法取消。
```python
job.cancel()
```









