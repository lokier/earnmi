import threading
from datetime import timedelta,datetime
from threading import Thread,Condition
from time import sleep
from typing import Any, Callable, List
import queue as Q

__all__ = [
    # Super-special typing primitives.
    'CallableEngine',
]

class _callback_item:
    def __init__(self, time: datetime, callback: Callable,args:dict):
        self.time = time
        self.callback:Callable = callback
        self.is_delete = False
        self.callback_args = args
        self.post_token = 0  ##相同时间提交的话，跟post_token来保证提交顺序。

    def __lt__(self, other):
        if(self.time < other.time):
            return True
        elif(self.time == other.time):
            return self.post_token < other.post_token
        return False



"""
    单一线程执行Callback。 
    任务执行引擎。支持实盘操作和回测环境。
    1、post：按照时间顺序、执行。
    2、postDeley：延迟操作
    3、可以监听天数变化操作。
"""
class CallableEngine:

    def __init__(self):
        self._active: bool = False
        self.is_backtest = False
        self._current_run_time:datetime = None
        self._thread: Thread = Thread(target=self._run)  ##实盘运行线程。
        self.task_queue = Q.PriorityQueue()
        self.dayChangedListeners_list = []
        self.__condition = Condition()
        self._token = 0

    def addDayChangedListener(self,callback:Callable):
        """
        监听天数变化
        callback :
        def callback(engine:CallableEinge):
        """
        self.dayChangedListeners_list.append(callback)

    def removeDayChangedListener(self,callback:Callable):
        """
        监听天数变化
        """
        self.dayChangedListeners_list.remove(callback)

    def postDelay(self,delay_second,callback:Callable,args:dict = {}):
        """
        发送deleay时间。
        Callable：方法名
        args:该方法的参数参数
        """
        time = self.now() + timedelta(seconds=delay_second)
        task = _callback_item(time=time, callback=callback,args = args)
        self.__condition.acquire()
        task.post_token = self._token + 1
        self._token =  task.post_token
        self.task_queue.put(task, block=False)
        self.__condition.notify() ##唤醒其它线程
        self.__condition.release()
        return task

    def post(self,callback:Callable,args:dict = {}):
        """
        相同时间可以保证按照post的提交顺序执行。
        """
        return self.postDelay(0,callback,args)

    def cancel(self,task:Any):
        if isinstance(task,_callback_item):
            self.__condition.acquire()
            task.is_delete = True
            task.time = self.now()
            self.__condition.release()

    def now(self) -> datetime:
        """
        当前时间。实盘环境是真实环境，回撤环境是对应回撤时间。
        """
        if self.is_backtest:
            return self._current_run_time
        else:
            return datetime.now()

    def run(self) -> None:
        """
              执行实盘操作。
         """
        self._active = True
        self.is_backtest = False
        self._current_run_time = datetime.now()
        self._thread.start()

    def run_backtest(self, start: datetime):
        """
        执行回撤。
        调用该方法之后，使用
        go方法模拟执行时间的走势。

        """
        self._active = True
        self.is_backtest = True
        self._current_run_time = start
        self._backtest_go_end_time = start
        self._thread.start()

    def stop(self) -> None:
        self._active = False
        self._thread.join()

    def go(self, second: int):
        if self._active == False:
            raise RuntimeError("not activie yet!");
        if not self.is_backtest:
            raise RuntimeError("go() method must call in backtest content!")

        # print(f"go time : +{second}s ")
        self.__condition.acquire()
        expect_go_time = self._backtest_go_end_time + timedelta(seconds=second)
        self._backtest_go_end_time = expect_go_time
        self.__condition.notify()  ##唤醒线程继续执行。
        self.__condition.release()

        ###判断当前是否在单一线程内，不在的化，要挂起线程等待到执行的时间点。
        if threading.current_thread() != self._thread:
            while expect_go_time > self._current_run_time:
                ##线程等待执行到指定的时间点。
                sleep(1)


    def _onDayChanged(self):
        """
        天数变化时间。
        """
        [callback(self) for callback in self.dayChangedListeners_list]

    def _run(self) -> None:
        """
        Get event from queue and then process it.
        """
        while self._active:
            self.__condition.acquire()
            now = self.now()
            try:
                ##获取下一个未取消的Task
                next_task:_callback_item = self.task_queue.get_nowait()
                while next_task.is_delete:
                    next_task = self.task_queue.get_nowait()
                wait_time_second = int(next_task.time.timestamp() - now.timestamp() + 0.49)
                if wait_time_second <= 0:
                    ##先释放锁，马上执行。
                    self.__condition.release()
                    self.__run_at_time(now,next_task)
                    continue
                max_wait_time = self._next_day_delay_second(now)
                wait_time_second = min(max_wait_time,wait_time_second)
                ##重新放入队列
                self.task_queue.put(next_task, block=False)
            except Q.Empty:
                wait_time_second = self._next_day_delay_second(now)
            assert  wait_time_second > 0
            ##需要延迟处理。

            if self.is_backtest:
                ##马上跳转到下一个时间点执行。
                next_time = now + timedelta(seconds=wait_time_second)

                ##回测的时间是一步一步往前的，不可能倒流的
                assert  now <= self._backtest_go_end_time

                if now == self._backtest_go_end_time:
                    ##已经只在goTime的时间末尾，挂起线程且等待go的调用。
                    #print(f"线程被挂起: {now}\n")
                    self.__condition.notify()
                    self.__condition.wait()
                else:
                    if next_time > self._backtest_go_end_time:
                        now = self._backtest_go_end_time #指定时间超过回测的go的指定范围内, 执行到
                    else:
                        now = next_time

            else:
                ##等待执行
                self.__condition.notify()
                self.__condition.wait(wait_time_second)
                now = self.now()
            self.__condition.release()

            ##时间继续往下走
            self.__run_at_time(now, None)


    def __run_at_time(self,time:datetime,task:_callback_item):
        assert self._current_run_time <= time
        old_time = self._current_run_time
        self._current_run_time = time
        if old_time.day != self._current_run_time.day:
            self._onDayChanged()
        if not task is None:
            task.callback(**task.callback_args)
        #print(f"__run_at_time:[{time}]\n")


    def _next_day_delay_second(self,d:datetime):
        next_day = datetime(year=d.year, month=d.month, day=d.day, hour=0, minute=0, second=0) + timedelta(days=1)
        return int(next_day.timestamp() - d.timestamp() + 0.49)




