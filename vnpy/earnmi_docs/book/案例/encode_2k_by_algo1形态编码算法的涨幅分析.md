#encode_2k_by_algo1形态编码算法的涨幅分析

###背景
+ 通过分叉线分析k线形态的看空或者看多特性
+ 通过calc_op_score得分值来分析k线形态的看空或者看多操作性

在使用Pattern.encode_2k_by_algo1()识别出来的2日k线形态中，可以用anaylsisPatternCoverity函数得出75个有意义的k线形态值，它们是：

    [206671, 265649, 213961, 265639, 265720, 206580, 324769, 81283, 265629, 29443, 206590, 206337, 199381, 265619, 259159, 265963, 265376, 
    442867, 14944, 265710, 258430, 265719, 280300, 206428, 265801, 265467, 81040, 36814, 21991, 251140, 265477, 88330, 88492, 95863, 265497, 265740, 265711, 
    265487, 88482, 199138, 199300, 265638, 88320, 206347, 88573, 22234, 206681, 258420, 279571, 265730, 273010, 266449, 205942, 265386, 265721, 272281, 265729, 265406,
    273020, 192091, 265457, 273000, 251869, 88563, 258187, 103153, 221251, 258440, 73993, 264991, 258349, 265700, 265659, 272919, 272929]

以下就对这75个形态值做涨幅分析。


统计k线形态之后第k日的涨幅情况，找出50%分叉线

+ 1日涨幅，涨幅情况以收盘价为准 
+ 3日涨幅, 涨幅情况以最后两日收盘价均价为准
+ 7日涨幅，涨幅情况以最后3天收盘均价为准
+ 14日涨幅，涨幅情况以最后5天收盘均价为准

如果1，3，7，14的分叉线递增关系，说明K线形态是一个很明显的看多或看空的形态。

>什么时分叉线？
>分叉线就是指FloatRange.calc_avg_line()值，计算一串涨幅值得中间值，该中间值是一个分叉线，把小于和大于这个中间值得分布情况各占一半50%


###1 收集k线形态对应得涨幅
通过CollectHandler方式去收集CollectData，其中:
+ CollectData.dimen_value : 形态编码值
+ CollectData.occur_bars  : 2日k线形态
+ CollectData.unkown_bars : 准备收集得14日涨幅情况基本bar
如下,通过继承CollectHandler专门收集上面对应得数据。
```python
class Pattern_2k_by_algo1_handler(CollectHandler):
    def __init__(self):
        self.pattern_values = [206671, 265649, 213961, 265639, 265720, 206580, 324769, 81283, 265629, 29443, 206590,
                                 206337, 199381, 265619, 259159, 265963, 265376,
                                 442867, 14944, 265710, 258430, 265719, 280300, 206428, 265801, 265467, 81040, 36814,
                                 21991, 251140, 265477, 88330, 88492, 95863, 265497, 265740, 265711,
                                 265487, 88482, 199138, 199300, 265638, 88320, 206347, 88573, 22234, 206681, 258420,
                                 279571, 265730, 273010, 266449, 205942, 265386, 265721, 272281, 265729, 265406,
                                 273020, 192091, 265457, 273000, 251869, 88563, 258187, 103153, 221251, 258440, 73993,
                                 264991, 258349, 265700, 265659, 272919, 272929]

    def onTraceStart(self, symbol: str):
        self.bar_list = []
        print(f"onTraceStart:{symbol}")
        pass

    def onTraceBar(self, bar: BarData):
        if not BarUtils.isOpen(bar):
            self.bar_list = []
            return None
        self.bar_list.append(bar)
        pattern_vaule = KPattern.encode_2k_by_algo1(self.bar_list)
        if self.pattern_values.__contains__(pattern_vaule):
            ##产生一个收集数据
            return CollectData(dimen_value=pattern_vaule,occur_bars=self.bar_list[-3:])
        return None

    def onCollecting(self, data: CollectData, bar: BarData):
        data.unkown_bars.append(bar)
        cur_size = len(data.unkown_bars)
        if cur_size>= 14:
            data.setFinished() ##收集到有14天的数据就算收集完成。
```

###2 计算各k日形态对应得分叉线=>分析看空、看多特性。

