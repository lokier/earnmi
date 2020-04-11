from typing import Dict, Any

from vnpy.event import EventEngine, Event
from vnpy.gateway.ctp import CtpGateway
from vnpy.gateway.xtp import XtpGateway
from vnpy.trader.constant import Exchange
from vnpy.trader.engine import MainEngine
from vnpy.trader.event import EVENT_LOG
from vnpy.trader.object import SubscribeRequest


def printLog(event:Event):
    print(event.data)

def main():
    event_engine = EventEngine()
    event_engine.register(EVENT_LOG,printLog)
    main_engine = MainEngine(event_engine)

    # geteway = XtpGateway(event_engine)
    #
    # default_setting: Dict[str, Any] = {
    #     "账号": "53191000704",
    #     "密码": "vj6JDKlq",
    #     "客户号": 1,
    #     "行情地址": "120.27.164.138",
    #     "行情端口": 6002,
    #     "交易地址": "120.27.164.69",
    #     "交易端口": 6001,
    #     "行情协议": "TCP",
    #     "授权码": "b8aa7173bba3470e390d787219b2112e"
    # }
    # geteway.connect(default_setting)

    geteway = CtpGateway(event_engine)
    default_setting: Dict[str, Any] = {
        "用户名": "161239",
        "密码": "Asdf4321",
        "经纪商代码": "9999",
        "交易服务器": "218.202.237.33:10102",
        "行情服务器": "218.202.237.33:10112",
        "产品名称": "",
        "授权编码": "",
        "产品信息": ""
    }
    geteway.connect(default_setting)



main()