if __name__ == "__main__":
    ###test
    time1 = datetime(year=2019, month=6, day=30, hour=22)
    time2 = datetime(year=2019, month=6, day=30, hour=23)
    time3 = datetime(year=2019, month=7, day=2, hour=23)
    time4 = datetime(year=2019, month=7, day=3, hour=12)
    time5 = datetime(year=2019, month=7, day=3, hour=23)

    print(f"second: {datetime.now().timestamp()}" )
    print(f"second: {datetime.now().timestamp()}" )

    def callback1():
        pass

    def callback2():
        pass

    def callback3():
        pass

    def callback4():
        pass

    def callback5():
        pass

    task1= _callback_item(time=time1,callback=callback1)
    task2= _callback_item(time=time2,callback=callback2)
    task3= _callback_item(time=time3,callback=callback3)
    task4= _callback_item(time=time4,callback=callback4)
    task5= _callback_item(time=time5,callback=callback5)





    que = Q.PriorityQueue()
    que.put(task3,block=False)
    que.put(task5,block=False)
    que.put(task4,block=False)
    que.put(task1,block=False)
    que.put(task2,block=False)


    ##del callback4

    #assert que. == 5
    assert task1 == que.get_nowait()
    #assert len(que) == 4

    ##按优级别
    assert task2 == que.get_nowait()
    assert task3 == que.get_nowait()
    assert task4 == que.get_nowait()
    assert task5 == que.get_nowait()

    ##级别一样，按顺序。
    task6 = _callback_item(time=time5, callback=callback5)
    task7 = _callback_item(time=time5, callback=callback5)
    task8 = _callback_item(time=time5, callback=callback5)
    task9 = _callback_item(time=time5, callback=callback5)
    task10 = _callback_item(time=time5, callback=callback5)

    task8.post_token = 1
    que.put(task8, block=False)
    task7.post_token = 2
    que.put(task7, block=False)
    task10.post_token = 3
    que.put(task10, block=False)
    task6.post_token = 4
    que.put(task6, block=False)
    task9.post_token = 5
    que.put(task9, block=False)
    assert task8 == que.get_nowait()
    assert task7 == que.get_nowait()
    assert task10 == que.get_nowait()
    assert task6 == que.get_nowait()
    assert task9 == que.get_nowait()


    try:
        lastime =  que.get_nowait()
        assert False
    except Q.Empty:
        assert True
    pass