```python
app = App()
start = datetime(year=2018,month=1,day=6)
end = datetime(year=2021,month=1,day=6)
drvier2 = ZZ500StockDriver()
bar_source = app.getBarManager().createBarSoruce(drvier2, start, end)
finished_list = []
CollectHandler.visit(Pattern_2k_by_algo1_handler(),bar_source,finished_list=finished_list)
print(f"finished size :{len(finished_list)}")
value_list_1_map = defaultdict(list)
value_list_3_map = defaultdict(list)
value_list_7_map = defaultdict(list)
value_list_14_map = defaultdict(list)
def cal_pct(close_price_list:[], pre_close_price)->float:
    close_price_list = numpy.array(close_price_list)
    close_price = close_price_list.mean()
    return 100 * (close_price - pre_close_price) / pre_close_price
### 收集对应的涨幅列表
for cData in finished_list:
    assert len(cData.unkown_bars) >= 14
    pattern_vaule = cData.dimen_value
    pre_close_price = cData.occur_bars[-1].close_price
    pct_1 = cal_pct([cData.unkown_bars[0].close_price],pre_close_price)
    pct_3 = cal_pct([cData.unkown_bars[i].close_price for i in range(1,3)],pre_close_price)
    pct_7 = cal_pct([cData.unkown_bars[i].close_price for i in range(4,7)],pre_close_price)
    pct_14 = cal_pct([cData.unkown_bars[i].close_price for i in range(11,14)],pre_close_price)
    value_list_1_map[pattern_vaule].append(pct_1)  #收集1日K线的涨幅情况
    value_list_3_map[pattern_vaule].append(pct_3)  #收集3日K线的涨幅情况
    value_list_7_map[pattern_vaule].append(pct_7)   #收集7日K线的涨幅情况
    value_list_14_map[pattern_vaule].append(pct_14)   #收集14日K线的涨幅情况
dataSet  = {}
fParser = FloatParser()
pattern_value_list = list(value_list_1_map.keys())
##计算分叉线值
dataSet['pattern_value'] = pattern_value_list
dataSet['1日分叉线'] = [ fParser.calc_avg_line(value_list_1_map[pattern_value])  for pattern_value in pattern_value_list]
dataSet['3日分叉线'] = [ fParser.calc_avg_line(value_list_3_map[pattern_value])  for pattern_value in pattern_value_list]
dataSet['7日分叉线'] = [ fParser.calc_avg_line(value_list_7_map[pattern_value])  for pattern_value in pattern_value_list]
dataSet['14日分叉线'] = [ fParser.calc_avg_line(value_list_14_map[pattern_value])  for pattern_value in pattern_value_list]
pData = pandas.DataFrame(dataSet).sort_values(by='14日分叉线')
print(f"{pData}")
```

###3 最终结果计算结果:
   72中2日k线形态得1，3，7，14日分叉线基本在涨幅0%左右，最看多得k线形体为258420，分叉为0.7，最看空的k线形态为199300，分叉值为-1.2，形态没有明显的看空或者看多特性。
