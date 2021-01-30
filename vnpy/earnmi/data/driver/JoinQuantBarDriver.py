from datetime import datetime,timedelta

from earnmi.core.Context import Context
from earnmi.data.BarDriver import BarDriver
from earnmi.data.BarStorage import BarStorage
from earnmi.model.bar import BarData
from earnmi.uitl.utils import utils
from vnpy.trader.constant import Interval
import numpy as np


class JoinQuantBarDriver(BarDriver):

    def to_jq_code(self,symbol:str)->str:
        return symbol



    def download_bars_from_jq(self, context:Context,symbol:str, start_date: datetime, end_date: datetime,interval:Interval,storage: BarStorage)->int:
        from earnmi.uitl.jqSdk import jqSdk
        jq = jqSdk.get()
        frequency = "1d"
        batch_day = 900
        if interval == Interval.DAILY:
            frequency = "1d"
            batch_day = 900
        elif interval == Interval.MINUTE:
            frequency = '1m'
            batch_day = 4
        elif interval == Interval.HOUR:
            frequency = "1h"
            batch_day = 200
        else:
            raise RuntimeError(f"unsupport interval:{interval}")

        interval = Interval.DAILY
        batch_start = start_date
        saveCount = 0
        jq_code = self.to_jq_code(symbol)
        requcent_cnt = 0
        while (batch_start.__lt__(end_date)):
            batch_end = batch_start + timedelta(days=batch_day)
            batch_end = utils.to_end_date(batch_end)
            if (batch_end.__gt__(end_date)):
                batch_end = end_date

            requcent_cnt+=1
            prices = jq.get_price(jq_code, start_date=batch_start, end_date=batch_end,
                                  fields=['open', 'close', 'high', 'low', 'volume'], frequency=frequency)
            if (prices is None):
                break
            bars = []
            lists = np.array(prices)
            for rowIndex in range(0, lists.shape[0]):
                bar = self.toBarData(symbol,prices,rowIndex,interval)
                if not bar is None:
                    bars.append(bar)
            saveCount += bars.__len__()
            storage.save_bar_data(bars)
            batch_start = batch_end  # + timedelta(days = 1)
        context.log_i("JoinQuantBarDriver",f"_download_bars_from_jq() :driver:{self.get_name()} jq_code={jq_code} start={start_date},end={end_date},requcent_cnt={requcent_cnt},count={saveCount}")
        return saveCount

    def toBarData(self,jq_code,prices,rowIndex:int,interval)->BarData:
        open_interest = 0
        row = prices.iloc[rowIndex]
        wd = prices.index[rowIndex]
        date = datetime(year=wd.year, month=wd.month, day=wd.day, hour=wd.hour, minute=wd.minute, second=wd.second);
        return BarData(
            symbol=jq_code,
            _driver=self.get_name(),
            datetime=date,
            interval=interval,
            volume=self._defualt_value(row['volume'],0.0),
            open_price=self._defualt_value(row['open'],0.0),
            high_price=self._defualt_value(row['high'],0.0),
            low_price=self._defualt_value(row['low'],0.0),
            close_price=self._defualt_value(row['close'],0.0),
            open_interest=self._defualt_value(open_interest,0.0),
        )

    def _defualt_value(self,value,deufault_value):
        if np.math.isnan(value):
            return deufault_value
        return value