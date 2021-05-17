
'''
单个股票的买入卖出策略类。 计算买入点和卖出点的 。
缺点：
+ 可能持有周期太长，没有止损点操作，对于买入点产出之后的中途走势异样没有修正。
+ 卖出点没有细分：止损点和止盈点，比较粗糙。

'''
import math

from earnmi.chart.Indicator import Indicator
from earnmi.core.analysis.FloatRange import FloatRange
from earnmi.data.BarSoruce import BarSource, BarSource
from earnmi.data.BarTrader import SimpleTrader


def __parse_order_list(order_list):
    ##计算涨幅比例
    pct_list = []
    hold_day_list = []
    total_hold_day = 0.0
    total_pct = 0.0
    total_size = len(order_list)
    avg_pct = 0.0
    avg_hold_day = 0.0

    pct_probal_dist = [0.0,0.0,0.0]  ###[<-1%的概率，（-1,1）的概率，>1的概率]
    pct_probal_dist_desc = "" ##持有天数分布描述
    hold_day_dist_desc = "" ##持有天数分布描述

    for order in order_list:
        pct = 100 * (order.sell_price - order.buy_price) / order.buy_price
        pct_list.append(pct)
        total_pct += pct
        total_hold_day += order.hold_day
        hold_day_list.append(order.hold_day)
    pct_range = FloatRange(-1, 1, 1)  # 生成浮点值范围区间对象
    hold_day_rang = FloatRange(1, 18, 3)
    if total_size > 0:
        avg_pct = total_pct / total_size
        avg_hold_day = total_hold_day / total_size
        _pct_dist = pct_range.calculate_distribute(pct_list).items(reverse=None)

        assert len(_pct_dist) ==3
        assert _pct_dist[0].right ==-1
        assert _pct_dist[1].left ==-1 and _pct_dist[1].right==1
        assert _pct_dist[2].left ==1
        pct_probal_dist[0] = _pct_dist[0].probal * 100
        pct_probal_dist[1] = _pct_dist[1].probal * 100
        pct_probal_dist[2] = _pct_dist[2].probal * 100
        pct_probal_dist_desc = pct_range.calculate_distribute(pct_list).toStr()
        hold_day_dist_desc = hold_day_rang.calculate_distribute(hold_day_list).toStr()
        # print(f"    交易总数:0")
        # print(f"    交易总数:{total_size}, 平均涨幅:%.2f, 平均持有天数:%.2f" % (total_pct / total_size, total_hold_day / total_size))
        # print(f"    涨幅分布情况:{pct_range.calculate_distribute(pct_list).toStr()}")
        # print(f"    持有天数分布情况:{hold_day_rang.calculate_distribute(hold_day_list).toStr()}")

    ret =  [total_size,avg_pct,avg_hold_day,pct_probal_dist[0],pct_probal_dist[1],pct_probal_dist[2],pct_probal_dist_desc,hold_day_dist_desc]
    print(f"{ret}")
    return ret

class BuyOrSellStrategy:

    def onBegin(self,code:str):
        self.indicator = Indicator(40)

    def onEnd(self,code:str):
        pass
    '''
     当天的交易情况： true表示买入点，false表示卖出点，None表示不操作。
    '''
    def is_buy_or_sell(self,bar:BarSource)->bool:
        return None

def analysis_BuyOrSellStrategy(source: BarSource, strategy: BuyOrSellStrategy):
    trader = SimpleTrader()  ##计算正向收益
    trader_reverse = SimpleTrader()  ##计算反向收益

    for symbol,bars in source.itemsSequence():
        code = bars[0].symbol
        print(f"start:{code}")
        strategy.onBegin(code)
        for bar in bars:
            _buy_or_sell = strategy.is_buy_or_sell(bar)
            ###是否持有
            if not _buy_or_sell is None:
                if _buy_or_sell:
                    ## 买入
                    if not trader.hasBuy(bar.symbol):
                        ##正向买入
                        the_buy_price = bar.close_price   # 上一个交易日的收盘价作为买入价
                        trader.buy(bar.symbol, the_buy_price, bar.datetime)
                    if trader_reverse.hasBuy(bar.symbol):
                        ##反向卖出
                        sell_Price = bars[-1].close_price  # 上一个交易日的收盘价作为买如价
                        trader_reverse.sell(bar.symbol, sell_Price, bar.datetime)
                else:
                    ## 卖出
                    if trader.hasBuy(bar.symbol):
                        ##正向卖出
                        sell_Price = bars[-1].close_price   # 上一个交易日的收盘价作为买如价
                        trader.sell(bar.symbol, sell_Price, bar.datetime)
                    if not trader_reverse.hasBuy(bar.symbol):
                        ##反向买入
                        the_buy_price = bar.close_price  # 上一个交易日的收盘价作为买入价
                        trader_reverse.buy(bar.symbol, the_buy_price, bar.datetime)
            trader.watch(bar.datetime)
            trader_reverse.watch(bar.datetime)
        trader.resetWatch()
        trader_reverse.resetWatch()
        strategy.onEnd(code)

    print("-------正向操作-----------")
    ret1 = __parse_order_list(trader.getOrederList())

    print("-------反向操作-----------")
    ret2 = __parse_order_list(trader_reverse.getOrederList())

    def tofloat(v):
        return f"%.2f" % v

    v = (ret1[3] - ret2[5])* (ret1[3] - ret2[5]) + (ret1[4] - ret2[4]) * (ret1[4] - ret2[4]) + (ret1[4] - ret2[4]) * (ret1[4] - ret2[4])
    v = math.sqrt(v)

    html = "<table>"
    html = html +'\n<tr><th>策略名</th> <td colspan="6">     </td></tr>'
    html = html +'\n<tr><th>策略说明</th> <td colspan="6">     </td></tr>'

    html = html + (
        ' \n <tr><th rowspan="2"></th>  <th rowspan="2">交易数</th> <th rowspan="2" >均收益</th> <th rowspan="2">均天数</th> <th colspan="3">收益分布概率</th> </tr>')
    html = html + (' \n <tr><th>小于-1%</th> <th> [-1,1]左右</th> <th>大于1%</th> </tr>')
    html = html + (
        f"\n <tr><th>正向</th>  <td>{ret1[0]}</td> <td>{tofloat(ret1[1])}%</td> <td>{tofloat(ret1[2])}</td> <td>{tofloat(ret1[3])}</td> <td>{tofloat(ret1[4])}</td> <td>{tofloat(ret1[5])}</td> </tr>")
    html = html + (
        f"\n <tr><th>反向</th>  <td>{ret2[0]}</td> <td>{tofloat(ret2[1])}%</td> <td>{tofloat(ret2[2])}</td> <td>{tofloat(ret2[3])}</td> <td>{tofloat(ret2[4])}</td> <td>{tofloat(ret2[5])}</td> </tr>")
    html = html + (f'\n <tr><td>反向值</td>  <td >{tofloat(v)}</td>  <th>天数分布</th>  <td colspan="4">{ret1[6]}</td></tr>')
    html = html + ("  \n</table>")


    print(f"html表格：\n{html}")