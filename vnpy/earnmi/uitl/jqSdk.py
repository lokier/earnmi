import jqdatasdk as jq
from datetime import datetime, timedelta

from vnpy.trader.constant import Interval

from vnpy.trader.object import BarData

from earnmi.uitl import BarUtils
from earnmi.uitl.utils import utils


class jqSdk(object):

    def __init__(self):
        self._isInit:bool = False

    def checkOk(self) ->bool:
        """
        检查服务器状态。
        :return:
        """
        if(not self._isInit):
            jq.auth('17666120227', 'Qwer4321')  # ID是申请时所填写的手机号；Password为聚宽官网登录密码，新申请用户默认为手机号后6位

        if (not jq.is_auth()):
            return False
        self._isInit = True
        return self._isInit

    def getOnMarketDate(self,code:str)->datetime:
        """
        返回上市日期
        :return:
        """
        self.checkOk()
        jqCode =  jq.normalize_code(code)
        security = jq.get_security_info(jqCode, date=None)
        return security.start_date

    """
    """
    def fethcNowDailyBars(self,codeList:[],start= None,end= None):
        self.checkOk()
        ret = {}
        if start == None or end == None:
            end = datetime.now()
            start = utils.to_start_date(end)
        print(f"start fethcNowDailyBars")
        df = jq.get_price(codeList, start_date=start, end_date=end, frequency='1d')
        print(f"end fethcNowDailyBars")
        for code in codeList:
            if len(df['close']) == 0:
                ret[code] = None
                continue
            close = df['close'][code][0]
            open = df['open'][code][0]
            high = df['high'][code][0]
            low = df['low'][code][0]
            volume = df['volume'][code][0]
            ret[code] =BarData(
                symbol=code,
                exchange=utils.getExchange(code),
                datetime=end,
                interval=Interval.DAILY,
                volume=volume,
                open_price=open,
                high_price=high,
                low_price=low,
                close_price=close,
                gateway_name='DB')
        return ret;




    def get(self) ->jq:
        self.checkOk()
        return jq

jqSdk = jqSdk()
#date = jqSdk.getOnMarketDate("000001")
#print(date)