from datetime import datetime

from earnmi.uitl.jqSdk import jqSdk

code = "601318" #在datetime(2019, 2, 27, 9, 48)，到达 high_price=68.57

jq = jqSdk.get()

end_day = datetime(year=2019, month=6, day=30,hour=23)

jq.finance.SW1_DAILY_PRICE

df =jq.get_bars(jq.normalize_code(code), 3, unit='1M',fields=['date','open','high','low','close','volume'],include_now=True,end_dt=end_day)

print(df)