```log
    pattern_value     1日分叉线         3日分叉线         7日分叉线        14日分叉线
5          206580  0.000000 -3.947368e-01 -5.440158e-01 -1.220657e+00
40         199300 -0.231660 -4.163197e-01 -5.632869e-01 -1.204819e+00
59         192091 -0.315457 -4.932735e-01 -1.030928e+00 -1.139287e+00
16         265376  0.260688  5.302227e-02 -1.239157e-01 -1.107754e+00
28          21991 -0.136612 -2.475248e-01 -4.347826e-01 -1.072125e+00
51         266449 -0.284091 -3.401361e-01 -2.372479e-01 -1.068640e+00
73         272919  0.000000 -4.295943e-01 -5.050505e-01 -1.039636e+00
11         206337  0.000000 -1.010101e-01 -7.054674e-01 -1.037037e+00
32          88492 -0.150602 -3.168568e-01 -5.937235e-01 -9.107468e-01
55         272281  0.000000 -1.141553e-01 -1.978239e-01 -8.727074e-01
36         265711 -0.070472 -3.365744e-01 -7.589025e-01 -8.476689e-01
68         251869 -0.348432 -5.280528e-01 -3.225806e-01 -8.294453e-01
10         206590  0.000000 -2.463054e-01 -6.029285e-01 -8.244994e-01
52         205942  0.000000 -1.121076e-01 -1.277139e-01 -8.097166e-01
64         103153  0.000000 -3.012048e-02 -2.652520e-01 -7.235142e-01
14         259159 -0.207900 -3.896104e-01 -4.140787e-01 -6.928406e-01
1          265649 -0.220022 -2.358491e-01 -5.031447e-01 -6.726457e-01
3          265639 -0.136986 -2.650177e-01 -4.997501e-01 -6.725515e-01
37         265487 -0.171233 -2.794857e-01 -5.847953e-01 -6.582885e-01
38          88482  0.000000  1.552759e-14 -1.759015e-01 -6.521739e-01
60         265457  0.298063  2.181025e-01  2.974148e-01 -6.393960e-01
6          324769 -0.060606 -1.118568e-01 -3.246753e-01 -6.315789e-01
0          206671 -0.129199 -2.500000e-01 -4.494382e-01 -6.276151e-01
42          88320  0.288184  2.505369e-01  5.772006e-01 -6.150062e-01
12         199381 -0.102145 -3.348214e-01 -5.312085e-01 -6.116208e-01
26          81040 -0.081169 -2.190581e-01 -1.403125e-14 -5.720229e-01
53         265386  0.134590 -1.765762e-14 -2.148805e-01 -5.633803e-01
18          14944 -0.094518 -2.599653e-01 -1.945525e-01 -5.494505e-01
67          73993  0.000000  0.000000e+00  2.901705e-01 -5.383580e-01
70         258349 -0.113507 -1.736111e-01 -1.648125e-01 -4.837929e-01
..            ...       ...           ...           ...           ...
7           81283  0.000000  0.000000e+00  6.626905e-02 -2.618780e-01
41         265638  0.000000 -1.968504e-01  0.000000e+00 -2.469136e-01
49         265730 -0.171233 -3.003003e-01 -5.067568e-01 -2.422774e-01
35         265740 -0.328407 -1.436094e-01 -2.253775e-01 -2.406739e-01
15         265963 -0.181865 -3.286879e-01 -8.818342e-02 -2.380952e-01
34         265497 -0.121655  0.000000e+00  1.273885e-01 -2.361673e-01
31          88330  0.000000  0.000000e+00  7.293946e-02 -2.218525e-01
71         265700  0.156201 -1.734505e-02  3.590406e-01 -2.029427e-01
17         442867  0.000000 -2.673797e-01 -2.244669e-01 -1.994515e-01
45          22234 -0.133333 -2.252252e-01 -5.615724e-01 -1.877934e-01
2          213961 -0.071480 -1.249196e-14 -2.936858e-01 -1.782531e-01
54         265721  0.000000 -4.793864e-02  7.457122e-02 -1.690821e-01
23         206428  0.000000 -1.201923e-01 -2.613776e-01 -1.349528e-01
69         264991 -0.129199  1.152074e-01  3.346720e-01 -1.022495e-01
20         258430 -0.150150 -1.657049e-14 -2.079597e-01 -6.190034e-02
48         279571  0.000000 -1.223491e-01  4.623209e-02 -5.837712e-02
74         272929  0.000000 -7.122507e-02 -1.383126e-01 -5.767013e-02
50         273010 -0.108578 -8.673027e-02 -2.024291e-01 -4.301075e-02
24         265801  0.130548  0.000000e+00  1.680672e-01 -3.911215e-02
39         199138  0.000000 -2.566735e-01 -5.439005e-01 -1.939254e-14
25         265467  0.280112  3.898236e-01  2.347418e-01  0.000000e+00
65         221251  0.000000 -2.004008e-01 -3.875969e-01  4.435573e-02
27          36814  0.000000 -1.414297e-14 -4.105090e-01  6.510417e-02
22         280300  0.000000  0.000000e+00  1.586033e-14  9.910803e-02
72         265659 -0.222074 -9.615385e-02 -4.616132e-01  1.023541e-01
19         265710  0.115340  1.612903e-01  1.158749e-01  1.242236e-01
9           29443  0.000000 -1.123596e-01 -1.261034e-01  1.498127e-01
63         258187  0.000000 -3.450656e-02 -1.745201e-01  4.846282e-01
21         265719  0.000000 -1.607717e-01  5.667182e-01  5.625879e-01
47         258420  0.162866  1.117318e-01  5.482456e-01  7.042254e-01
```


###最终结论
 纯粹依靠识别75日形态值去预测未来1，3，7，14日的涨幅情况是不靠谱的。

