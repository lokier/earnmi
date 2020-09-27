from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData


class BarUtils:



    """
    将零散的整理bars的价格
    """
    def arrangePrice(bars:['BarData'],basePrice:float)->['BarData']:

        barList = []
        new_open_price = basePrice
        for bar in bars:
            open_price = bar.open_price
            close_price = bar.close_price
            high_price = bar.high_price
            low_price = bar.low_price
            close_price = close_price * new_open_price / open_price
            high_price = high_price * new_open_price / open_price
            low_price = low_price * new_open_price / open_price
            open_price = new_open_price

            barList.append( BarData(
                symbol=bar.symbol,
                exchange=Exchange.SSE,
                datetime=bar.datetime,
                interval=Interval.WEEKLY,
                volume=bar.volume,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                gateway_name='arrangePrice'
            ))
            new_open_price = close_price
        return barList