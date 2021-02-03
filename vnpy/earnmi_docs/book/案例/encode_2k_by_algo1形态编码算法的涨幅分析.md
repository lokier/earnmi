#encode_2k_by_algo1形态编码算法的涨幅分析

在使用Pattern.encode_2k_by_algo1()识别出来的2日k线形态中，可以用anaylsisPatternCoverity函数得出75个有意义的k线形态值，它们是：

    [206671, 265649, 213961, 265639, 265720, 206580, 324769, 81283, 265629, 29443, 206590, 206337, 199381, 265619, 259159, 265963, 265376, 
    442867, 14944, 265710, 258430, 265719, 280300, 206428, 265801, 265467, 81040, 36814, 21991, 251140, 265477, 88330, 88492, 95863, 265497, 265740, 265711, 
    265487, 88482, 199138, 199300, 265638, 88320, 206347, 88573, 22234, 206681, 258420, 279571, 265730, 273010, 266449, 205942, 265386, 265721, 272281, 265729, 265406,
    273020, 192091, 265457, 273000, 251869, 88563, 258187, 103153, 221251, 258440, 73993, 264991, 258349, 265700, 265659, 272919, 272929]

以下就对这75个形态值做涨幅分析。


统计k线形态之后第k日的涨幅情况，找出50%分叉线

1日涨幅，涨幅情况以收盘价为准
3日涨幅, 涨幅情况以最后两日收盘价均价为准
7日涨幅，涨幅情况以最后3天收盘均价为准
14日涨幅，涨幅情况以最后5天收盘均价为准

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

###2 计算各k日形态对应得分叉值

```python
app = App()
start = datetime(year=2018,month=1,day=6)
end = datetime(year=2021,month=1,day=6)
drvier2 = ZZ500StockDriver()
bar_source = app.getBarManager().createBarSoruce([drvier2], Interval.DAILY, start, end)
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
fParser = FloatParser(-10,10)
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
   72中2日k线形态得1，3，7，14日分叉线基本在涨幅0%左右，最看多得k线形体为258420，分叉为0.9，最看空的k线形态为199300，分叉值为-1.1
```log
    pattern_value  1日分叉线  3日分叉线  7日分叉线  14日分叉线
40         199300    0.1   -0.5   -0.5    -1.1
16         265376    0.3    0.1    0.1    -1.1
5          206580   -0.1   -0.3   -0.5    -1.1
51         266449   -0.1   -0.1   -0.1    -0.9
11         206337   -0.1   -0.1   -0.7    -0.9
73         272919    0.1   -0.1   -0.5    -0.9
59         192091   -0.3   -0.5   -0.7    -0.9
28          21991   -0.1   -0.1   -0.5    -0.9
32          88492   -0.1   -0.3   -0.5    -0.9
6          324769   -0.1   -0.1   -0.3    -0.7
64         103153    0.1   -0.1   -0.1    -0.7
10         206590   -0.1   -0.3   -0.5    -0.7
68         251869   -0.1   -0.3   -0.3    -0.7
36         265711   -0.1   -0.3   -0.7    -0.7
52         205942   -0.1    0.1    0.1    -0.7
14         259159   -0.1   -0.3   -0.3    -0.7
1          265649    0.1   -0.3   -0.5    -0.7
60         265457    0.3    0.3    0.5    -0.7
55         272281    0.3   -0.1    0.1    -0.7
0          206671   -0.1   -0.3   -0.5    -0.5
42          88320    0.3    0.3    0.7    -0.5
30         265477    0.1    0.1   -0.1    -0.5
70         258349    0.1   -0.1   -0.1    -0.5
38          88482    0.1    0.3   -0.1    -0.5
53         265386    0.1    0.1   -0.1    -0.5
37         265487   -0.1   -0.1   -0.5    -0.5
8          265629    0.1   -0.1   -0.1    -0.5
12         199381   -0.1   -0.3   -0.5    -0.5
4          265720    0.1   -0.1   -0.1    -0.5
3          265639    0.1   -0.1   -0.5    -0.5
..            ...    ...    ...    ...     ...
61         273000    0.1   -0.3   -0.3    -0.1
49         265730    0.1   -0.3   -0.5    -0.1
29         251140    0.1    0.1    0.5    -0.1
69         264991   -0.1    0.1    0.3    -0.1
45          22234    0.1   -0.1   -0.5    -0.1
44          88573    0.1    0.1   -0.1    -0.1
31          88330    0.1   -0.1    0.1    -0.1
33          95863    0.1    0.1   -0.1    -0.1
41         265638   -0.1   -0.3    0.3    -0.1
34         265497    0.1   -0.1    0.1    -0.1
39         199138   -0.1   -0.3   -0.3    -0.1
46         206681    0.1   -0.5   -0.7    -0.1
17         442867    0.1   -0.3   -0.1    -0.1
65         221251    0.1   -0.3   -0.3     0.1
50         273010   -0.1   -0.1   -0.1     0.1
54         265721    0.1    0.1    0.1     0.1
25         265467    0.3    0.5    0.5     0.1
19         265710    0.3    0.3    0.1     0.1
20         258430   -0.1    0.1   -0.1     0.1
23         206428    0.1   -0.1   -0.1     0.1
24         265801    0.3    0.1    0.3     0.1
27          36814    0.1   -0.1   -0.1     0.1
9           29443    0.3    0.1   -0.1     0.1
74         272929   -0.1    0.1   -0.1     0.1
48         279571    0.1    0.1    0.3     0.3
22         280300   -0.1    0.3    0.1     0.3
72         265659   -0.3   -0.1   -0.5     0.3
63         258187    0.3    0.1   -0.1     0.5
21         265719    0.3   -0.1    0.7     0.7
47         258420    0.3    0.3    0.7     0.9
```


###最终结论
 纯粹依靠识别75日形态值去预测未来1，3，7，14日的涨幅情况是不靠谱的。

