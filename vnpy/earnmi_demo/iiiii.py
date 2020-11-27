from dataclasses import dataclass

import numpy as np
import talib

import time
import sched

schedule = sched.scheduler( time.time,time.sleep)

def func2(string1):
    print(f"now excuted func is %s"%string1)
    time.sleep(5)
    schedule.enter(2, 0, func2, (1,))
    schedule.enter(2, 0, func2, (1,))
    schedule.enter(2, 0, func2, (1,))
    schedule.enter(2, 0, func2, (1,))

def func(string1):
    print(f"now excuted func is %s"%string1)
    schedule.enter(2, 0, func2, (1,))
    schedule.enter(2, 0, func2, (1,))
    schedule.enter(2, 0, func2, (1,))
    schedule.enter(2, 0, func2, (1,))



print("start")
schedule.enter(2,0,func,('d',))
schedule.enter(2,0,func,('x',))
schedule.enter(3,0,func,('z',))
schedule.enter(4,0,func,('c',))
schedule.run()

print("end")

