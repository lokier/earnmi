import jqdatasdk as jq
from datetime import datetime, timedelta

class jqSdk(object):

    def __init__(self):
        self._isInit:bool = False

    def checkOk(self) ->bool:
        """
        检查服务器状态。
        :return:
        """
        if(not self._isInit):
            jq.auth('13530336157', 'Qwer4321')  # ID是申请时所填写的手机号；Password为聚宽官网登录密码，新申请用户默认为手机号后6位

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

    def get(self):
        self.checkOk()
        return jq

jqSdk = jqSdk()
#date = jqSdk.getOnMarketDate("000001")
#print(date)