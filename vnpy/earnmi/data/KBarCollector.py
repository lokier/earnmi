from abc import abstractmethod

from vnpy.trader.object import BarData


class TraceData(object):
    finished = False

"""
K线形态图收集器
"""
class KBarCollector:

    def onCreate(self):
        pass

    """
    开始新的股票遍历,如果需要忽略该code，返回false。
    """
    def onStart(self,code:str) ->bool:
        return True

    """
    收集bar，如果需要开始追踪这个bar，返回TraceData对象。
    """
    @abstractmethod
    def collect(self,bar:BarData)->TraceData:
        pass

    def onTrace(self,traceData:TraceData,newBar:BarData):
        pass

    def onTraceFinish(self, traceData:TraceData):
        pass

    ##未追踪完成，便终止的traceData
    def onTraceStop(self, traceData:TraceData):
        pass

    def onEnd(self,code:str):
        pass

    def onDestroy(self):
        pass